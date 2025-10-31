"""Application submission and status API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Optional, List
from datetime import datetime
import uuid
import asyncio
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.application import (
    ApplicationCreate,
    ApplicationStatusResponse,
    Application,
    ApplicationStatus,
    PhotographMetadata,
    ProcessingMetadata,
)
from app.models.audit import AuditLog, EventType, ActorType, ResourceType
from app.database.mongodb import get_database
from app.database.repositories import ApplicationRepository, AuditLogRepository
from app.core.logging import logger
from app.services.queue_service import queue_service
from app.services.audit_service import audit_service
from app.services.metrics_service import metrics_service, MetricType
from app.utils.error_responses import ErrorCode, create_error_response, handle_exception

router = APIRouter(prefix="/applications", tags=["applications"])
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=ApplicationStatusResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def submit_application(
    request: Request,
    application_data: ApplicationCreate,
    db=Depends(get_database)
) -> ApplicationStatusResponse:
    """
    Submit a new application for processing
    
    - **applicant_data**: Applicant demographic information
    - **photograph_base64**: Base64 encoded photograph (JPEG/PNG)
    - **photograph_format**: Image format (jpg, jpeg, png)
    
    Returns application ID and initial status
    """
    try:
        # Generate unique application ID
        application_id = str(uuid.uuid4())
        
        logger.info(f"Received application submission: {application_id}")
        
        # Create photograph metadata (actual storage will be handled by photograph service)
        photograph_metadata = PhotographMetadata(
            path=f"./storage/photographs/{application_id}.{application_data.photograph_format}",
            format=application_data.photograph_format,
            width=0,  # Will be updated after validation
            height=0,  # Will be updated after validation
            file_size=len(application_data.photograph_base64),
            uploaded_at=datetime.utcnow()
        )
        
        # Create application document
        application = Application(
            application_id=application_id,
            applicant_data=application_data.applicant_data,
            photograph=photograph_metadata,
            processing=ProcessingMetadata(
                status=ApplicationStatus.PENDING
            ),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        app_repo = ApplicationRepository(db)
        await app_repo.create(application)
        
        logger.info(f"Application created in database: {application_id}")
        
        # Create audit log for application submission
        await audit_service.log_application_submission(
            db=db,
            application_id=application_id,
            applicant_email=application_data.applicant_data.email,
            applicant_name=application_data.applicant_data.name,
            ip_address=request.client.host if request.client else None
        )
        
        # Add to processing queue
        await queue_service.enqueue_application({
            "application_id": application_id,
            "photograph_base64": application_data.photograph_base64,
            "photograph_format": application_data.photograph_format,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Application queued for processing: {application_id}")
        
        # Record metrics
        metrics_service.record_count(MetricType.APPLICATION_SUBMISSION)
        
        # Return response
        return ApplicationStatusResponse(
            application_id=application_id,
            status=ApplicationStatus.PENDING,
            is_duplicate=False,
            identity_id=None,
            error_message=None,
            created_at=application.created_at,
            updated_at=application.updated_at
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        error_response = create_error_response(
            ErrorCode.E400,
            details={"validation_error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response.dict()
        )
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}")
        error_response = handle_exception(e, context="application_submission")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.get("/{application_id}/status", response_model=ApplicationStatusResponse)
async def get_application_status(
    application_id: str,
    db=Depends(get_database)
) -> ApplicationStatusResponse:
    """
    Get the processing status of an application
    
    - **application_id**: Unique application identifier
    
    Returns current processing status and results
    """
    try:
        app_repo = ApplicationRepository(db)
        application = await app_repo.get_by_id(application_id)
        
        if not application:
            error_response = create_error_response(
                ErrorCode.E202,
                details={"application_id": application_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response.dict()
            )
        
        return ApplicationStatusResponse(
            application_id=application.application_id,
            status=application.processing.status,
            is_duplicate=application.result.is_duplicate,
            identity_id=application.result.identity_id,
            error_message=application.processing.error_message,
            created_at=application.created_at,
            updated_at=application.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving application status: {str(e)}")
        error_response = handle_exception(e, context="get_application_status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.post("/batch", response_model=List[ApplicationStatusResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def submit_applications_batch(
    request: Request,
    applications_data: List[ApplicationCreate],
    db=Depends(get_database)
) -> List[ApplicationStatusResponse]:
    """
    Submit multiple applications for processing in batch (optimized for performance)
    
    - **applications_data**: List of application submissions
    
    Returns list of application IDs and initial statuses
    
    Note: Batch size is limited to 100 applications per request
    """
    try:
        # Validate batch size
        if len(applications_data) > 100:
            error_response = create_error_response(
                ErrorCode.E400,
                details={"error": "Batch size exceeds maximum of 100 applications"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        if not applications_data:
            error_response = create_error_response(
                ErrorCode.E400,
                details={"error": "Empty batch submission"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        logger.info(f"Received batch application submission: {len(applications_data)} applications")
        
        # Prepare applications for batch insert
        applications = []
        queue_items = []
        responses = []
        
        for app_data in applications_data:
            # Generate unique application ID
            application_id = str(uuid.uuid4())
            
            # Create photograph metadata
            photograph_metadata = PhotographMetadata(
                path=f"./storage/photographs/{application_id}.{app_data.photograph_format}",
                format=app_data.photograph_format,
                width=0,
                height=0,
                file_size=len(app_data.photograph_base64),
                uploaded_at=datetime.utcnow()
            )
            
            # Create application document
            application = Application(
                application_id=application_id,
                applicant_data=app_data.applicant_data,
                photograph=photograph_metadata,
                processing=ProcessingMetadata(
                    status=ApplicationStatus.PENDING
                ),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            applications.append(application.model_dump())
            
            # Prepare queue item
            queue_items.append({
                "application_id": application_id,
                "photograph_base64": app_data.photograph_base64,
                "photograph_format": app_data.photograph_format,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Prepare response
            responses.append(ApplicationStatusResponse(
                application_id=application_id,
                status=ApplicationStatus.PENDING,
                is_duplicate=False,
                identity_id=None,
                error_message=None,
                created_at=application.created_at,
                updated_at=application.updated_at
            ))
        
        # Batch insert into MongoDB (optimized)
        app_repo = ApplicationRepository(db)
        await app_repo.create_batch(applications)
        
        logger.info(f"Batch created {len(applications)} applications in database")
        
        # Create audit logs in parallel
        audit_tasks = [
            audit_service.log_application_submission(
                db=db,
                application_id=app["application_id"],
                applicant_email=app["applicant_data"]["email"],
                applicant_name=app["applicant_data"]["name"],
                ip_address=request.client.host if request.client else None
            )
            for app in applications
        ]
        await asyncio.gather(*audit_tasks, return_exceptions=True)
        
        # Add to processing queue in batch
        for queue_item in queue_items:
            await queue_service.enqueue_application(queue_item)
        
        logger.info(f"Batch queued {len(queue_items)} applications for processing")
        
        # Record metrics
        metrics_service.record_count(MetricType.APPLICATION_SUBMISSION, count=len(applications))
        
        return responses
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Batch validation error: {str(e)}")
        error_response = create_error_response(
            ErrorCode.E400,
            details={"validation_error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response.dict()
        )
    except Exception as e:
        logger.error(f"Error submitting batch applications: {str(e)}")
        error_response = handle_exception(e, context="batch_application_submission")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.post("/status/batch", response_model=List[ApplicationStatusResponse])
async def get_batch_application_status(
    application_ids: List[str],
    db=Depends(get_database)
) -> List[ApplicationStatusResponse]:
    """
    Get status for multiple applications in batch
    
    - **application_ids**: List of application IDs to query (max 100)
    
    Returns list of application statuses
    """
    try:
        # Validate batch size
        if len(application_ids) > 100:
            error_response = create_error_response(
                ErrorCode.E400,
                details={"error": "Batch size exceeds maximum of 100 applications"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        if not application_ids:
            error_response = create_error_response(
                ErrorCode.E400,
                details={"error": "Empty application ID list"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        logger.info(f"Batch status query for {len(application_ids)} applications")
        
        app_repo = ApplicationRepository(db)
        responses = []
        
        # Query all applications
        for app_id in application_ids:
            application = await app_repo.get_by_id(app_id)
            
            if application:
                responses.append(ApplicationStatusResponse(
                    application_id=application.application_id,
                    status=application.processing.status,
                    is_duplicate=application.result.is_duplicate,
                    identity_id=application.result.identity_id,
                    error_message=application.processing.error_message,
                    created_at=application.created_at,
                    updated_at=application.updated_at
                ))
            else:
                # Application not found - return not found status
                responses.append(ApplicationStatusResponse(
                    application_id=app_id,
                    status=ApplicationStatus.FAILED,
                    is_duplicate=False,
                    identity_id=None,
                    error_message="Application not found",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
        
        logger.info(f"Batch status query completed: {len(responses)} results")
        
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch status query: {str(e)}")
        error_response = handle_exception(e, context="batch_status_query")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

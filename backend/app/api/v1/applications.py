"""Application submission and status API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Query, File, UploadFile, Form
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import asyncio
import base64
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


@router.get("", response_model=Dict[str, Any])
async def list_applications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: str = Query(None, description="Filter by status"),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    List all applications with pagination
    
    Returns paginated list of applications
    """
    try:
        skip = (page - 1) * page_size
        
        # Build query
        query = {}
        if status_filter:
            query["processing.status"] = status_filter
        
        # Get total count
        total = await db.applications.count_documents(query)
        
        # Get applications
        cursor = db.applications.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        
        applications = []
        async for doc in cursor:
            applications.append({
                "application_id": doc.get("application_id"),
                "status": doc.get("processing", {}).get("status"),
                "is_duplicate": doc.get("result", {}).get("is_duplicate", False),
                "identity_id": doc.get("result", {}).get("identity_id"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "updated_at": doc.get("updated_at").isoformat() if doc.get("updated_at") else None,
                "applicant_name": doc.get("applicant_data", {}).get("name"),
                "applicant_email": doc.get("applicant_data", {}).get("email")
            })
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": applications,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error listing applications: {str(e)}")
        error_response = handle_exception(e, context="list_applications")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.post("/upload", response_model=ApplicationStatusResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_application(
    request: Request,
    photograph: UploadFile = File(...),
    name: str = Form(...),
    date_of_birth: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: Optional[str] = Form(None),
    db=Depends(get_database)
) -> ApplicationStatusResponse:
    """
    Upload a new application with multipart form data
    
    - **photograph**: Image file (JPEG/PNG)
    - **name**: Applicant name
    - **date_of_birth**: Date of birth (YYYY-MM-DD)
    - **email**: Email address
    - **phone**: Phone number
    - **address**: Optional address
    
    Returns application ID and initial status
    """
    try:
        # Read file content
        file_content = await photograph.read()
        
        # Convert to base64
        photograph_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Determine format from filename
        filename = photograph.filename or ""
        if filename.lower().endswith('.png'):
            photograph_format = 'png'
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            photograph_format = 'jpg'
        else:
            raise ValueError("Unsupported image format. Please upload JPEG or PNG.")
        
        # Generate unique application ID
        application_id = str(uuid.uuid4())
        
        logger.info(f"Received application upload: {application_id}")
        
        # Create applicant data
        from app.models.application import ApplicantData
        applicant_data = ApplicantData(
            name=name,
            date_of_birth=date_of_birth,
            email=email,
            phone=phone,
            address=address
        )
        
        # Get image dimensions using PIL
        from PIL import Image
        import io
        
        try:
            image = Image.open(io.BytesIO(file_content))
            width, height = image.size
        except Exception as img_error:
            logger.warning(f"Could not read image dimensions: {str(img_error)}")
            width, height = 640, 480  # Default dimensions if can't read
        
        # Create photograph metadata
        photograph_metadata = PhotographMetadata(
            path=f"./storage/photographs/{application_id}.{photograph_format}",
            format=photograph_format,
            width=width,
            height=height,
            file_size=len(file_content),
            uploaded_at=datetime.utcnow()
        )
        
        # Create application document
        application = Application(
            application_id=application_id,
            applicant_data=applicant_data,
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
        
        # Create audit log
        await audit_service.log_application_submission(
            db=db,
            application_id=application_id,
            applicant_email=email,
            applicant_name=name,
            ip_address=request.client.host if request.client else None
        )
        
        # Add to processing queue
        await queue_service.enqueue_application({
            "application_id": application_id,
            "photograph_base64": photograph_base64,
            "photograph_format": photograph_format,
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
            detail=error_response.to_dict()
        )
    except Exception as e:
        logger.error(f"Error uploading application: {str(e)}")
        error_response = handle_exception(e, context="upload_application")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.to_dict()
        )


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


@router.get("/{application_id}", response_model=Dict[str, Any])
async def get_application(
    application_id: str,
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Get full application details by ID
    
    Returns complete application information
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
        
        # Convert to dict and format dates
        app_dict = application.model_dump()
        app_dict["created_at"] = application.created_at.isoformat() if application.created_at else None
        app_dict["updated_at"] = application.updated_at.isoformat() if application.updated_at else None
        
        return app_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving application: {str(e)}")
        error_response = handle_exception(e, context="get_application")
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


@router.post("/{application_id}/confirm-match", response_model=Dict[str, Any])
async def confirm_match(
    application_id: str,
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Confirm a duplicate match for an application
    
    Updates the application status to confirmed duplicate
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
        
        # Update status to confirmed duplicate
        await app_repo.update_status(application_id, ApplicationStatus.DUPLICATE)
        
        logger.info(f"Match confirmed for application: {application_id}")
        
        return {
            "message": "Match confirmed successfully",
            "application_id": application_id,
            "status": ApplicationStatus.DUPLICATE
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming match: {str(e)}")
        error_response = handle_exception(e, context="confirm_match")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.post("/{application_id}/reject-match", response_model=Dict[str, Any])
async def reject_match(
    application_id: str,
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Reject a duplicate match for an application
    
    Updates the application status to verified (unique)
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
        
        # Update status to verified (not a duplicate)
        await app_repo.update_status(application_id, ApplicationStatus.VERIFIED)
        await app_repo.update_result(application_id, {"is_duplicate": False})
        
        logger.info(f"Match rejected for application: {application_id}")
        
        return {
            "message": "Match rejected successfully",
            "application_id": application_id,
            "status": ApplicationStatus.VERIFIED
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting match: {str(e)}")
        error_response = handle_exception(e, context="reject_match")
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

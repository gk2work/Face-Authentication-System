"""Application submission and status API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Optional
from datetime import datetime
import uuid
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
        
        # Create audit log
        audit_repo = AuditLogRepository(db)
        audit_log = AuditLog(
            event_type=EventType.APPLICATION_SUBMITTED,
            actor_id="system",
            actor_type=ActorType.API,
            resource_id=application_id,
            resource_type=ResourceType.APPLICATION,
            action="Application submitted for processing",
            details={
                "applicant_email": application_data.applicant_data.email,
                "applicant_name": application_data.applicant_data.name,
                "photograph_format": application_data.photograph_format
            },
            success=True
        )
        await audit_repo.create(audit_log)
        
        # Add to processing queue
        await queue_service.enqueue_application({
            "application_id": application_id,
            "photograph_base64": application_data.photograph_base64,
            "photograph_format": application_data.photograph_format,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Application queued for processing: {application_id}")
        
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit application"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application status"
        )

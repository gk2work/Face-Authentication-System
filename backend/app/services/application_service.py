"""Application persistence and management service"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.models.application import (
    Application,
    ApplicationCreate,
    ApplicationStatus,
    PhotographMetadata,
    ProcessingMetadata,
    ApplicationResult
)
from app.database.repositories import ApplicationRepository
from app.core.logging import logger


class ApplicationService:
    """Service for application record persistence and management"""
    
    async def create_application(
        self,
        app_repo: ApplicationRepository,
        application_data: ApplicationCreate,
        photograph_path: str,
        width: int,
        height: int,
        file_size: int
    ) -> Application:
        """
        Create and persist a new application record
        
        Args:
            app_repo: Application repository instance
            application_data: Application creation data
            photograph_path: Path where photograph is stored
            width: Photograph width in pixels
            height: Photograph height in pixels
            file_size: Photograph file size in bytes
            
        Returns:
            Created Application object
        """
        # Generate unique application ID using uuid4
        application_id = str(uuid.uuid4())
        
        logger.info(f"Creating application record: {application_id}")
        
        # Create photograph metadata
        photograph_metadata = PhotographMetadata(
            path=photograph_path,
            format=application_data.photograph_format,
            width=width,
            height=height,
            file_size=file_size,
            uploaded_at=datetime.utcnow()
        )
        
        # Create processing metadata with initial status as "pending"
        processing_metadata = ProcessingMetadata(
            status=ApplicationStatus.PENDING,
            face_detected=False,
            quality_score=None,
            embedding_generated=False,
            duplicate_check_completed=False,
            error_code=None,
            error_message=None,
            processing_started_at=None,
            processing_completed_at=None
        )
        
        # Create application result
        application_result = ApplicationResult(
            identity_id=None,
            is_duplicate=False,
            matched_applications=[],
            final_status=ApplicationStatus.PENDING,
            reviewed_by=None,
            review_notes=None,
            reviewed_at=None
        )
        
        # Create application document
        application = Application(
            application_id=application_id,
            applicant_data=application_data.applicant_data,
            photograph=photograph_metadata,
            processing=processing_metadata,
            result=application_result,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Persist to MongoDB with error handling
        try:
            await app_repo.create(application)
            logger.info(f"Application record created successfully: {application_id}")
            return application
            
        except ValueError as e:
            logger.error(f"Failed to create application (duplicate ID): {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to create application: {str(e)}")
            raise
    
    async def update_application_status(
        self,
        app_repo: ApplicationRepository,
        application_id: str,
        status: ApplicationStatus,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update application processing status
        
        Args:
            app_repo: Application repository instance
            application_id: Application identifier
            status: New status
            error_code: Optional error code
            error_message: Optional error message
            
        Returns:
            True if updated successfully
        """
        logger.info(f"Updating application status: {application_id} -> {status}")
        
        try:
            updated = await app_repo.update_status(
                application_id=application_id,
                status=status,
                error_code=error_code,
                error_message=error_message
            )
            
            if updated:
                logger.info(f"Application status updated: {application_id}")
            else:
                logger.warning(f"Application not found or not updated: {application_id}")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to update application status: {str(e)}")
            raise
    
    async def update_processing_metadata(
        self,
        app_repo: ApplicationRepository,
        application_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update application processing metadata
        
        Args:
            app_repo: Application repository instance
            application_id: Application identifier
            metadata: Metadata fields to update
            
        Returns:
            True if updated successfully
        """
        logger.info(f"Updating processing metadata: {application_id}")
        
        try:
            updated = await app_repo.update_processing_metadata(
                application_id=application_id,
                metadata=metadata
            )
            
            if updated:
                logger.info(f"Processing metadata updated: {application_id}")
            else:
                logger.warning(f"Application not found or not updated: {application_id}")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to update processing metadata: {str(e)}")
            raise
    
    async def update_application_result(
        self,
        app_repo: ApplicationRepository,
        application_id: str,
        result_data: Dict[str, Any]
    ) -> bool:
        """
        Update application result
        
        Args:
            app_repo: Application repository instance
            application_id: Application identifier
            result_data: Result fields to update
            
        Returns:
            True if updated successfully
        """
        logger.info(f"Updating application result: {application_id}")
        
        try:
            updated = await app_repo.update_result(
                application_id=application_id,
                result_data=result_data
            )
            
            if updated:
                logger.info(f"Application result updated: {application_id}")
            else:
                logger.warning(f"Application not found or not updated: {application_id}")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to update application result: {str(e)}")
            raise
    
    async def get_application(
        self,
        app_repo: ApplicationRepository,
        application_id: str
    ) -> Optional[Application]:
        """
        Retrieve application by ID
        
        Args:
            app_repo: Application repository instance
            application_id: Application identifier
            
        Returns:
            Application object or None if not found
        """
        try:
            application = await app_repo.get_by_id(application_id)
            
            if application:
                logger.info(f"Application retrieved: {application_id}")
            else:
                logger.warning(f"Application not found: {application_id}")
            
            return application
            
        except Exception as e:
            logger.error(f"Failed to retrieve application: {str(e)}")
            raise
    
    async def get_applications_by_status(
        self,
        app_repo: ApplicationRepository,
        status: ApplicationStatus,
        limit: int = 100,
        skip: int = 0
    ) -> List[Application]:
        """
        Retrieve applications by status
        
        Args:
            app_repo: Application repository instance
            status: Application status to filter by
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of Application objects
        """
        try:
            applications = await app_repo.get_by_status(
                status=status,
                limit=limit,
                skip=skip
            )
            
            logger.info(f"Retrieved {len(applications)} applications with status: {status}")
            
            return applications
            
        except Exception as e:
            logger.error(f"Failed to retrieve applications by status: {str(e)}")
            raise


# Global application service instance
application_service = ApplicationService()

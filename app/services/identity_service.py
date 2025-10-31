"""Identity management service for creating and managing unique applicant identities"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.logging import logger
from app.database.repositories import IdentityRepository, ApplicationRepository
from app.models.identity import Identity, IdentityStatus
from app.models.application import ApplicationStatus


class IdentityService:
    """Service for managing applicant identities"""
    
    def __init__(self):
        logger.info("Identity service initialized")
    
    def _get_identity_repo(self, db):
        """Get identity repository instance with database connection"""
        return IdentityRepository(db)
    
    def _get_application_repo(self, db):
        """Get application repository instance with database connection"""
        return ApplicationRepository(db)
    
    def generate_unique_id(self) -> str:
        """
        Generate a unique identifier using UUID v4
        
        Returns:
            UUID v4 string
        """
        unique_id = str(uuid.uuid4())
        logger.debug(f"Generated unique ID: {unique_id}")
        return unique_id
    
    async def create_identity(self, db, application_id: str, 
                             metadata: Optional[Dict[str, Any]] = None) -> Identity:
        """
        Create a new identity for a unique applicant
        
        Args:
            db: Database connection
            application_id: Application ID to associate with identity
            metadata: Optional metadata to store with identity
            
        Returns:
            Created Identity object
            
        Raises:
            ValueError: If identity creation fails
        """
        try:
            identity_repo = self._get_identity_repo(db)
            
            # Generate unique ID
            unique_id = self.generate_unique_id()
            
            # Validate uniqueness (check if ID already exists)
            existing_identity = await identity_repo.get_by_unique_id(unique_id)
            
            # In the extremely rare case of collision, regenerate
            while existing_identity is not None:
                logger.warning(f"UUID collision detected: {unique_id}. Regenerating...")
                unique_id = self.generate_unique_id()
                existing_identity = await identity_repo.get_by_unique_id(unique_id)
            
            # Create identity document
            identity = Identity(
                unique_id=unique_id,
                status=IdentityStatus.ACTIVE,
                metadata=metadata or {},
                application_ids=[application_id]
            )
            
            # Store in database
            await identity_repo.create(identity)
            
            logger.info(f"Created new identity: {unique_id} for application: {application_id}")
            
            return identity
            
        except Exception as e:
            logger.error(f"Failed to create identity: {str(e)}")
            raise ValueError(f"Identity creation failed: {str(e)}")
    
    async def get_identity(self, db, unique_id: str) -> Optional[Identity]:
        """
        Get identity by unique ID
        
        Args:
            unique_id: Identity unique identifier
            
        Returns:
            Identity object or None if not found
        """
        try:
            identity = await identity_repo.get_by_unique_id(unique_id)
            return identity
        except Exception as e:
            logger.error(f"Failed to get identity: {str(e)}")
            return None
    
    async def update_identity_status(self, db, unique_id: str, 
                                    status: IdentityStatus) -> bool:
        """
        Update identity status
        
        Args:
            unique_id: Identity unique identifier
            status: New status
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            success = await identity_repo.update_status(unique_id, status)
            
            if success:
                logger.info(f"Updated identity status: {unique_id} -> {status}")
            else:
                logger.warning(f"Failed to update identity status: {unique_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update identity status: {str(e)}")
            return False
    
    async def update_identity_metadata(self, db, unique_id: str, 
                                      metadata: Dict[str, Any]) -> bool:
        """
        Update identity metadata
        
        Args:
            unique_id: Identity unique identifier
            metadata: Metadata dictionary
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            success = await identity_repo.update_metadata(unique_id, metadata)
            
            if success:
                logger.info(f"Updated identity metadata: {unique_id}")
            else:
                logger.warning(f"Failed to update identity metadata: {unique_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update identity metadata: {str(e)}")
            return False
    
    async def add_application_to_identity(self, db, unique_id: str, 
                                         application_id: str) -> bool:
        """
        Add application ID to identity's application list
        
        Args:
            unique_id: Identity unique identifier
            application_id: Application ID to add
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            success = await identity_repo.add_application_id(unique_id, application_id)
            
            if success:
                logger.info(f"Added application {application_id} to identity {unique_id}")
            else:
                logger.warning(f"Failed to add application to identity: {unique_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add application to identity: {str(e)}")
            return False
    
    async def get_identity_applications(self, unique_id: str) -> List[str]:
        """
        Get all application IDs associated with an identity
        
        Args:
            unique_id: Identity unique identifier
            
        Returns:
            List of application IDs
        """
        try:
            identity = await identity_repo.get_by_unique_id(unique_id)
            
            if identity:
                return identity.application_ids
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get identity applications: {str(e)}")
            return []
    
    async def validate_unique_id(self, unique_id: str) -> bool:
        """
        Validate that a unique ID exists and is active
        
        Args:
            unique_id: Identity unique identifier
            
        Returns:
            True if valid and active, False otherwise
        """
        try:
            identity = await identity_repo.get_by_unique_id(unique_id)
            
            if identity and identity.status == IdentityStatus.ACTIVE:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to validate unique ID: {str(e)}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get identity service statistics
        
        Returns:
            Dictionary with statistics
        """
        # This would require additional repository methods to count identities
        # For now, return basic info
        return {
            "service": "identity_management",
            "status": "active"
        }


# Global identity service instance
identity_service = IdentityService()

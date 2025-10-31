"""Identity management service for creating and managing unique applicant identities"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.logging import logger
from app.database.repositories import identity_repository, application_repository
from app.models.identity import Identity, IdentityStatus
from app.models.application import ApplicationStatus


class IdentityService:
    """Service for managing applicant identities"""
    
    def __init__(self):
        logger.info("Identity service initialized")
    
    def generate_unique_id(self) -> str:
        """
        Generate a unique identifier using UUID v4
        
        Returns:
            UUID v4 string
        """
        unique_id = str(uuid.uuid4())
        logger.debug(f"Generated unique ID: {unique_id}")
        return unique_id
    
    async def create_identity(self, application_id: str, 
                             metadata: Optional[Dict[str, Any]] = None) -> Identity:
        """
        Create a new identity for a unique applicant
        
        Args:
            application_id: Application ID to associate with identity
            metadata: Optional metadata to store with identity
            
        Returns:
            Created Identity object
            
        Raises:
            ValueError: If identity creation fails
        """
        try:
            # Generate unique ID
            unique_id = self.generate_unique_id()
            
            # Validate uniqueness (check if ID already exists)
            existing_identity = await identity_repository.get_by_unique_id(unique_id)
            
            # In the extremely rare case of collision, regenerate
            while existing_identity is not None:
                logger.warning(f"UUID collision detected: {unique_id}. Regenerating...")
                unique_id = self.generate_unique_id()
                existing_identity = await identity_repository.get_by_unique_id(unique_id)
            
            # Create identity document
            identity = Identity(
                unique_id=unique_id,
                status=IdentityStatus.ACTIVE,
                metadata=metadata or {},
                application_ids=[application_id]
            )
            
            # Store in database
            await identity_repository.create(identity)
            
            logger.info(f"Created new identity: {unique_id} for application: {application_id}")
            
            return identity
            
        except Exception as e:
            logger.error(f"Failed to create identity: {str(e)}")
            raise ValueError(f"Identity creation failed: {str(e)}")
    
    async def get_identity(self, unique_id: str) -> Optional[Identity]:
        """
        Get identity by unique ID
        
        Args:
            unique_id: Identity unique identifier
            
        Returns:
            Identity object or None if not found
        """
        try:
            identity = await identity_repository.get_by_unique_id(unique_id)
            return identity
        except Exception as e:
            logger.error(f"Failed to get identity: {str(e)}")
            return None
    
    async def update_identity_status(self, unique_id: str, 
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
            success = await identity_repository.update_status(unique_id, status)
            
            if success:
                logger.info(f"Updated identity status: {unique_id} -> {status}")
            else:
                logger.warning(f"Failed to update identity status: {unique_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update identity status: {str(e)}")
            return False
    
    async def update_identity_metadata(self, unique_id: str, 
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
            success = await identity_repository.update_metadata(unique_id, metadata)
            
            if success:
                logger.info(f"Updated identity metadata: {unique_id}")
            else:
                logger.warning(f"Failed to update identity metadata: {unique_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update identity metadata: {str(e)}")
            return False
    
    async def add_application_to_identity(self, unique_id: str, 
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
            success = await identity_repository.add_application_id(unique_id, application_id)
            
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
            identity = await identity_repository.get_by_unique_id(unique_id)
            
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
            identity = await identity_repository.get_by_unique_id(unique_id)
            
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

    async def link_embedding_to_identity(self, identity_id: str, application_id: str,
                                        embedding: List[float], bounding_box: Dict[str, int],
                                        quality_score: float) -> bool:
        """
        Link facial embedding to identity
        
        Args:
            identity_id: Identity unique identifier
            application_id: Application identifier
            embedding: Facial embedding vector
            bounding_box: Face bounding box coordinates
            quality_score: Quality assessment score
            
        Returns:
            True if linked successfully, False otherwise
        """
        try:
            from app.services.embedding_storage_service import embedding_storage_service
            
            # Store embedding with identity association
            success = await embedding_storage_service.store_embedding(
                identity_id=identity_id,
                application_id=application_id,
                embedding=embedding,
                bounding_box=bounding_box,
                quality_score=quality_score
            )
            
            if success:
                logger.info(f"Linked embedding to identity: {identity_id} for application: {application_id}")
            else:
                logger.error(f"Failed to link embedding to identity: {identity_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to link embedding to identity: {str(e)}")
            return False
    
    async def get_identity_by_application(self, application_id: str) -> Optional[Identity]:
        """
        Get identity associated with an application
        
        Args:
            application_id: Application identifier
            
        Returns:
            Identity object or None if not found
        """
        try:
            from app.database.repositories import embedding_repository
            
            # Get embedding by application ID
            embedding = await embedding_repository.get_by_application_id(application_id)
            
            if not embedding:
                logger.warning(f"No embedding found for application: {application_id}")
                return None
            
            # Get identity by identity ID from embedding
            identity = await identity_repository.get_by_unique_id(embedding.identity_id)
            
            return identity
            
        except Exception as e:
            logger.error(f"Failed to get identity by application: {str(e)}")
            return None
    
    async def create_or_link_identity(self, application_id: str, embedding: List[float],
                                     bounding_box: Dict[str, int], quality_score: float,
                                     is_duplicate: bool, matched_application_id: Optional[str] = None,
                                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new identity for unique applicant or link to existing identity for duplicate
        
        Args:
            application_id: Application identifier
            embedding: Facial embedding vector
            bounding_box: Face bounding box coordinates
            quality_score: Quality assessment score
            is_duplicate: Whether application is a duplicate
            matched_application_id: Application ID of matched duplicate (if is_duplicate=True)
            metadata: Optional metadata for new identity
            
        Returns:
            Identity unique ID
            
        Raises:
            ValueError: If operation fails
        """
        try:
            if is_duplicate and matched_application_id:
                # Retrieve existing identity from matched application
                identity = await self.get_identity_by_application(matched_application_id)
                
                if not identity:
                    raise ValueError(f"No identity found for matched application: {matched_application_id}")
                
                # Add current application to identity
                await self.add_application_to_identity(identity.unique_id, application_id)
                
                # Link embedding to existing identity
                await self.link_embedding_to_identity(
                    identity_id=identity.unique_id,
                    application_id=application_id,
                    embedding=embedding,
                    bounding_box=bounding_box,
                    quality_score=quality_score
                )
                
                logger.info(f"Linked duplicate application {application_id} to existing identity {identity.unique_id}")
                
                return identity.unique_id
                
            else:
                # Create new identity for unique applicant
                identity = await self.create_identity(application_id, metadata)
                
                # Link embedding to new identity
                await self.link_embedding_to_identity(
                    identity_id=identity.unique_id,
                    application_id=application_id,
                    embedding=embedding,
                    bounding_box=bounding_box,
                    quality_score=quality_score
                )
                
                logger.info(f"Created new identity {identity.unique_id} for unique application {application_id}")
                
                return identity.unique_id
                
        except Exception as e:
            logger.error(f"Failed to create or link identity: {str(e)}")
            raise ValueError(f"Identity operation failed: {str(e)}")

    async def mark_application_as_duplicate(self, application_id: str, identity_id: str,
                                           matched_application_id: str, 
                                           confidence_score: float) -> bool:
        """
        Mark application as duplicate and link to identity
        
        Args:
            application_id: Application identifier to mark as duplicate
            identity_id: Identity unique identifier to link to
            matched_application_id: Application ID that was matched
            confidence_score: Match confidence score
            
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            # Update application status to duplicate
            await application_repository.update_status(
                application_id=application_id,
                status=ApplicationStatus.DUPLICATE
            )
            
            # Update application result with identity and match information
            result_data = {
                "identity_id": identity_id,
                "is_duplicate": True,
                "final_status": ApplicationStatus.DUPLICATE
            }
            
            await application_repository.update_result(
                application_id=application_id,
                result_data=result_data
            )
            
            # Update processing metadata with match confidence
            processing_metadata = {
                "duplicate_check_completed": True
            }
            
            await application_repository.update_processing_metadata(
                application_id=application_id,
                metadata=processing_metadata
            )
            
            logger.info(
                f"Marked application {application_id} as duplicate. "
                f"Identity: {identity_id}, Matched: {matched_application_id}, "
                f"Confidence: {confidence_score:.3f}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark application as duplicate: {str(e)}")
            return False
    
    async def mark_application_as_verified(self, application_id: str, 
                                          identity_id: str) -> bool:
        """
        Mark application as verified (unique, non-duplicate)
        
        Args:
            application_id: Application identifier
            identity_id: Identity unique identifier
            
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            # Update application status to verified
            await application_repository.update_status(
                application_id=application_id,
                status=ApplicationStatus.VERIFIED
            )
            
            # Update application result with identity
            result_data = {
                "identity_id": identity_id,
                "is_duplicate": False,
                "final_status": ApplicationStatus.VERIFIED
            }
            
            await application_repository.update_result(
                application_id=application_id,
                result_data=result_data
            )
            
            # Update processing metadata
            processing_metadata = {
                "duplicate_check_completed": True
            }
            
            await application_repository.update_processing_metadata(
                application_id=application_id,
                metadata=processing_metadata
            )
            
            logger.info(f"Marked application {application_id} as verified. Identity: {identity_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark application as verified: {str(e)}")
            return False
    
    async def process_application_result(self, application_id: str, embedding: List[float],
                                        bounding_box: Dict[str, int], quality_score: float,
                                        is_duplicate: bool, matched_application_id: Optional[str] = None,
                                        confidence_score: Optional[float] = None) -> str:
        """
        Process application result and create/link identity
        
        Args:
            application_id: Application identifier
            embedding: Facial embedding vector
            bounding_box: Face bounding box coordinates
            quality_score: Quality assessment score
            is_duplicate: Whether application is a duplicate
            matched_application_id: Matched application ID (if duplicate)
            confidence_score: Match confidence score (if duplicate)
            
        Returns:
            Identity unique ID
            
        Raises:
            ValueError: If processing fails
        """
        try:
            # Create or link identity
            identity_id = await self.create_or_link_identity(
                application_id=application_id,
                embedding=embedding,
                bounding_box=bounding_box,
                quality_score=quality_score,
                is_duplicate=is_duplicate,
                matched_application_id=matched_application_id
            )
            
            # Mark application status
            if is_duplicate and matched_application_id and confidence_score:
                await self.mark_application_as_duplicate(
                    application_id=application_id,
                    identity_id=identity_id,
                    matched_application_id=matched_application_id,
                    confidence_score=confidence_score
                )
            else:
                await self.mark_application_as_verified(
                    application_id=application_id,
                    identity_id=identity_id
                )
            
            logger.info(f"Processed application result: {application_id} -> Identity: {identity_id}")
            
            return identity_id
            
        except Exception as e:
            logger.error(f"Failed to process application result: {str(e)}")
            raise ValueError(f"Application processing failed: {str(e)}")

    async def suspend_identity(self, unique_id: str, reason: str) -> bool:
        """
        Suspend an identity
        
        Args:
            unique_id: Identity unique identifier
            reason: Reason for suspension
            
        Returns:
            True if suspended successfully, False otherwise
        """
        try:
            # Update status to suspended
            success = await self.update_identity_status(unique_id, IdentityStatus.SUSPENDED)
            
            if success:
                # Add suspension reason to metadata
                identity = await self.get_identity(unique_id)
                if identity:
                    metadata = identity.metadata.copy()
                    metadata["suspension_reason"] = reason
                    metadata["suspended_at"] = datetime.utcnow().isoformat()
                    
                    await self.update_identity_metadata(unique_id, metadata)
                
                logger.info(f"Suspended identity {unique_id}. Reason: {reason}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to suspend identity: {str(e)}")
            return False
    
    async def reactivate_identity(self, unique_id: str) -> bool:
        """
        Reactivate a suspended identity
        
        Args:
            unique_id: Identity unique identifier
            
        Returns:
            True if reactivated successfully, False otherwise
        """
        try:
            # Update status to active
            success = await self.update_identity_status(unique_id, IdentityStatus.ACTIVE)
            
            if success:
                # Update metadata
                identity = await self.get_identity(unique_id)
                if identity:
                    metadata = identity.metadata.copy()
                    metadata["reactivated_at"] = datetime.utcnow().isoformat()
                    # Remove suspension reason
                    metadata.pop("suspension_reason", None)
                    
                    await self.update_identity_metadata(unique_id, metadata)
                
                logger.info(f"Reactivated identity {unique_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reactivate identity: {str(e)}")
            return False
    
    async def merge_identities(self, source_id: str, target_id: str, 
                              reason: str) -> bool:
        """
        Merge two identities (mark source as merged into target)
        
        Args:
            source_id: Source identity to merge from
            target_id: Target identity to merge into
            reason: Reason for merge
            
        Returns:
            True if merged successfully, False otherwise
        """
        try:
            # Get both identities
            source_identity = await self.get_identity(source_id)
            target_identity = await self.get_identity(target_id)
            
            if not source_identity or not target_identity:
                logger.error(f"One or both identities not found: {source_id}, {target_id}")
                return False
            
            # Transfer all applications from source to target
            for app_id in source_identity.application_ids:
                await self.add_application_to_identity(target_id, app_id)
                
                # Update application to point to target identity
                await application_repository.update_result(
                    application_id=app_id,
                    result_data={"identity_id": target_id}
                )
            
            # Mark source identity as merged
            await self.update_identity_status(source_id, IdentityStatus.MERGED)
            
            # Update source metadata
            source_metadata = source_identity.metadata.copy()
            source_metadata["merged_into"] = target_id
            source_metadata["merge_reason"] = reason
            source_metadata["merged_at"] = datetime.utcnow().isoformat()
            await self.update_identity_metadata(source_id, source_metadata)
            
            # Update target metadata
            target_metadata = target_identity.metadata.copy()
            if "merged_from" not in target_metadata:
                target_metadata["merged_from"] = []
            target_metadata["merged_from"].append({
                "identity_id": source_id,
                "merged_at": datetime.utcnow().isoformat(),
                "reason": reason
            })
            await self.update_identity_metadata(target_id, target_metadata)
            
            logger.info(f"Merged identity {source_id} into {target_id}. Reason: {reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to merge identities: {str(e)}")
            return False
    
    async def query_identities(self, status: Optional[IdentityStatus] = None,
                              limit: int = 100, skip: int = 0) -> List[Identity]:
        """
        Query identities with filters
        
        Args:
            status: Optional status filter
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of Identity objects
        """
        try:
            # This would require additional repository methods
            # For now, return empty list as placeholder
            logger.info(f"Query identities: status={status}, limit={limit}, skip={skip}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to query identities: {str(e)}")
            return []
    
    async def get_identity_details(self, unique_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an identity
        
        Args:
            unique_id: Identity unique identifier
            
        Returns:
            Dictionary with identity details or None if not found
        """
        try:
            identity = await self.get_identity(unique_id)
            
            if not identity:
                return None
            
            # Get all applications for this identity
            applications = await application_repository.get_by_identity_id(unique_id)
            
            return {
                "unique_id": identity.unique_id,
                "status": identity.status,
                "created_at": identity.created_at.isoformat(),
                "updated_at": identity.updated_at.isoformat(),
                "metadata": identity.metadata,
                "application_count": len(identity.application_ids),
                "application_ids": identity.application_ids,
                "applications": [
                    {
                        "application_id": app.application_id,
                        "status": app.processing.status,
                        "created_at": app.created_at.isoformat()
                    }
                    for app in applications
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get identity details: {str(e)}")
            return None

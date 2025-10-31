"""Override service for manual review decisions"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from app.core.logging import logger
from app.database.repositories import ApplicationRepository, IdentityRepository
from app.models.application import ApplicationStatus
from app.models.identity import IdentityStatus
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service


class OverrideDecision(str, Enum):
    """Override decision types"""
    APPROVE_DUPLICATE = "approve_duplicate"
    REJECT_DUPLICATE = "reject_duplicate"
    FLAG_FOR_REVIEW = "flag_for_further_review"


class OverrideService:
    """Service for handling manual override decisions"""
    
    def __init__(self):
        self.min_justification_length = 10
        logger.info("Override service initialized")
    
    def validate_decision(self, decision: str) -> bool:
        """
        Validate override decision
        
        Args:
            decision: Decision string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            OverrideDecision(decision)
            return True
        except ValueError:
            return False
    
    def validate_justification(self, justification: str) -> bool:
        """
        Validate justification text
        
        Args:
            justification: Justification text
            
        Returns:
            True if valid, False otherwise
        """
        return len(justification.strip()) >= self.min_justification_length
    
    async def apply_override(self, application_id: str, decision: str,
                           justification: str, admin_id: str, db=None) -> Dict[str, Any]:
        """
        Apply manual override decision
        
        Args:
            application_id: Application ID
            decision: Override decision
            justification: Justification for decision
            admin_id: Admin user ID
            
        Returns:
            Dictionary with result information
            
        Raises:
            ValueError: If validation fails or operation fails
        """
        try:
            # Validate inputs
            if not self.validate_decision(decision):
                raise ValueError(f"Invalid decision: {decision}")
            
            if not self.validate_justification(justification):
                raise ValueError(f"Justification must be at least {self.min_justification_length} characters")
            
            # Get database connection if not provided
            if db is None:
                from app.database.mongodb import get_database
                db = await get_database()
            
            # Get application
            app_repo = ApplicationRepository(db)
            application = await app_repo.get_by_id(application_id)
            
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            # Store original status
            original_status = application.processing.status
            original_is_duplicate = application.result.is_duplicate
            
            # Apply decision
            new_status = original_status
            result_updates = {
                "reviewed_by": admin_id,
                "review_notes": justification,
                "reviewed_at": datetime.utcnow()
            }
            
            if decision == OverrideDecision.APPROVE_DUPLICATE:
                # Confirm as duplicate
                new_status = ApplicationStatus.DUPLICATE
                result_updates["is_duplicate"] = True
                result_updates["final_status"] = ApplicationStatus.DUPLICATE
                
                logger.info(f"Override: Approved duplicate for {application_id}")
                
            elif decision == OverrideDecision.REJECT_DUPLICATE:
                # Reject duplicate classification - mark as verified
                new_status = ApplicationStatus.VERIFIED
                result_updates["is_duplicate"] = False
                result_updates["final_status"] = ApplicationStatus.VERIFIED
                
                # If was previously duplicate, may need to create new identity
                if original_is_duplicate:
                    from app.services.identity_service import identity_service
                    
                    # Create new identity for this application
                    new_identity = await identity_service.create_identity(
                        application_id=application_id,
                        metadata={"override_reason": justification, "overridden_by": admin_id}
                    )
                    
                    result_updates["identity_id"] = new_identity.unique_id
                    
                    logger.info(f"Override: Created new identity {new_identity.unique_id} for {application_id}")
                
                logger.info(f"Override: Rejected duplicate for {application_id}")
                
            elif decision == OverrideDecision.FLAG_FOR_REVIEW:
                # Flag for further review - keep current status
                result_updates["requires_manual_review"] = True
                
                logger.info(f"Override: Flagged for review {application_id}")
            
            # Update application
            await app_repo.update_status(application_id, new_status)
            await app_repo.update_result(application_id, result_updates)
            
            # Log override decision to audit trail
            if db:
                await audit_service.log_override_decision(
                    db=db,
                    application_id=application_id,
                    admin_id=admin_id,
                    decision=decision,
                    justification=justification,
                    original_status=original_status.value,
                    new_status=new_status.value
                )
            
            # Send notification if webhook configured
            # (webhook URL would need to be retrieved from application or config)
            
            # Build result
            result = {
                "application_id": application_id,
                "decision": decision,
                "original_status": original_status,
                "new_status": new_status,
                "admin_id": admin_id,
                "justification": justification,
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            }
            
            logger.info(f"Override applied successfully: {application_id} - {decision}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply override: {str(e)}")
            raise ValueError(f"Override failed: {str(e)}")
    
    async def get_override_history(self, application_id: str) -> list[Dict[str, Any]]:
        """
        Get override history for an application
        
        Args:
            application_id: Application ID
            
        Returns:
            List of override records
        """
        try:
            # This would require querying audit logs
            # For now, return empty list as placeholder
            logger.info(f"Retrieved override history for {application_id}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get override history: {str(e)}")
            return []
    
    async def bulk_override(self, application_ids: list[str], decision: str,
                          justification: str, admin_id: str) -> Dict[str, Any]:
        """
        Apply override decision to multiple applications
        
        Args:
            application_ids: List of application IDs
            decision: Override decision
            justification: Justification for decision
            admin_id: Admin user ID
            
        Returns:
            Dictionary with bulk operation results
        """
        try:
            results = {
                "total": len(application_ids),
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for app_id in application_ids:
                try:
                    await self.apply_override(app_id, decision, justification, admin_id)
                    results["successful"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "application_id": app_id,
                        "error": str(e)
                    })
            
            logger.info(f"Bulk override completed: {results['successful']}/{results['total']} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk override failed: {str(e)}")
            raise ValueError(f"Bulk override failed: {str(e)}")
    
    def get_override_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about override operations
        
        Returns:
            Dictionary with override statistics
        """
        # This would require querying audit logs
        # For now, return placeholder data
        return {
            "total_overrides": 0,
            "approved_duplicates": 0,
            "rejected_duplicates": 0,
            "flagged_for_review": 0,
            "by_admin": {}
        }


# Global override service instance
override_service = OverrideService()

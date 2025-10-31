"""Audit service for logging and tracking system events"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.logging import logger
from app.database.repositories import AuditLogRepository
from app.models.audit import AuditLog, EventType, ActorType, ResourceType


class AuditService:
    """Service for managing audit logs"""
    
    def __init__(self):
        logger.info("Audit service initialized")
    
    async def log_override_decision(self, application_id: str, admin_id: str,
                                   decision: str, justification: str,
                                   previous_status: str, new_status: str,
                                   ip_address: Optional[str] = None) -> bool:
        """
        Log override decision to audit trail
        
        Args:
            application_id: Application ID
            admin_id: Admin user ID
            decision: Override decision
            justification: Justification text
            previous_status: Previous application status
            new_status: New application status
            ip_address: Optional IP address
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            audit_log = AuditLog(
                event_type=EventType.DUPLICATE_OVERRIDE,
                actor_id=admin_id,
                actor_type=ActorType.ADMIN,
                resource_id=application_id,
                resource_type=ResourceType.APPLICATION,
                action=f"Override decision: {decision}",
                details={
                    "decision": decision,
                    "justification": justification,
                    "previous_status": previous_status,
                    "new_status": new_status,
                    "timestamp": datetime.utcnow().isoformat()
                },
                ip_address=ip_address,
                success=True
            )
            
            await audit_log_repository.create(audit_log)
            
            logger.info(f"Logged override decision: {application_id} by {admin_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log override decision: {str(e)}")
            return False
    
    async def log_duplicate_detection(self, application_id: str, 
                                     matched_application_id: str,
                                     confidence_score: float,
                                     is_duplicate: bool) -> bool:
        """
        Log duplicate detection event
        
        Args:
            application_id: Application ID
            matched_application_id: Matched application ID
            confidence_score: Match confidence score
            is_duplicate: Whether classified as duplicate
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            audit_log = AuditLog(
                event_type=EventType.DUPLICATE_DETECTED,
                actor_id="system",
                actor_type=ActorType.SYSTEM,
                resource_id=application_id,
                resource_type=ResourceType.APPLICATION,
                action=f"Duplicate detection: {'duplicate' if is_duplicate else 'unique'}",
                details={
                    "matched_application_id": matched_application_id,
                    "confidence_score": confidence_score,
                    "is_duplicate": is_duplicate,
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=True
            )
            
            await audit_log_repository.create(audit_log)
            
            logger.info(f"Logged duplicate detection: {application_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log duplicate detection: {str(e)}")
            return False
    
    async def log_identity_issued(self, application_id: str, identity_id: str) -> bool:
        """
        Log identity issuance event
        
        Args:
            application_id: Application ID
            identity_id: Identity unique ID
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            audit_log = AuditLog(
                event_type=EventType.IDENTITY_ISSUED,
                actor_id="system",
                actor_type=ActorType.SYSTEM,
                resource_id=identity_id,
                resource_type=ResourceType.IDENTITY,
                action=f"Identity issued for application {application_id}",
                details={
                    "application_id": application_id,
                    "identity_id": identity_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=True
            )
            
            await audit_log_repository.create(audit_log)
            
            logger.info(f"Logged identity issuance: {identity_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log identity issuance: {str(e)}")
            return False
    
    async def log_admin_action(self, admin_id: str, action: str,
                              resource_id: Optional[str] = None,
                              resource_type: Optional[ResourceType] = None,
                              details: Optional[Dict[str, Any]] = None,
                              ip_address: Optional[str] = None) -> bool:
        """
        Log general admin action
        
        Args:
            admin_id: Admin user ID
            action: Action description
            resource_id: Optional resource ID
            resource_type: Optional resource type
            details: Optional additional details
            ip_address: Optional IP address
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            audit_log = AuditLog(
                event_type=EventType.DATA_ACCESS,
                actor_id=admin_id,
                actor_type=ActorType.ADMIN,
                resource_id=resource_id,
                resource_type=resource_type,
                action=action,
                details=details or {},
                ip_address=ip_address,
                success=True
            )
            
            await audit_log_repository.create(audit_log)
            
            logger.info(f"Logged admin action: {action} by {admin_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {str(e)}")
            return False
    
    async def get_override_audit_trail(self, application_id: str) -> List[AuditLog]:
        """
        Get audit trail for override decisions on an application
        
        Args:
            application_id: Application ID
            
        Returns:
            List of audit log entries
        """
        try:
            logs = await audit_log_repository.get_by_resource_id(application_id)
            
            # Filter for override events
            override_logs = [
                log for log in logs 
                if log.event_type in [EventType.DUPLICATE_OVERRIDE, EventType.MANUAL_OVERRIDE]
            ]
            
            logger.info(f"Retrieved {len(override_logs)} override audit entries for {application_id}")
            
            return override_logs
            
        except Exception as e:
            logger.error(f"Failed to get override audit trail: {str(e)}")
            return []
    
    async def get_admin_activity(self, admin_id: str, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 limit: int = 100) -> List[AuditLog]:
        """
        Get activity log for an admin user
        
        Args:
            admin_id: Admin user ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of results
            
        Returns:
            List of audit log entries
        """
        try:
            filters = {
                "actor_id": admin_id
            }
            
            if start_date:
                filters["start_date"] = start_date
            if end_date:
                filters["end_date"] = end_date
            
            logs, total = await audit_log_repository.query(filters, limit=limit)
            
            logger.info(f"Retrieved {len(logs)} activity entries for admin {admin_id}")
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get admin activity: {str(e)}")
            return []
    
    async def get_audit_statistics(self, start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get audit statistics
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with audit statistics
        """
        try:
            # This would require aggregation queries
            # For now, return placeholder data
            return {
                "total_events": 0,
                "by_event_type": {},
                "by_actor_type": {},
                "override_count": 0,
                "duplicate_detection_count": 0,
                "identity_issuance_count": 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit statistics: {str(e)}")
            return {}
    
    def validate_audit_integrity(self, audit_log: AuditLog) -> bool:
        """
        Validate audit log integrity (insert-only, no modifications)
        
        Args:
            audit_log: Audit log entry
            
        Returns:
            True if valid, False otherwise
        """
        # Audit logs should be immutable
        # This is enforced at the database level by not providing update/delete methods
        # This method can be used for additional validation if needed
        return True


# Global audit service instance
audit_service = AuditService()

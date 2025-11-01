"""Audit service for logging and tracking system events"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.logging import logger
from app.database.repositories import AuditLogRepository
from app.models.audit import AuditLog, EventType, ActorType, ResourceType


class AuditService:
    """Service for managing audit logs"""
    
    def __init__(self):
        self.audit_repo: Optional[AuditLogRepository] = None
        logger.info("Audit service initialized")
    
    def _get_audit_repo(self, db) -> AuditLogRepository:
        """Get audit repository instance with database connection"""
        return AuditLogRepository(db)
    
    async def create_audit_log(
        self,
        db,
        event_type: EventType,
        actor_id: str,
        actor_type: ActorType,
        action: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a structured audit log entry with automatic timestamp
        
        Args:
            db: Database connection
            event_type: Type of event being logged
            actor_id: ID of the actor performing the action
            actor_type: Type of actor (system, admin, etc.)
            action: Description of the action performed
            resource_id: Optional ID of the affected resource
            resource_type: Optional type of resource
            details: Optional additional event details
            ip_address: Optional IP address of the actor
            user_agent: Optional user agent string
            success: Whether the action was successful
            error_message: Optional error message if action failed
            
        Returns:
            Audit log ID if created successfully, None otherwise
        """
        try:
            # Create audit log with automatic timestamp
            audit_log = AuditLog(
                event_type=event_type,
                timestamp=datetime.utcnow(),  # Automatic timestamp
                actor_id=actor_id,
                actor_type=actor_type,
                resource_id=resource_id,
                resource_type=resource_type,
                action=action,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            
            # Store in MongoDB audit_logs collection
            audit_repo = self._get_audit_repo(db)
            log_id = await audit_repo.create(audit_log)
            
            logger.debug(f"Created audit log: {event_type} by {actor_id} (ID: {log_id})")
            
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            return None
    
    async def log_override_decision(
        self,
        db,
        application_id: str,
        admin_id: str,
        decision: str,
        justification: str,
        previous_status: str,
        new_status: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Log override decision to audit trail
        
        Args:
            db: Database connection
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
            log_id = await self.create_audit_log(
                db=db,
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
                    "new_status": new_status
                },
                ip_address=ip_address,
                success=True
            )
            
            if log_id:
                logger.info(f"Logged override decision: {application_id} by {admin_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to log override decision: {str(e)}")
            return False
    
    async def log_duplicate_detection(
        self,
        db,
        application_id: str,
        matched_application_id: Optional[str],
        confidence_score: float,
        is_duplicate: bool
    ) -> bool:
        """
        Log duplicate detection event
        
        Args:
            db: Database connection
            application_id: Application ID
            matched_application_id: Matched application ID (None if unique)
            confidence_score: Match confidence score
            is_duplicate: Whether classified as duplicate
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            log_id = await self.create_audit_log(
                db=db,
                event_type=EventType.DUPLICATE_DETECTED,
                actor_id="system",
                actor_type=ActorType.SYSTEM,
                resource_id=application_id,
                resource_type=ResourceType.APPLICATION,
                action=f"Duplicate detection: {'duplicate' if is_duplicate else 'unique'}",
                details={
                    "matched_application_id": matched_application_id,
                    "confidence_score": confidence_score,
                    "is_duplicate": is_duplicate
                },
                success=True
            )
            
            if log_id:
                logger.info(f"Logged duplicate detection: {application_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to log duplicate detection: {str(e)}")
            return False
    
    async def log_identity_issued(
        self,
        db,
        application_id: str,
        identity_id: str
    ) -> bool:
        """
        Log identity issuance event
        
        Args:
            db: Database connection
            application_id: Application ID
            identity_id: Identity unique ID
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            log_id = await self.create_audit_log(
                db=db,
                event_type=EventType.IDENTITY_ISSUED,
                actor_id="system",
                actor_type=ActorType.SYSTEM,
                resource_id=identity_id,
                resource_type=ResourceType.IDENTITY,
                action=f"Identity issued for application {application_id}",
                details={
                    "application_id": application_id,
                    "identity_id": identity_id
                },
                success=True
            )
            
            if log_id:
                logger.info(f"Logged identity issuance: {identity_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to log identity issuance: {str(e)}")
            return False
    
    async def log_admin_action(
        self,
        db,
        admin_id: str,
        action: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Log general admin action
        
        Args:
            db: Database connection
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
            log_id = await self.create_audit_log(
                db=db,
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
            
            if log_id:
                logger.info(f"Logged admin action: {action} by {admin_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {str(e)}")
            return False
    
    async def log_application_submission(
        self,
        db,
        application_id: str,
        applicant_email: str,
        applicant_name: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Log application submission event
        
        Args:
            db: Database connection
            application_id: Application ID
            applicant_email: Applicant email
            applicant_name: Applicant name
            ip_address: Optional IP address
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            log_id = await self.create_audit_log(
                db=db,
                event_type=EventType.APPLICATION_SUBMITTED,
                actor_id="system",
                actor_type=ActorType.API,
                resource_id=application_id,
                resource_type=ResourceType.APPLICATION,
                action="Application submitted for processing",
                details={
                    "applicant_email": applicant_email,
                    "applicant_name": applicant_name
                },
                ip_address=ip_address,
                success=True
            )
            
            if log_id:
                logger.info(f"Logged application submission: {application_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to log application submission: {str(e)}")
            return False
    
    async def get_override_audit_trail(
        self,
        db,
        application_id: str
    ) -> List[AuditLog]:
        """
        Get audit trail for override decisions on an application
        
        Args:
            db: Database connection
            application_id: Application ID
            
        Returns:
            List of audit log entries
        """
        try:
            audit_repo = self._get_audit_repo(db)
            logs = await audit_repo.get_by_resource_id(application_id)
            
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
    
    async def get_admin_activity(
        self,
        db,
        admin_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get activity log for an admin user
        
        Args:
            db: Database connection
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
            
            audit_repo = self._get_audit_repo(db)
            logs, total = await audit_repo.query(filters, limit=limit)
            
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
    
    async def log_application_completion(
        self,
        db,
        application_id: str,
        identity_id: str,
        is_duplicate: bool,
        status: str
    ) -> Optional[str]:
        """
        Log application processing completion
        
        Args:
            db: Database connection
            application_id: Application identifier
            identity_id: Assigned identity ID
            is_duplicate: Whether duplicate was detected
            status: Final application status
            
        Returns:
            Audit log ID if successful
        """
        return await self.create_audit_log(
            db=db,
            event_type=EventType.APPLICATION_SUBMITTED,
            actor_id="system",
            actor_type=ActorType.SYSTEM,
            action=f"Application processing completed with status: {status}",
            resource_id=application_id,
            resource_type=ResourceType.APPLICATION,
            details={
                "identity_id": identity_id,
                "is_duplicate": is_duplicate,
                "final_status": status
            },
            success=True
        )
    
    async def log_application_rejection(
        self,
        db,
        application_id: str,
        error_code: str,
        error_message: str
    ) -> Optional[str]:
        """
        Log application rejection
        
        Args:
            db: Database connection
            application_id: Application identifier
            error_code: Error code
            error_message: Error message
            
        Returns:
            Audit log ID if successful
        """
        return await self.create_audit_log(
            db=db,
            event_type=EventType.APPLICATION_SUBMITTED,
            actor_id="system",
            actor_type=ActorType.SYSTEM,
            action=f"Application rejected: {error_code}",
            resource_id=application_id,
            resource_type=ResourceType.APPLICATION,
            details={
                "error_code": error_code,
                "error_message": error_message
            },
            success=False,
            error_message=error_message
        )
    
    async def log_application_failure(
        self,
        db,
        application_id: str,
        error_message: str
    ) -> Optional[str]:
        """
        Log application processing failure
        
        Args:
            db: Database connection
            application_id: Application identifier
            error_message: Error message
            
        Returns:
            Audit log ID if successful
        """
        return await self.create_audit_log(
            db=db,
            event_type=EventType.APPLICATION_SUBMITTED,
            actor_id="system",
            actor_type=ActorType.SYSTEM,
            action="Application processing failed",
            resource_id=application_id,
            resource_type=ResourceType.APPLICATION,
            details={
                "error_message": error_message
            },
            success=False,
            error_message=error_message
        )
    
    async def log_override_decision(
        self,
        db,
        application_id: str,
        admin_id: str,
        decision: str,
        justification: str,
        original_status: str,
        new_status: str
    ) -> Optional[str]:
        """
        Log admin override decision
        
        Args:
            db: Database connection
            application_id: Application identifier
            admin_id: Admin user ID
            decision: Override decision
            justification: Justification for decision
            original_status: Original application status
            new_status: New application status
            
        Returns:
            Audit log ID if successful
        """
        return await self.create_audit_log(
            db=db,
            event_type=EventType.OVERRIDE_DECISION,
            actor_id=admin_id,
            actor_type=ActorType.ADMIN,
            action=f"Override decision: {decision}",
            resource_id=application_id,
            resource_type=ResourceType.APPLICATION,
            details={
                "decision": decision,
                "justification": justification,
                "original_status": original_status,
                "new_status": new_status
            },
            success=True
        )


# Global audit service instance
audit_service = AuditService()

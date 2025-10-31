"""Review workflow integration service"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.logging import logger
from app.database.repositories import ApplicationRepository
from app.models.application import ApplicationStatus
from app.services.deduplication_service import deduplication_service
from app.services.override_service import override_service
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service


class ReviewWorkflowService:
    """
    Service for integrating duplicate detection with review interface
    and managing the complete review workflow
    """
    
    def __init__(self):
        logger.info("Review workflow service initialized")
    
    async def get_pending_reviews(
        self,
        db,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get applications pending manual review
        
        Args:
            db: Database connection
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of applications requiring review
        """
        app_repo = ApplicationRepository(db)
        
        # Get applications with pending_review status
        applications = await app_repo.get_by_status(
            status=ApplicationStatus.PENDING_REVIEW,
            limit=limit,
            skip=skip
        )
        
        review_cases = []
        for app in applications:
            # Get duplicate match details if available
            matched_app_id = None
            confidence_score = None
            
            if app.result.matches:
                matched_app_id = app.result.matches[0].get("matched_application_id")
                confidence_score = app.result.matches[0].get("confidence_score")
            
            review_cases.append({
                "application_id": app.application_id,
                "applicant_name": app.applicant_data.name,
                "matched_application_id": matched_app_id,
                "confidence_score": confidence_score,
                "created_at": app.created_at,
                "requires_review": True,
                "review_reason": app.result.review_reason
            })
        
        logger.info(f"Retrieved {len(review_cases)} pending reviews")
        return review_cases
    
    async def get_review_case_details(
        self,
        db,
        application_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a review case
        
        Args:
            db: Database connection
            application_id: Application identifier
            
        Returns:
            Detailed review case information
        """
        app_repo = ApplicationRepository(db)
        
        # Get current application
        application = await app_repo.get_by_id(application_id)
        if not application:
            return None
        
        # Get matched application if duplicate
        matched_application = None
        if application.result.is_duplicate and application.result.matches:
            matched_app_id = application.result.matches[0].get("matched_application_id")
            if matched_app_id:
                matched_application = await app_repo.get_by_id(matched_app_id)
        
        # Build detailed response
        details = {
            "application_id": application.application_id,
            "current_application": {
                "applicant_name": application.applicant_data.name,
                "applicant_email": application.applicant_data.email,
                "photograph_path": application.photograph.path,
                "quality_score": application.processing.quality_score,
                "created_at": application.created_at.isoformat()
            },
            "matched_application": None,
            "confidence_score": None,
            "review_reason": application.result.review_reason,
            "status": application.processing.status.value
        }
        
        if matched_application:
            details["matched_application"] = {
                "application_id": matched_application.application_id,
                "applicant_name": matched_application.applicant_data.name,
                "applicant_email": matched_application.applicant_data.email,
                "photograph_path": matched_application.photograph.path,
                "identity_id": matched_application.result.identity_id,
                "created_at": matched_application.created_at.isoformat()
            }
            details["confidence_score"] = application.result.matches[0].get("confidence_score")
        
        return details
    
    async def submit_review_decision(
        self,
        db,
        application_id: str,
        decision: str,
        justification: str,
        reviewer_id: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit review decision and propagate through workflow
        
        Args:
            db: Database connection
            application_id: Application identifier
            decision: Review decision
            justification: Justification for decision
            reviewer_id: Reviewer user ID
            webhook_url: Optional webhook URL for notifications
            
        Returns:
            Result of review decision
        """
        try:
            # Apply override decision
            result = await override_service.apply_override(
                application_id=application_id,
                decision=decision,
                justification=justification,
                admin_id=reviewer_id,
                db=db
            )
            
            # Send notification if webhook configured
            if webhook_url:
                await notification_service.notify_application_status(
                    application_id=application_id,
                    status=result["new_status"].value.lower(),
                    webhook_url=webhook_url,
                    additional_data={
                        "decision": decision,
                        "reviewed_by": reviewer_id,
                        "justification": justification
                    }
                )
            
            logger.info(
                f"Review decision submitted for {application_id}: {decision} "
                f"by {reviewer_id}"
            )
            
            return {
                "success": True,
                "application_id": application_id,
                "decision": decision,
                "new_status": result["new_status"].value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to submit review decision: {str(e)}")
            raise
    
    async def get_review_statistics(self, db) -> Dict[str, Any]:
        """
        Get statistics about review workflow
        
        Args:
            db: Database connection
            
        Returns:
            Review workflow statistics
        """
        app_repo = ApplicationRepository(db)
        
        # Get counts by status
        pending_reviews = await app_repo.get_by_status(
            status=ApplicationStatus.PENDING_REVIEW,
            limit=1000
        )
        
        # Get audit statistics for overrides
        audit_stats = await audit_service.get_audit_statistics(
            db=db,
            start_date=None,
            end_date=None
        )
        
        return {
            "pending_reviews": len(pending_reviews),
            "total_overrides": audit_stats.get("override_count", 0),
            "review_backlog_age_days": self._calculate_backlog_age(pending_reviews)
        }
    
    def _calculate_backlog_age(self, applications: List) -> float:
        """Calculate average age of review backlog in days"""
        if not applications:
            return 0.0
        
        now = datetime.utcnow()
        total_age = sum(
            (now - app.created_at).total_seconds() / 86400
            for app in applications
        )
        
        return round(total_age / len(applications), 2)
    
    async def bulk_review_decision(
        self,
        db,
        application_ids: List[str],
        decision: str,
        justification: str,
        reviewer_id: str
    ) -> Dict[str, Any]:
        """
        Apply review decision to multiple applications
        
        Args:
            db: Database connection
            application_ids: List of application IDs
            decision: Review decision
            justification: Justification for decision
            reviewer_id: Reviewer user ID
            
        Returns:
            Bulk operation results
        """
        results = {
            "total": len(application_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for app_id in application_ids:
            try:
                await self.submit_review_decision(
                    db=db,
                    application_id=app_id,
                    decision=decision,
                    justification=justification,
                    reviewer_id=reviewer_id
                )
                results["successful"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "application_id": app_id,
                    "error": str(e)
                })
        
        logger.info(
            f"Bulk review completed: {results['successful']}/{results['total']} "
            f"successful"
        )
        
        return results


# Global review workflow service instance
review_workflow_service = ReviewWorkflowService()

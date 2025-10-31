"""Notification service for status updates and webhooks"""

import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from app.core.logging import logger
from app.core.config import settings


class NotificationEvent(str, Enum):
    """Notification event types"""
    APPLICATION_SUBMITTED = "application.submitted"
    APPLICATION_PROCESSING = "application.processing"
    APPLICATION_APPROVED = "application.approved"
    APPLICATION_REJECTED = "application.rejected"
    APPLICATION_FAILED = "application.failed"
    APPLICATION_PENDING_REVIEW = "application.pending_review"
    IDENTITY_CREATED = "identity.created"
    DUPLICATE_DETECTED = "duplicate.detected"


class NotificationService:
    """Service for sending status notifications via webhooks"""
    
    def __init__(self):
        self.webhook_timeout = 10  # seconds
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        logger.info("Notification service initialized")
    
    async def send_webhook(
        self,
        webhook_url: str,
        event: NotificationEvent,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send webhook notification with retry logic
        
        Args:
            webhook_url: Webhook endpoint URL
            event: Event type
            data: Event data payload
            headers: Optional custom headers
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "FaceAuth-Webhook/1.0"
        }
        
        if headers:
            default_headers.update(headers)
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.webhook_timeout) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers=default_headers
                    )
                    
                    if response.status_code in [200, 201, 202, 204]:
                        logger.info(
                            f"Webhook sent successfully: {event.value} to {webhook_url} "
                            f"(status: {response.status_code})"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Webhook returned non-success status: {response.status_code} "
                            f"for {event.value} to {webhook_url}"
                        )
                        
            except httpx.TimeoutException:
                logger.warning(
                    f"Webhook timeout (attempt {attempt + 1}/{self.max_retries}): "
                    f"{event.value} to {webhook_url}"
                )
            except httpx.RequestError as e:
                logger.warning(
                    f"Webhook request error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{str(e)} for {event.value} to {webhook_url}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected webhook error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{str(e)} for {event.value} to {webhook_url}"
                )
            
            # Retry with exponential backoff
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        logger.error(
            f"Webhook failed after {self.max_retries} attempts: "
            f"{event.value} to {webhook_url}"
        )
        return False
    
    async def notify_application_status(
        self,
        application_id: str,
        status: str,
        webhook_url: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send application status notification
        
        Args:
            application_id: Application identifier
            status: Application status
            webhook_url: Optional webhook URL (uses default if not provided)
            additional_data: Optional additional data to include
            
        Returns:
            True if notification sent successfully
        """
        if not webhook_url:
            # No webhook configured
            logger.debug(f"No webhook configured for application {application_id}")
            return False
        
        # Map status to event
        event_mapping = {
            "pending": NotificationEvent.APPLICATION_SUBMITTED,
            "processing": NotificationEvent.APPLICATION_PROCESSING,
            "approved": NotificationEvent.APPLICATION_APPROVED,
            "rejected": NotificationEvent.APPLICATION_REJECTED,
            "failed": NotificationEvent.APPLICATION_FAILED,
            "pending_review": NotificationEvent.APPLICATION_PENDING_REVIEW
        }
        
        event = event_mapping.get(status.lower(), NotificationEvent.APPLICATION_PROCESSING)
        
        data = {
            "application_id": application_id,
            "status": status,
            **(additional_data or {})
        }
        
        return await self.send_webhook(webhook_url, event, data)
    
    async def notify_identity_created(
        self,
        identity_id: str,
        application_id: str,
        webhook_url: Optional[str] = None
    ) -> bool:
        """
        Send identity creation notification
        
        Args:
            identity_id: Identity identifier
            application_id: Application identifier
            webhook_url: Optional webhook URL
            
        Returns:
            True if notification sent successfully
        """
        if not webhook_url:
            return False
        
        data = {
            "identity_id": identity_id,
            "application_id": application_id
        }
        
        return await self.send_webhook(
            webhook_url,
            NotificationEvent.IDENTITY_CREATED,
            data
        )
    
    async def notify_duplicate_detected(
        self,
        application_id: str,
        matched_application_id: str,
        confidence_score: float,
        webhook_url: Optional[str] = None
    ) -> bool:
        """
        Send duplicate detection notification
        
        Args:
            application_id: Application identifier
            matched_application_id: Matched application ID
            confidence_score: Confidence score
            webhook_url: Optional webhook URL
            
        Returns:
            True if notification sent successfully
        """
        if not webhook_url:
            return False
        
        data = {
            "application_id": application_id,
            "matched_application_id": matched_application_id,
            "confidence_score": confidence_score
        }
        
        return await self.send_webhook(
            webhook_url,
            NotificationEvent.DUPLICATE_DETECTED,
            data
        )
    
    async def send_batch_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Send multiple notifications in parallel
        
        Args:
            notifications: List of notification configs with webhook_url, event, and data
            
        Returns:
            Dictionary with success and failure counts
        """
        tasks = []
        for notification in notifications:
            task = self.send_webhook(
                webhook_url=notification["webhook_url"],
                event=notification["event"],
                data=notification["data"],
                headers=notification.get("headers")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        failure_count = len(results) - success_count
        
        logger.info(
            f"Batch notifications completed: {success_count} succeeded, "
            f"{failure_count} failed out of {len(notifications)}"
        )
        
        return {
            "total": len(notifications),
            "success": success_count,
            "failed": failure_count
        }


# Global notification service instance
notification_service = NotificationService()

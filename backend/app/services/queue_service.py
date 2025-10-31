"""Simple in-memory queue service for application processing"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import deque
from app.core.logging import logger
from app.core.config import settings


class QueueService:
    """In-memory queue service for local development"""
    
    def __init__(self):
        self._queue: deque = deque()
        self._processing: Dict[str, Dict[str, Any]] = {}
        self._max_queue_size = settings.MAX_QUEUE_SIZE
        self._lock = asyncio.Lock()
        self._stats = {
            "total_enqueued": 0,
            "total_processed": 0,
            "total_failed": 0,
            "current_queue_size": 0
        }
    
    async def enqueue_application(self, application_data: Dict[str, Any]) -> bool:
        """
        Add application to processing queue
        
        Args:
            application_data: Application data including application_id
            
        Returns:
            True if enqueued successfully, False if queue is full
        """
        async with self._lock:
            if len(self._queue) >= self._max_queue_size:
                logger.warning(f"Queue is full. Size: {len(self._queue)}")
                return False
            
            application_id = application_data.get("application_id")
            
            # Add to queue
            self._queue.append({
                **application_data,
                "enqueued_at": datetime.utcnow().isoformat(),
                "retry_count": 0
            })
            
            # Update stats
            self._stats["total_enqueued"] += 1
            self._stats["current_queue_size"] = len(self._queue)
            
            logger.info(f"Application enqueued: {application_id}. Queue size: {len(self._queue)}")
            
            return True
    
    async def dequeue_application(self) -> Optional[Dict[str, Any]]:
        """
        Get next application from queue
        
        Returns:
            Application data or None if queue is empty
        """
        async with self._lock:
            if not self._queue:
                return None
            
            application_data = self._queue.popleft()
            application_id = application_data.get("application_id")
            
            # Mark as processing
            self._processing[application_id] = {
                **application_data,
                "processing_started_at": datetime.utcnow().isoformat()
            }
            
            # Update stats
            self._stats["current_queue_size"] = len(self._queue)
            
            logger.info(f"Application dequeued: {application_id}. Queue size: {len(self._queue)}")
            
            return application_data
    
    async def mark_completed(self, application_id: str, success: bool = True) -> None:
        """
        Mark application processing as completed
        
        Args:
            application_id: Application identifier
            success: Whether processing was successful
        """
        async with self._lock:
            if application_id in self._processing:
                del self._processing[application_id]
                
                if success:
                    self._stats["total_processed"] += 1
                    logger.info(f"Application processing completed: {application_id}")
                else:
                    self._stats["total_failed"] += 1
                    logger.error(f"Application processing failed: {application_id}")
    
    async def requeue_application(self, application_id: str, max_retries: int = 3) -> bool:
        """
        Requeue failed application for retry
        
        Args:
            application_id: Application identifier
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if requeued, False if max retries exceeded
        """
        async with self._lock:
            if application_id not in self._processing:
                logger.warning(f"Application not found in processing: {application_id}")
                return False
            
            application_data = self._processing[application_id]
            retry_count = application_data.get("retry_count", 0)
            
            if retry_count >= max_retries:
                logger.error(f"Max retries exceeded for application: {application_id}")
                del self._processing[application_id]
                self._stats["total_failed"] += 1
                return False
            
            # Increment retry count and requeue
            application_data["retry_count"] = retry_count + 1
            application_data["requeued_at"] = datetime.utcnow().isoformat()
            
            self._queue.append(application_data)
            del self._processing[application_id]
            
            self._stats["current_queue_size"] = len(self._queue)
            
            logger.info(f"Application requeued: {application_id}. Retry: {retry_count + 1}/{max_retries}")
            
            return True
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        async with self._lock:
            return len(self._queue)
    
    async def get_processing_count(self) -> int:
        """Get number of applications currently being processed"""
        async with self._lock:
            return len(self._processing)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        async with self._lock:
            return {
                **self._stats,
                "processing_count": len(self._processing)
            }
    
    async def get_processing_applications(self) -> List[str]:
        """Get list of application IDs currently being processed"""
        async with self._lock:
            return list(self._processing.keys())
    
    async def clear_queue(self) -> int:
        """
        Clear all items from queue (for testing/maintenance)
        
        Returns:
            Number of items cleared
        """
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._stats["current_queue_size"] = 0
            logger.warning(f"Queue cleared. {count} items removed")
            return count
    
    async def is_processing(self, application_id: str) -> bool:
        """Check if application is currently being processed"""
        async with self._lock:
            return application_id in self._processing


# Global queue service instance
queue_service = QueueService()

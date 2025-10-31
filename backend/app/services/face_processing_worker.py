"""Background worker for processing face recognition tasks"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.logging import logger
from app.services.queue_service import queue_service
from app.services.face_recognition_service import face_recognition_service, FaceRecognitionError
from app.services.embedding_cache_service import embedding_cache_service
from app.database.repositories import ApplicationRepository
from app.models.application import ApplicationStatus


class FaceProcessingWorker:
    """Background worker for processing queued applications"""
    
    def __init__(self):
        self.is_running = False
        self.max_retries = 3
        self.processing_delay = 0.1  # Delay between queue checks in seconds
        
    async def process_application(self, application_data: Dict[str, Any]) -> bool:
        """
        Process a single application through face recognition pipeline
        
        Args:
            application_data: Application data from queue
            
        Returns:
            True if processing succeeded, False otherwise
        """
        application_id = application_data.get("application_id")
        photograph_path = application_data.get("photograph_path")
        
        try:
            logger.info(f"Starting face recognition processing for application: {application_id}")
            
            # Update status to processing
            await application_repository.update_processing_status(
                application_id=application_id,
                status=ApplicationStatus.PROCESSING,
                processing_started_at=datetime.utcnow()
            )
            
            # Check cache first
            cached_embedding = await embedding_cache_service.get(application_id)
            
            if cached_embedding:
                logger.info(f"Using cached embedding for application: {application_id}")
                result = {
                    "embedding": cached_embedding,
                    "bounding_box": None,  # Not stored in cache
                    "quality_score": 1.0,  # Assume good quality if cached
                    "face_detected": True
                }
            else:
                # Process photograph through face recognition pipeline
                result = face_recognition_service.process_photograph(photograph_path)
                
                # Cache the embedding
                await embedding_cache_service.set(application_id, result["embedding"])
            
            # Update application with results
            await application_repository.update_face_recognition_results(
                application_id=application_id,
                embedding=result["embedding"],
                bounding_box=result["bounding_box"],
                quality_score=result["quality_score"],
                face_detected=result["face_detected"]
            )
            
            logger.info(f"Face recognition processing completed for application: {application_id}")
            
            return True
            
        except FaceRecognitionError as e:
            # Handle face recognition specific errors
            logger.error(f"Face recognition error for application {application_id}: {e.error_code} - {e.message}")
            
            # Update application with error details
            await application_repository.update_processing_error(
                application_id=application_id,
                status=ApplicationStatus.REJECTED,
                error_code=e.error_code,
                error_message=e.message
            )
            
            return False
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error processing application {application_id}: {str(e)}")
            
            # Update application with generic error
            await application_repository.update_processing_error(
                application_id=application_id,
                status=ApplicationStatus.FAILED,
                error_code="E999",
                error_message=f"Processing failed: {str(e)}"
            )
            
            return False
    
    async def process_with_retry(self, application_data: Dict[str, Any]) -> bool:
        """
        Process application with retry logic
        
        Args:
            application_data: Application data from queue
            
        Returns:
            True if processing succeeded, False if all retries exhausted
        """
        application_id = application_data.get("application_id")
        retry_count = application_data.get("retry_count", 0)
        
        # Attempt processing
        success = await self.process_application(application_data)
        
        if success:
            # Mark as completed in queue
            await queue_service.mark_completed(application_id, success=True)
            return True
        
        # Check if we should retry
        if retry_count < self.max_retries:
            logger.info(f"Retrying application {application_id}. Attempt {retry_count + 1}/{self.max_retries}")
            
            # Requeue for retry
            requeued = await queue_service.requeue_application(application_id, max_retries=self.max_retries)
            
            if requeued:
                return False  # Will be processed again
        
        # All retries exhausted
        logger.error(f"All retries exhausted for application {application_id}")
        await queue_service.mark_completed(application_id, success=False)
        
        return False
    
    async def run(self):
        """
        Main worker loop - continuously processes queued applications
        """
        self.is_running = True
        logger.info("Face processing worker started")
        
        while self.is_running:
            try:
                # Get next application from queue
                application_data = await queue_service.dequeue_application()
                
                if application_data:
                    # Process application with retry logic
                    await self.process_with_retry(application_data)
                else:
                    # Queue is empty, wait before checking again
                    await asyncio.sleep(self.processing_delay)
                    
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(1)  # Wait before continuing
        
        logger.info("Face processing worker stopped")
    
    async def stop(self):
        """Stop the worker"""
        logger.info("Stopping face processing worker...")
        self.is_running = False
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get worker status
        
        Returns:
            Dictionary with worker status information
        """
        queue_stats = await queue_service.get_stats()
        
        return {
            "is_running": self.is_running,
            "max_retries": self.max_retries,
            "queue_stats": queue_stats
        }


# Global worker instance
face_processing_worker = FaceProcessingWorker()

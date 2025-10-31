"""End-to-end application processing orchestrator"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np

from app.core.logging import logger
from app.services.queue_service import queue_service
from app.services.photograph_service import photograph_service
from app.services.face_recognition_service import face_recognition_service, FaceRecognitionError
from app.services.face_detection_service import face_detection_service, FaceDetectionError
from app.services.face_embedding_service import face_embedding_service
from app.services.deduplication_service import deduplication_service
from app.services.identity_service import identity_service
from app.services.vector_index_service import vector_index_service
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service
from app.services.websocket_manager import websocket_manager
from app.database.repositories import ApplicationRepository, IdentityRepository, EmbeddingRepository
from app.models.application import ApplicationStatus
from app.utils.error_responses import ErrorCode


class ApplicationProcessor:
    """
    Orchestrates end-to-end application processing workflow:
    1. Photograph ingestion and validation
    2. Face recognition and quality assessment
    3. De-duplication check
    4. Identity management (new or existing)
    5. Status updates and audit logging
    """
    
    def __init__(self):
        self.is_running = False
        self.max_retries = 3
        self.processing_delay = 0.1
        
    async def process_application_end_to_end(
        self, 
        application_id: str,
        photograph_base64: str,
        photograph_format: str,
        db,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process application through complete workflow
        
        Args:
            application_id: Unique application identifier
            photograph_base64: Base64 encoded photograph
            photograph_format: Image format (jpg, png)
            db: Database connection
            
        Returns:
            Processing result with status and details
        """
        app_repo = ApplicationRepository(db)
        identity_repo = IdentityRepository(db)
        embedding_repo = EmbeddingRepository(db)
        
        try:
            logger.info(f"Starting end-to-end processing for application: {application_id}")
            
            # ===== STAGE 1: Photograph Ingestion =====
            await self._update_stage(app_repo, application_id, "ingestion", ApplicationStatus.PROCESSING)
            
            # Send WebSocket update
            await websocket_manager.send_processing_update(
                application_id=application_id,
                stage="ingestion",
                status="in_progress",
                progress=10,
                message="Saving photograph"
            )
            
            # Send processing notification
            if webhook_url:
                await notification_service.notify_application_status(
                    application_id=application_id,
                    status="processing",
                    webhook_url=webhook_url,
                    additional_data={"stage": "ingestion"}
                )
            
            photograph_path = await photograph_service.save_photograph(
                application_id=application_id,
                photograph_base64=photograph_base64,
                format=photograph_format
            )
            
            logger.info(f"[{application_id}] Stage 1: Photograph saved to {photograph_path}")
            
            # Send WebSocket update
            await websocket_manager.send_processing_update(
                application_id=application_id,
                stage="ingestion",
                status="completed",
                progress=20,
                message="Photograph saved successfully"
            )
            
            # ===== STAGE 2: Face Recognition =====
            await self._update_stage(app_repo, application_id, "face_recognition", ApplicationStatus.PROCESSING)
            
            # Send WebSocket update
            await websocket_manager.send_processing_update(
                application_id=application_id,
                stage="face_detection",
                status="in_progress",
                progress=30,
                message="Detecting face in photograph"
            )
            
            try:
                face_result = face_recognition_service.process_photograph(photograph_path)
                
                # Update application with face recognition results
                await app_repo.update_face_recognition_results(
                    application_id=application_id,
                    embedding=face_result["embedding"],
                    bounding_box=face_result["bounding_box"],
                    quality_score=face_result["quality_score"],
                    face_detected=face_result["face_detected"]
                )
                
                logger.info(
                    f"[{application_id}] Stage 2: Face recognition completed. "
                    f"Quality: {face_result['quality_score']:.3f}"
                )
                
                # Send WebSocket update
                await websocket_manager.send_processing_update(
                    application_id=application_id,
                    stage="face_recognition",
                    status="completed",
                    progress=50,
                    message="Face detected and embedding generated",
                    details={
                        "quality_score": face_result['quality_score'],
                        "face_detected": face_result['face_detected']
                    }
                )
                
            except FaceRecognitionError as e:
                # Face recognition failed - reject application
                await self._handle_rejection(
                    app_repo, application_id, e.error_code, e.message, db
                )
                
                # Send WebSocket error update
                await websocket_manager.send_error_update(
                    application_id=application_id,
                    error_code=e.error_code.value,
                    error_message=e.message,
                    details=e.details
                )
                
                # Send rejection notification
                if webhook_url:
                    await notification_service.notify_application_status(
                        application_id=application_id,
                        status="rejected",
                        webhook_url=webhook_url,
                        additional_data={
                            "error_code": e.error_code.value,
                            "error_message": e.message
                        }
                    )
                
                return {
                    "status": "rejected",
                    "error_code": e.error_code.value,
                    "error_message": e.message
                }
            
            # ===== STAGE 3: De-duplication Check =====
            await self._update_stage(app_repo, application_id, "deduplication", ApplicationStatus.PROCESSING)
            
            # Send WebSocket update
            await websocket_manager.send_processing_update(
                application_id=application_id,
                stage="duplicate_detection",
                status="in_progress",
                progress=60,
                message="Checking for duplicate applications"
            )
            
            embedding_array = np.array(face_result["embedding"], dtype=np.float32)
            
            dedup_result = await deduplication_service.detect_duplicates(
                embedding=embedding_array,
                application_id=application_id,
                db=db
            )
            
            logger.info(
                f"[{application_id}] Stage 3: De-duplication check completed. "
                f"Is duplicate: {dedup_result.is_duplicate}, "
                f"Matches: {len(dedup_result.matches)}"
            )
            
            # Send WebSocket update
            await websocket_manager.send_processing_update(
                application_id=application_id,
                stage="duplicate_detection",
                status="completed",
                progress=70,
                message="Duplicate detection completed",
                details={
                    "is_duplicate": dedup_result.is_duplicate,
                    "match_count": len(dedup_result.matches)
                }
            )
            
            # ===== STAGE 4: Identity Management =====
            await self._update_stage(app_repo, application_id, "identity_management", ApplicationStatus.PROCESSING)
            
            # Send WebSocket update
            await websocket_manager.send_processing_update(
                application_id=application_id,
                stage="identity_management",
                status="in_progress",
                progress=80,
                message="Assigning identity"
            )
            
            if dedup_result.is_duplicate:
                # Existing identity found
                matched_app_id = dedup_result.matches[0].matched_application_id
                confidence = dedup_result.matches[0].confidence_score
                
                # Get identity from matched application
                matched_app = await app_repo.get_by_id(matched_app_id)
                
                if matched_app and matched_app.result.identity_id:
                    identity_id = matched_app.result.identity_id
                    
                    # Link application to existing identity
                    await identity_service.link_application_to_identity(
                        db=db,
                        identity_id=identity_id,
                        application_id=application_id
                    )
                    
                    logger.info(
                        f"[{application_id}] Stage 4: Linked to existing identity {identity_id}. "
                        f"Confidence: {confidence:.3f}"
                    )
                    
                    # Check if manual review is required
                    if dedup_result.requires_manual_review:
                        final_status = ApplicationStatus.PENDING_REVIEW
                        logger.warning(
                            f"[{application_id}] Flagged for manual review: {dedup_result.review_reason}"
                        )
                    else:
                        final_status = ApplicationStatus.APPROVED
                    
                else:
                    # Matched application has no identity (shouldn't happen)
                    logger.error(f"[{application_id}] Matched application has no identity ID")
                    identity_id = await self._create_new_identity(
                        app_repo, identity_repo, embedding_repo, application_id, embedding_array, db
                    )
                    final_status = ApplicationStatus.APPROVED
                    
            else:
                # No duplicate found - create new identity
                identity_id = await self._create_new_identity(
                    app_repo, identity_repo, embedding_repo, application_id, embedding_array, db
                )
                final_status = ApplicationStatus.APPROVED
                
                logger.info(f"[{application_id}] Stage 4: Created new identity {identity_id}")
            
            # ===== STAGE 5: Finalization =====
            # Update application with final result
            await app_repo.update_result(
                application_id=application_id,
                result_data={
                    "is_duplicate": dedup_result.is_duplicate,
                    "identity_id": identity_id,
                    "confidence_score": dedup_result.matches[0].confidence_score if dedup_result.matches else 1.0,
                    "requires_manual_review": dedup_result.requires_manual_review,
                    "review_reason": dedup_result.review_reason
                }
            )
            
            # Update final status
            await app_repo.update_status(
                application_id=application_id,
                status=final_status
            )
            
            # Log completion to audit trail
            await audit_service.log_application_completion(
                db=db,
                application_id=application_id,
                identity_id=identity_id,
                is_duplicate=dedup_result.is_duplicate,
                status=final_status.value
            )
            
            logger.info(
                f"[{application_id}] Processing completed successfully. "
                f"Status: {final_status.value}, Identity: {identity_id}"
            )
            
            # Send WebSocket completion update
            await websocket_manager.send_completion_update(
                application_id=application_id,
                result={
                    "status": final_status.value,
                    "identity_id": identity_id,
                    "is_duplicate": dedup_result.is_duplicate,
                    "requires_manual_review": dedup_result.requires_manual_review,
                    "confidence_score": dedup_result.matches[0].confidence_score if dedup_result.matches else 1.0
                }
            )
            
            # Send completion notification
            if webhook_url:
                await notification_service.notify_application_status(
                    application_id=application_id,
                    status=final_status.value.lower(),
                    webhook_url=webhook_url,
                    additional_data={
                        "identity_id": identity_id,
                        "is_duplicate": dedup_result.is_duplicate,
                        "requires_manual_review": dedup_result.requires_manual_review
                    }
                )
                
                # Send identity created notification if new identity
                if not dedup_result.is_duplicate:
                    await notification_service.notify_identity_created(
                        identity_id=identity_id,
                        application_id=application_id,
                        webhook_url=webhook_url
                    )
                
                # Send duplicate detected notification if duplicate
                if dedup_result.is_duplicate and dedup_result.matches:
                    await notification_service.notify_duplicate_detected(
                        application_id=application_id,
                        matched_application_id=dedup_result.matches[0].matched_application_id,
                        confidence_score=dedup_result.matches[0].confidence_score,
                        webhook_url=webhook_url
                    )
            
            return {
                "status": "success",
                "application_id": application_id,
                "identity_id": identity_id,
                "is_duplicate": dedup_result.is_duplicate,
                "final_status": final_status.value,
                "requires_manual_review": dedup_result.requires_manual_review
            }
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"[{application_id}] Unexpected error during processing: {str(e)}", exc_info=True)
            
            await self._handle_failure(
                app_repo, application_id, str(e), db
            )
            
            return {
                "status": "failed",
                "error_message": str(e)
            }
    
    async def _create_new_identity(
        self,
        app_repo: ApplicationRepository,
        identity_repo: IdentityRepository,
        embedding_repo: EmbeddingRepository,
        application_id: str,
        embedding: np.ndarray,
        db
    ) -> str:
        """Create new identity and store embedding"""
        # Create new identity
        identity_id = await identity_service.create_identity(
            db=db,
            application_id=application_id
        )
        
        # Store embedding in vector index
        vector_index_service.add_embedding(
            application_id=application_id,
            embedding=embedding
        )
        
        # Store embedding in database
        from app.models.identity import IdentityEmbedding
        embedding_doc = IdentityEmbedding(
            identity_id=identity_id,
            application_id=application_id,
            embedding=embedding.tolist(),
            created_at=datetime.utcnow()
        )
        await embedding_repo.create(embedding_doc)
        
        return identity_id
    
    async def _update_stage(
        self,
        app_repo: ApplicationRepository,
        application_id: str,
        stage: str,
        status: ApplicationStatus
    ):
        """Update application processing stage"""
        await app_repo.update_processing_metadata(
            application_id=application_id,
            metadata={
                "current_stage": stage,
                "status": status
            }
        )
    
    async def _handle_rejection(
        self,
        app_repo: ApplicationRepository,
        application_id: str,
        error_code: ErrorCode,
        error_message: str,
        db
    ):
        """Handle application rejection"""
        await app_repo.update_processing_error(
            application_id=application_id,
            status=ApplicationStatus.REJECTED,
            error_code=error_code.value,
            error_message=error_message
        )
        
        # Log rejection to audit trail
        await audit_service.log_application_rejection(
            db=db,
            application_id=application_id,
            error_code=error_code.value,
            error_message=error_message
        )
        
        logger.warning(f"[{application_id}] Application rejected: {error_code.value} - {error_message}")
    
    async def _handle_failure(
        self,
        app_repo: ApplicationRepository,
        application_id: str,
        error_message: str,
        db
    ):
        """Handle processing failure"""
        await app_repo.update_processing_error(
            application_id=application_id,
            status=ApplicationStatus.FAILED,
            error_code="E999",
            error_message=f"Processing failed: {error_message}"
        )
        
        # Log failure to audit trail
        await audit_service.log_application_failure(
            db=db,
            application_id=application_id,
            error_message=error_message
        )
    
    async def process_from_queue(self):
        """Process applications from queue with retry logic"""
        while self.is_running:
            try:
                # Get next application from queue
                application_data = await queue_service.dequeue_application()
                
                if application_data:
                    application_id = application_data.get("application_id")
                    photograph_base64 = application_data.get("photograph_base64")
                    photograph_format = application_data.get("photograph_format")
                    retry_count = application_data.get("retry_count", 0)
                    
                    # Get database connection
                    from app.database.mongodb import get_database
                    db = await get_database()
                    
                    # Process application
                    result = await self.process_application_end_to_end(
                        application_id=application_id,
                        photograph_base64=photograph_base64,
                        photograph_format=photograph_format,
                        db=db
                    )
                    
                    if result["status"] == "success" or result["status"] == "rejected":
                        # Mark as completed
                        await queue_service.mark_completed(application_id, success=True)
                    else:
                        # Failed - check if we should retry
                        if retry_count < self.max_retries:
                            logger.info(f"Retrying application {application_id}. Attempt {retry_count + 1}/{self.max_retries}")
                            await queue_service.requeue_application(application_id, max_retries=self.max_retries)
                        else:
                            logger.error(f"All retries exhausted for application {application_id}")
                            await queue_service.mark_completed(application_id, success=False)
                else:
                    # Queue is empty
                    await asyncio.sleep(self.processing_delay)
                    
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}", exc_info=True)
                await asyncio.sleep(1)
    
    async def start(self):
        """Start the application processor"""
        if self.is_running:
            logger.warning("Application processor is already running")
            return
        
        self.is_running = True
        logger.info("Application processor started")
        
        # Start processing loop
        asyncio.create_task(self.process_from_queue())
    
    async def stop(self):
        """Stop the application processor"""
        logger.info("Stopping application processor...")
        self.is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status"""
        return {
            "is_running": self.is_running,
            "max_retries": self.max_retries
        }


# Global application processor instance
application_processor = ApplicationProcessor()

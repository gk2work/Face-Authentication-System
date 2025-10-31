"""Health check service for monitoring system components"""

from typing import Dict, Any
from pathlib import Path
import os

from app.core.logging import logger
from app.core.config import settings


class HealthCheckService:
    """Service for checking health of system components"""
    
    def __init__(self):
        """Initialize health check service"""
        logger.info("Health check service initialized")
    
    async def check_database(self, mongodb_manager) -> Dict[str, Any]:
        """
        Check MongoDB database health
        
        Args:
            mongodb_manager: MongoDB manager instance
            
        Returns:
            Dictionary with status and details
        """
        try:
            is_healthy = await mongodb_manager.health_check()
            
            return {
                "status": "ok" if is_healthy else "failed",
                "message": "Database connection healthy" if is_healthy else "Database connection failed",
                "type": "mongodb"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "failed",
                "message": f"Database check error: {str(e)}",
                "type": "mongodb"
            }
    
    def check_storage(self) -> Dict[str, Any]:
        """
        Check storage directories health
        
        Returns:
            Dictionary with status and details
        """
        try:
            storage_path = Path(settings.STORAGE_PATH)
            vector_path = Path(settings.VECTOR_DB_PATH)
            
            # Check if directories exist and are writable
            storage_exists = storage_path.exists()
            storage_writable = os.access(storage_path, os.W_OK) if storage_exists else False
            
            vector_exists = vector_path.exists()
            vector_writable = os.access(vector_path, os.W_OK) if vector_exists else False
            
            all_ok = storage_exists and storage_writable and vector_exists and vector_writable
            
            return {
                "status": "ok" if all_ok else "degraded",
                "message": "Storage accessible" if all_ok else "Storage issues detected",
                "details": {
                    "photographs_storage": {
                        "exists": storage_exists,
                        "writable": storage_writable,
                        "path": str(storage_path)
                    },
                    "vector_storage": {
                        "exists": vector_exists,
                        "writable": vector_writable,
                        "path": str(vector_path)
                    }
                }
            }
        except Exception as e:
            logger.error(f"Storage health check failed: {str(e)}")
            return {
                "status": "failed",
                "message": f"Storage check error: {str(e)}"
            }
    
    def check_vector_index(self) -> Dict[str, Any]:
        """
        Check FAISS vector index health
        
        Returns:
            Dictionary with status and details
        """
        try:
            from app.services.vector_index_service import vector_index_service
            
            stats = vector_index_service.get_stats()
            
            return {
                "status": "ok",
                "message": "Vector index operational",
                "details": {
                    "total_vectors": stats.get("total_vectors", 0),
                    "index_type": stats.get("index_type", "unknown")
                }
            }
        except Exception as e:
            logger.error(f"Vector index health check failed: {str(e)}")
            return {
                "status": "degraded",
                "message": f"Vector index check error: {str(e)}"
            }
    
    def check_face_recognition_model(self) -> Dict[str, Any]:
        """
        Check face recognition model health
        
        Returns:
            Dictionary with status and details
        """
        try:
            from app.services.face_recognition_service import face_recognition_service
            
            # Check if models are loaded
            has_mtcnn = face_recognition_service.mtcnn is not None
            has_embedding_model = face_recognition_service.embedding_model is not None
            
            all_ok = has_mtcnn and has_embedding_model
            
            return {
                "status": "ok" if all_ok else "failed",
                "message": "Face recognition models loaded" if all_ok else "Models not loaded",
                "details": {
                    "mtcnn_loaded": has_mtcnn,
                    "embedding_model_loaded": has_embedding_model,
                    "device": str(face_recognition_service.device)
                }
            }
        except Exception as e:
            logger.error(f"Face recognition model health check failed: {str(e)}")
            return {
                "status": "failed",
                "message": f"Model check error: {str(e)}"
            }
    
    def check_metrics_service(self) -> Dict[str, Any]:
        """
        Check metrics service health
        
        Returns:
            Dictionary with status and details
        """
        try:
            from app.services.metrics_service import metrics_service
            
            uptime = metrics_service.get_uptime_seconds()
            
            return {
                "status": "ok",
                "message": "Metrics service operational",
                "details": {
                    "uptime_seconds": round(uptime, 2)
                }
            }
        except Exception as e:
            logger.error(f"Metrics service health check failed: {str(e)}")
            return {
                "status": "degraded",
                "message": f"Metrics check error: {str(e)}"
            }
    
    async def get_comprehensive_health(self, mongodb_manager) -> Dict[str, Any]:
        """
        Get comprehensive health check of all components
        
        Args:
            mongodb_manager: MongoDB manager instance
            
        Returns:
            Dictionary with overall status and component checks
        """
        checks = {
            "database": await self.check_database(mongodb_manager),
            "storage": self.check_storage(),
            "vector_index": self.check_vector_index(),
            "face_recognition": self.check_face_recognition_model(),
            "metrics": self.check_metrics_service()
        }
        
        # Determine overall status
        statuses = [check["status"] for check in checks.values()]
        
        if all(s == "ok" for s in statuses):
            overall_status = "healthy"
        elif any(s == "failed" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "checks": checks,
            "timestamp": None  # Will be set by endpoint
        }


# Global health check service instance
health_check_service = HealthCheckService()

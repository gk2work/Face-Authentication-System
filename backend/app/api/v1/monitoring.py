"""Monitoring and metrics API endpoints"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.services.metrics_service import metrics_service
from app.services.alerting_service import alerting_service
from app.api.dependencies import require_admin_or_reviewer
from app.models.user import User
from app.core.logging import logger

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    current_user: User = Depends(require_admin_or_reviewer)
) -> Dict[str, Any]:
    """
    Get current system metrics
    
    Returns comprehensive metrics including:
    - Uptime
    - Event counters
    - Latency statistics
    - Processing rates
    - Error rates
    """
    try:
        metrics = metrics_service.get_all_metrics()
        logger.info(f"Metrics retrieved by {current_user.username}")
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        return {
            "error": "Failed to retrieve metrics",
            "message": str(e)
        }


@router.post("/metrics/reset")
async def reset_metrics(
    current_user: User = Depends(require_admin_or_reviewer)
) -> Dict[str, str]:
    """
    Reset all metrics (admin only)
    
    Useful for testing or after maintenance
    """
    try:
        metrics_service.reset_metrics()
        logger.info(f"Metrics reset by {current_user.username}")
        return {
            "status": "success",
            "message": "Metrics reset successfully"
        }
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/alerts/check")
async def check_alerts(
    current_user: User = Depends(require_admin_or_reviewer)
) -> Dict[str, str]:
    """
    Manually trigger alert checks
    
    Checks all metrics against thresholds and sends alerts if needed
    """
    try:
        alerting_service.check_all_metrics()
        logger.info(f"Alert check triggered by {current_user.username}")
        return {
            "status": "success",
            "message": "Alert checks completed"
        }
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get system status summary (public endpoint)
    
    Returns basic system health information
    """
    try:
        metrics = metrics_service.get_all_metrics()
        
        # Determine overall status
        error_rate = metrics.get('error_rate_percent', 0)
        status = "healthy"
        
        if error_rate > 5:
            status = "degraded"
        elif error_rate > 10:
            status = "unhealthy"
        
        return {
            "status": status,
            "uptime_seconds": metrics.get('uptime_seconds', 0),
            "total_events": sum(metrics.get('counters', {}).values()),
            "error_rate_percent": error_rate,
            "processing_rates": metrics.get('processing_rates', {})
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

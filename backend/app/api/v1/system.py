"""System status and error handling API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime

from app.core.logging import logger
from app.api.dependencies import require_admin
from app.models.user import User
from app.utils.resilience import get_resilience_status
from app.utils.retry import dead_letter_queue
from app.utils.circuit_breaker import circuit_breaker_registry
from app.database.mongodb import mongodb_manager

router = APIRouter(prefix="/system", tags=["system"])

# Create a separate router for health endpoint without prefix
health_router = APIRouter(tags=["system"])


@health_router.get("/health")
async def health_check_v1() -> Dict[str, Any]:
    """
    Health check endpoint at /api/v1/health
    
    Returns basic health status for the API
    """
    try:
        # Quick database check
        db_healthy = await mongodb_manager.health_check()
        
        if db_healthy:
            return {
                "status": "healthy",
                "service": "face-auth-system",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "unhealthy",
                "service": "face-auth-system",
                "message": "Database connection failed",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "face-auth-system",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/resilience", response_model=Dict[str, Any])
async def get_resilience_info(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get resilience status including circuit breakers and dead letter queue
    
    Requires admin authentication
    """
    try:
        return get_resilience_status()
    except Exception as e:
        logger.error(f"Error retrieving resilience status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resilience status"
        )


@router.get("/circuit-breakers", response_model=Dict[str, Any])
async def get_circuit_breakers(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get status of all circuit breakers
    
    Requires admin authentication
    """
    try:
        return circuit_breaker_registry.get_all_states()
    except Exception as e:
        logger.error(f"Error retrieving circuit breaker status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve circuit breaker status"
        )


@router.post("/circuit-breakers/reset", response_model=Dict[str, str])
async def reset_circuit_breakers(
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Reset all circuit breakers to closed state
    
    Requires admin authentication
    """
    try:
        circuit_breaker_registry.reset_all()
        logger.info(f"Circuit breakers reset by admin: {current_user.username}")
        return {"message": "All circuit breakers reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting circuit breakers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset circuit breakers"
        )


@router.get("/dead-letter-queue", response_model=Dict[str, Any])
async def get_dead_letter_queue_status(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get dead letter queue statistics
    
    Requires admin authentication
    """
    try:
        return dead_letter_queue.get_statistics()
    except Exception as e:
        logger.error(f"Error retrieving dead letter queue status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dead letter queue status"
        )


@router.get("/dead-letter-queue/items")
async def get_dead_letter_queue_items(
    current_user: User = Depends(require_admin)
):
    """
    Get all items in dead letter queue
    
    Requires admin authentication
    """
    try:
        return {"items": dead_letter_queue.get_all()}
    except Exception as e:
        logger.error(f"Error retrieving dead letter queue items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dead letter queue items"
        )


@router.delete("/dead-letter-queue", response_model=Dict[str, str])
async def clear_dead_letter_queue(
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Clear all items from dead letter queue
    
    Requires admin authentication
    """
    try:
        count = dead_letter_queue.get_count()
        dead_letter_queue.clear()
        logger.info(f"Dead letter queue cleared by admin: {current_user.username} ({count} items)")
        return {"message": f"Dead letter queue cleared successfully ({count} items removed)"}
    except Exception as e:
        logger.error(f"Error clearing dead letter queue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear dead letter queue"
        )


@router.delete("/dead-letter-queue/{index}", response_model=Dict[str, Any])
async def remove_dead_letter_item(
    index: int,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Remove specific item from dead letter queue
    
    Requires admin authentication
    """
    try:
        item = dead_letter_queue.remove(index)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item at index {index} not found"
            )
        
        logger.info(f"Dead letter queue item {index} removed by admin: {current_user.username}")
        return {"message": "Item removed successfully", "item": item}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing dead letter queue item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove dead letter queue item"
        )

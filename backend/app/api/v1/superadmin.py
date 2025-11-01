"""Superadmin API endpoints for managing admin users"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime

from app.models.user import (
    User, UserCreate, AdminUserResponse, AdminUserStatsResponse,
    AggregateStatsResponse, PaginatedAdminUsersResponse
)
from app.api.dependencies import require_superadmin, get_current_user
from app.database.mongodb import get_database
from app.services.superadmin_service import SuperadminService
from app.core.logging import logger

router = APIRouter(prefix="/superadmin", tags=["Superadmin"])


@router.get("/users", response_model=PaginatedAdminUsersResponse)
async def list_admin_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by username, email, or full name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date (after)"),
    created_before: Optional[datetime] = Query(None, description="Filter by creation date (before)"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(require_superadmin),
    db=Depends(get_database)
):
    """
    List all admin users with pagination, search, and filtering
    
    Requires superadmin role.
    """
    try:
        service = SuperadminService(db)
        users, total = await service.get_admin_users(
            page=page,
            page_size=page_size,
            search=search,
            role=role,
            is_active=is_active,
            created_after=created_after,
            created_before=created_before,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        # Convert to response models
        user_responses = [AdminUserResponse(**user) for user in users]
        
        return PaginatedAdminUsersResponse(
            users=user_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Failed to list admin users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admin users: {str(e)}"
        )



@router.get("/users/{username}", response_model=AdminUserResponse)
async def get_admin_user(
    username: str,
    current_user: User = Depends(require_superadmin),
    db=Depends(get_database)
):
    """
    Get detailed information about a specific admin user
    
    Requires superadmin role.
    """
    try:
        service = SuperadminService(db)
        users, _ = await service.get_admin_users(
            page=1,
            page_size=1,
            search=username
        )
        
        if not users or users[0]["username"] != username:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        
        return AdminUserResponse(**users[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get admin user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admin user: {str(e)}"
        )



@router.get("/users/{username}/stats", response_model=AdminUserStatsResponse)
async def get_admin_user_stats(
    username: str,
    current_user: User = Depends(require_superadmin),
    db=Depends(get_database)
):
    """
    Get statistics for a specific admin user
    
    Includes:
    - Total applications processed
    - Applications by status breakdown
    - Override decisions
    - 30-day activity timeline
    
    Requires superadmin role.
    """
    try:
        service = SuperadminService(db)
        stats = await service.get_admin_user_stats(username)
        
        return AdminUserStatsResponse(**stats)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get admin user stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admin user statistics: {str(e)}"
        )



@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    user_data: UserCreate,
    current_user: User = Depends(require_superadmin),
    db=Depends(get_database)
):
    """
    Create a new admin user
    
    Validates:
    - Username uniqueness (3-50 characters)
    - Email format
    - Password strength (minimum 8 characters)
    - Full name (1-200 characters)
    
    Logs creation event to audit log.
    
    Requires superadmin role.
    """
    try:
        service = SuperadminService(db)
        user = await service.create_admin_user(user_data, current_user.username)
        
        # Get user with application count
        users, _ = await service.get_admin_users(
            page=1,
            page_size=1,
            search=user.username
        )
        
        if users:
            return AdminUserResponse(**users[0])
        
        # Fallback if aggregation fails
        return AdminUserResponse(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            application_count=0
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create admin user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin user: {str(e)}"
        )



from pydantic import BaseModel, EmailStr
from typing import List


class UserUpdateRequest(BaseModel):
    """Request model for updating admin user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


@router.put("/users/{username}", response_model=AdminUserResponse)
async def update_admin_user(
    username: str,
    update_data: UserUpdateRequest,
    current_user: User = Depends(require_superadmin),
    db=Depends(get_database)
):
    """
    Update an existing admin user
    
    Prevents:
    - Self-modification of active status
    
    Logs modification event with changed fields to audit log.
    
    Requires superadmin role.
    """
    try:
        # Convert to dict and remove None values
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        service = SuperadminService(db)
        user = await service.update_admin_user(username, update_dict, current_user.username)
        
        # Get user with application count
        users, _ = await service.get_admin_users(
            page=1,
            page_size=1,
            search=username
        )
        
        if users:
            return AdminUserResponse(**users[0])
        
        # Fallback if aggregation fails
        return AdminUserResponse(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            application_count=0
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update admin user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update admin user: {str(e)}"
        )



class DeactivateResponse(BaseModel):
    """Response model for user deactivation"""
    success: bool
    message: str


@router.delete("/users/{username}", response_model=DeactivateResponse)
async def deactivate_admin_user(
    username: str,
    current_user: User = Depends(require_superadmin),
    db=Depends(get_database)
):
    """
    Deactivate an admin user
    
    Prevents:
    - Self-deactivation
    
    Logs deactivation event to audit log.
    
    Requires superadmin role.
    """
    try:
        service = SuperadminService(db)
        success = await service.deactivate_admin_user(username, current_user.username)
        
        return DeactivateResponse(
            success=success,
            message=f"User {username} deactivated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to deactivate admin user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate admin user: {str(e)}"
        )



@router.get("/stats", response_model=AggregateStatsResponse)
async def get_aggregate_stats(
    current_user: User = Depends(require_superadmin),
    db=Depends(get_database)
):
    """
    Get aggregate statistics for all admin users
    
    Includes:
    - Total active/inactive users
    - Users by role breakdown
    - Total applications in last 30 days
    - Most active users (top 5)
    
    Requires superadmin role.
    """
    try:
        service = SuperadminService(db)
        stats = await service.get_aggregate_stats()
        
        return AggregateStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get aggregate stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve aggregate statistics: {str(e)}"
        )

"""User management API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime

from app.models.user import User, UserCreate, UserResponse, UserRole
from app.database.mongodb import get_database
from app.database.repositories import UserRepository
from app.api.dependencies import require_admin
from app.services.auth_service import auth_service
from app.core.logging import logger

router = APIRouter(prefix="/users", tags=["users"])


class UserUpdateRequest(BaseModel):
    """Request model for updating user"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    roles: Optional[List[UserRole]] = None
    is_active: Optional[bool] = None


from pydantic import BaseModel


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_admin),
    db=Depends(get_database)
) -> List[UserResponse]:
    """
    List all users (admin only)
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    
    Returns list of users
    """
    try:
        user_repo = UserRepository(db)
        
        # Get all users
        users = await user_repo.list_all(skip=skip, limit=limit, is_active=is_active)
        
        # Convert to response models
        user_responses = [
            UserResponse(
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                roles=user.roles,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login
            )
            for user in users
        ]
        
        logger.info(f"Listed {len(user_responses)} users by {current_user.username}")
        
        return user_responses
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: User = Depends(require_admin),
    db=Depends(get_database)
) -> UserResponse:
    """
    Get user by username (admin only)
    
    - **username**: Username to retrieve
    
    Returns user information
    """
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_username(username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        
        logger.info(f"User {username} retrieved by {current_user.username}")
        
        return UserResponse(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db=Depends(get_database)
) -> UserResponse:
    """
    Create a new user (admin only)
    
    - **username**: Unique username
    - **email**: User's email address
    - **password**: User's password (min 8 characters)
    - **full_name**: User's full name
    - **roles**: List of user roles
    
    Returns created user information
    """
    try:
        user_repo = UserRepository(db)
        
        # Check if username already exists
        existing_user = await user_repo.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Hash password
        hashed_password = auth_service.get_password_hash(user_data.password)
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            roles=user_data.roles,
            is_active=True
        )
        
        await user_repo.create(user)
        
        logger.info(f"User {user.username} created by {current_user.username}")
        
        return UserResponse(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.put("/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    update_data: UserUpdateRequest,
    current_user: User = Depends(require_admin),
    db=Depends(get_database)
) -> UserResponse:
    """
    Update user information (admin only)
    
    - **username**: Username to update
    - **email**: New email address (optional)
    - **full_name**: New full name (optional)
    - **roles**: New roles list (optional)
    - **is_active**: New active status (optional)
    
    Returns updated user information
    """
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_username(username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        
        # Update fields
        update_dict = {}
        if update_data.email is not None:
            update_dict["email"] = update_data.email
        if update_data.full_name is not None:
            update_dict["full_name"] = update_data.full_name
        if update_data.roles is not None:
            update_dict["roles"] = update_data.roles
        if update_data.is_active is not None:
            update_dict["is_active"] = update_data.is_active
        
        update_dict["updated_at"] = datetime.utcnow()
        
        # Update user
        await user_repo.update(username, update_dict)
        
        # Get updated user
        updated_user = await user_repo.get_by_username(username)
        
        logger.info(f"User {username} updated by {current_user.username}")
        
        return UserResponse(
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            roles=updated_user.roles,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{username}")
async def deactivate_user(
    username: str,
    current_user: User = Depends(require_admin),
    db=Depends(get_database)
) -> dict:
    """
    Deactivate a user (admin only)
    
    - **username**: Username to deactivate
    
    Returns success message
    """
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_username(username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        
        # Prevent deactivating yourself
        if username == current_user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        # Deactivate user
        await user_repo.update(username, {
            "is_active": False,
            "updated_at": datetime.utcnow()
        })
        
        logger.info(f"User {username} deactivated by {current_user.username}")
        
        return {
            "success": True,
            "message": f"User {username} deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )

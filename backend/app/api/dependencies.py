"""FastAPI dependencies for authentication and authorization"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

from app.models.user import User, UserRole, TokenData
from app.services.auth_service import auth_service
from app.database.mongodb import get_database
from app.database.repositories import UserRepository
from app.core.logging import logger

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_database)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database connection
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        token_data = auth_service.decode_access_token(credentials.credentials)
        
        if token_data is None or token_data.username is None:
            raise credentials_exception
        
        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_username(token_data.username)
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_roles(required_roles: List[UserRole]):
    """
    Dependency factory to check if user has required roles
    
    Args:
        required_roles: List of roles required to access the endpoint
        
    Returns:
        Dependency function that validates user roles
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if current user has any of the required roles
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            User if authorized
            
        Raises:
            HTTPException: If user doesn't have required roles
        """
        user_roles = set(current_user.roles)
        required_roles_set = set(required_roles)
        
        if not user_roles.intersection(required_roles_set):
            logger.warning(
                f"User {current_user.username} attempted to access endpoint requiring roles "
                f"{[r.value for r in required_roles]} but has roles {[r.value for r in current_user.roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker


# Common role dependencies
require_admin = require_roles([UserRole.ADMIN])
require_admin_or_reviewer = require_roles([UserRole.ADMIN, UserRole.REVIEWER])
require_auditor = require_roles([UserRole.ADMIN, UserRole.AUDITOR])
require_superadmin = require_roles([UserRole.SUPERADMIN])

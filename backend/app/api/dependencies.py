"""FastAPI dependencies for authentication and authorization"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Set, Dict

from app.models.user import User, UserRole, TokenData
from app.services.auth_service import auth_service
from app.database.mongodb import get_database
from app.database.repositories import UserRepository
from app.core.logging import logger

security = HTTPBearer()


# Role Hierarchy Definition
# =========================
# This hierarchy defines which roles inherit permissions from other roles.
# Higher-level roles automatically gain access to all endpoints that lower-level roles can access.
#
# Hierarchy Structure:
#   superadmin (Level 5) - Highest privilege, can access everything
#       ↓ inherits all below
#   admin (Level 4) - Administrative access
#       ↓ inherits all below
#   reviewer/auditor (Level 3) - Parallel roles at same level
#       ↓ inherits all below
#   operator (Level 2) - Base role with standard access
#
# Each role maps to a set of roles it can access (including itself).
ROLE_HIERARCHY: Dict[UserRole, Set[UserRole]] = {
    UserRole.SUPERADMIN: {
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.REVIEWER,
        UserRole.AUDITOR,
        UserRole.OPERATOR
    },
    UserRole.ADMIN: {
        UserRole.ADMIN,
        UserRole.REVIEWER,
        UserRole.AUDITOR,
        UserRole.OPERATOR
    },
    UserRole.REVIEWER: {
        UserRole.REVIEWER,
        UserRole.OPERATOR
    },
    UserRole.AUDITOR: {
        UserRole.AUDITOR,
        UserRole.OPERATOR
    },
    UserRole.OPERATOR: {
        UserRole.OPERATOR
    }
}


def get_effective_roles(user_roles: List[UserRole]) -> Set[UserRole]:
    """
    Calculate all effective roles for a user including inherited roles.
    
    This function implements role hierarchy by expanding a user's assigned roles
    to include all roles they inherit permissions from. For example, a user with
    the 'admin' role will have effective roles of: admin, reviewer, auditor, and operator.
    
    The role hierarchy is defined in ROLE_HIERARCHY constant:
    - superadmin: Has access to all roles (superadmin, admin, reviewer, auditor, operator)
    - admin: Has access to admin, reviewer, auditor, and operator roles
    - reviewer: Has access to reviewer and operator roles
    - auditor: Has access to auditor and operator roles
    - operator: Has access to operator role only (base role)
    
    Args:
        user_roles: List of roles directly assigned to the user
        
    Returns:
        Set of all roles the user has access to, including both assigned roles
        and inherited roles based on the hierarchy
        
    Examples:
        >>> get_effective_roles([UserRole.SUPERADMIN])
        {UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.REVIEWER, UserRole.AUDITOR, UserRole.OPERATOR}
        
        >>> get_effective_roles([UserRole.ADMIN])
        {UserRole.ADMIN, UserRole.REVIEWER, UserRole.AUDITOR, UserRole.OPERATOR}
        
        >>> get_effective_roles([UserRole.REVIEWER, UserRole.AUDITOR])
        {UserRole.REVIEWER, UserRole.AUDITOR, UserRole.OPERATOR}
        
        >>> get_effective_roles([UserRole.OPERATOR])
        {UserRole.OPERATOR}
        
        >>> get_effective_roles([])
        set()
    """
    effective_roles = set()
    
    for role in user_roles:
        # Get all roles this role has access to from the hierarchy
        # If role is not in hierarchy, just add the role itself
        effective_roles.update(ROLE_HIERARCHY.get(role, {role}))
    
    return effective_roles


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
        Check if current user has any of the required roles (including inherited roles)
        
        This function implements role hierarchy by expanding the user's assigned roles
        to include inherited roles before checking against required roles.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            User if authorized
            
        Raises:
            HTTPException: If user doesn't have required roles (directly or through inheritance)
        """
        # Get effective roles including inherited roles from hierarchy
        effective_roles = get_effective_roles(current_user.roles)
        required_roles_set = set(required_roles)
        
        # Check if any effective role matches required roles
        if not effective_roles.intersection(required_roles_set):
            # Access denied - log with full details
            logger.warning(
                f"Authorization DENIED for user '{current_user.username}' | "
                f"Required roles: {[r.value for r in required_roles]} | "
                f"Assigned roles: {[r.value for r in current_user.roles]} | "
                f"Effective roles (with hierarchy): {sorted([r.value for r in effective_roles])}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Access granted - determine if it was through direct role or inheritance
        assigned_roles_set = set(current_user.roles)
        direct_match = bool(assigned_roles_set.intersection(required_roles_set))
        
        if direct_match:
            # Access granted through directly assigned role
            logger.debug(
                f"Authorization GRANTED for user '{current_user.username}' | "
                f"Required roles: {[r.value for r in required_roles]} | "
                f"Matched via direct role assignment"
            )
        else:
            # Access granted through role inheritance
            inherited_roles = effective_roles - assigned_roles_set
            matching_inherited = inherited_roles.intersection(required_roles_set)
            logger.info(
                f"Authorization GRANTED for user '{current_user.username}' via ROLE INHERITANCE | "
                f"Required roles: {[r.value for r in required_roles]} | "
                f"Assigned roles: {[r.value for r in current_user.roles]} | "
                f"Granted through inherited roles: {sorted([r.value for r in matching_inherited])}"
            )
        
        return current_user
    
    return role_checker


# Common role dependencies
require_admin = require_roles([UserRole.ADMIN])
require_admin_or_reviewer = require_roles([UserRole.ADMIN, UserRole.REVIEWER])
require_auditor = require_roles([UserRole.ADMIN, UserRole.AUDITOR])
require_superadmin = require_roles([UserRole.SUPERADMIN])

"""Authentication API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.user import UserLogin, Token, UserCreate, UserResponse, User
from app.services.auth_service import auth_service
from app.database.mongodb import get_database
from app.database.repositories import UserRepository
from app.core.logging import logger
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db=Depends(get_database)
) -> Token:
    """
    Authenticate user and return JWT access token
    
    - **username**: User's username
    - **password**: User's password
    
    Returns JWT access token
    """
    try:
        user_repo = UserRepository(db)
        
        # Get user from database
        user = await user_repo.get_by_username(credentials.username)
        
        # Authenticate user
        if not auth_service.authenticate_user(user, credentials.password):
            logger.warning(f"Failed login attempt for username: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={
                "sub": user.username,
                "roles": [role.value for role in user.roles]
            },
            expires_delta=access_token_expires
        )
        
        # Update last login
        await user_repo.update_last_login(user.username)
        
        logger.info(f"User logged in successfully: {user.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db=Depends(get_database)
) -> UserResponse:
    """
    Register a new user (admin only in production)
    
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
                detail="Username already registered"
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
        
        logger.info(f"New user registered: {user.username}")
        
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_database)
) -> UserResponse:
    """
    Get current authenticated user information
    
    Returns current user details
    """
    try:
        # Decode token
        token_data = auth_service.decode_access_token(credentials.credentials)
        
        if token_data is None or token_data.username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_username(token_data.username)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
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
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

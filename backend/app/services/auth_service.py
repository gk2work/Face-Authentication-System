"""Authentication service for JWT token management and password hashing"""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.models.user import User, TokenData, UserRole
from app.core.logging import logger


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            # Convert strings to bytes
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a plain password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        # Convert password to bytes and hash
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Return as string for storage
        return hashed.decode('utf-8')
    
    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> Optional[TokenData]:
        """
        Decode and validate a JWT access token
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            username: str = payload.get("sub")
            roles: list = payload.get("roles", [])
            
            if username is None:
                return None
            
            # Convert role strings to UserRole enums
            user_roles = [UserRole(role) for role in roles if role in [r.value for r in UserRole]]
            
            return TokenData(username=username, roles=user_roles)
            
        except JWTError as e:
            logger.warning(f"JWT decode error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error decoding token: {str(e)}")
            return None
    
    def authenticate_user(
        self,
        user: Optional[User],
        password: str
    ) -> bool:
        """
        Authenticate a user with password
        
        Args:
            user: User object from database
            password: Plain text password to verify
            
        Returns:
            True if authentication successful, False otherwise
        """
        if not user:
            return False
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {user.username}")
            return False
        
        if not self.verify_password(password, user.hashed_password):
            return False
        
        return True


# Global auth service instance
auth_service = AuthService()

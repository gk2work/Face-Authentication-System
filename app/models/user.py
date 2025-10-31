"""User and authentication data models"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles for access control"""
    ADMIN = "admin"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"
    OPERATOR = "operator"


class User(BaseModel):
    """User document model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    hashed_password: str
    full_name: str = Field(..., min_length=1, max_length=200)
    roles: List[UserRole] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "System Administrator",
                "roles": ["admin"]
            }
        }


class UserCreate(BaseModel):
    """Model for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=200)
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.OPERATOR])


class UserLogin(BaseModel):
    """Model for user login"""
    username: str
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    roles: List[UserRole] = Field(default_factory=list)


class UserResponse(BaseModel):
    """Response model for user queries"""
    username: str
    email: EmailStr
    full_name: str
    roles: List[UserRole]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

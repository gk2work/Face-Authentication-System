"""User and authentication data models"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles for access control"""
    SUPERADMIN = "superadmin"
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


class AdminUserResponse(BaseModel):
    """Response model for admin user in superadmin context"""
    username: str
    email: EmailStr
    full_name: str
    roles: List[UserRole]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    application_count: int = 0


class AdminUserStatsResponse(BaseModel):
    """Response model for admin user statistics"""
    username: str
    total_applications: int
    applications_by_status: Dict[str, int]
    total_overrides: int
    overrides_by_decision: Dict[str, int]
    activity_timeline: List[Dict[str, Any]]
    last_30_days_total: int


class AggregateStatsResponse(BaseModel):
    """Response model for aggregate admin statistics"""
    total_admin_users: int
    active_admin_users: int
    inactive_admin_users: int
    users_by_role: Dict[str, int]
    total_applications_last_30_days: int
    most_active_users: List[Dict[str, Any]]


class PaginatedAdminUsersResponse(BaseModel):
    """Paginated response for admin users"""
    users: List[AdminUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

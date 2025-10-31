"""Audit log data models"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Audit event types"""
    APPLICATION_SUBMITTED = "application_submitted"
    FACE_DETECTED = "face_detected"
    EMBEDDING_GENERATED = "embedding_generated"
    DUPLICATE_DETECTED = "duplicate_detected"
    IDENTITY_ISSUED = "identity_issued"
    APPLICATION_REJECTED = "application_rejected"
    MANUAL_OVERRIDE = "manual_override"
    IDENTITY_MERGED = "identity_merged"
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGOUT = "admin_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"


class ActorType(str, Enum):
    """Actor type for audit events"""
    SYSTEM = "system"
    ADMIN = "admin"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"
    API = "api"


class ResourceType(str, Enum):
    """Resource type for audit events"""
    APPLICATION = "application"
    IDENTITY = "identity"
    EMBEDDING = "embedding"
    USER = "user"
    SYSTEM = "system"


class AuditLog(BaseModel):
    """Audit log document model"""
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor_id: str = Field(..., description="ID of the actor performing the action")
    actor_type: ActorType
    resource_id: Optional[str] = Field(None, description="ID of the affected resource")
    resource_type: Optional[ResourceType] = None
    action: str = Field(..., description="Description of the action performed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "application_submitted",
                "actor_id": "system",
                "actor_type": "system",
                "resource_id": "app-123",
                "resource_type": "application",
                "action": "New application submitted",
                "details": {
                    "applicant_email": "john.doe@example.com"
                },
                "ip_address": "192.168.1.1"
            }
        }


class AuditLogQuery(BaseModel):
    """Query parameters for audit log search"""
    event_type: Optional[EventType] = None
    actor_id: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    skip: int = Field(default=0, ge=0)


class AuditLogResponse(BaseModel):
    """Response model for audit log queries"""
    total: int
    logs: list[AuditLog]
    page: int
    page_size: int

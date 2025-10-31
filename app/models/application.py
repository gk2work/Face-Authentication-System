"""Application data models"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    """Application processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    VERIFIED = "verified"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    FAILED = "failed"


class ApplicantData(BaseModel):
    """Applicant demographic information"""
    name: str = Field(..., min_length=1, max_length=200)
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    address: Optional[str] = None
    demographic_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PhotographMetadata(BaseModel):
    """Photograph metadata"""
    url: Optional[str] = None
    path: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    format: str = Field(..., pattern=r"^(jpg|jpeg|png)$")
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    file_size: int = Field(..., gt=0, description="File size in bytes")


class ProcessingMetadata(BaseModel):
    """Application processing metadata"""
    status: ApplicationStatus = ApplicationStatus.PENDING
    face_detected: bool = False
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    embedding_generated: bool = False
    duplicate_check_completed: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None


class MatchResult(BaseModel):
    """Duplicate match result"""
    matched_application_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    matched_identity_id: Optional[str] = None


class ApplicationResult(BaseModel):
    """Final application processing result"""
    identity_id: Optional[str] = None
    is_duplicate: bool = False
    matched_applications: List[MatchResult] = Field(default_factory=list)
    final_status: ApplicationStatus = ApplicationStatus.PENDING
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class Application(BaseModel):
    """Complete application document model"""
    application_id: str = Field(..., description="Unique application identifier")
    applicant_data: ApplicantData
    photograph: PhotographMetadata
    processing: ProcessingMetadata = Field(default_factory=ProcessingMetadata)
    result: ApplicationResult = Field(default_factory=ApplicationResult)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "application_id": "550e8400-e29b-41d4-a716-446655440000",
                "applicant_data": {
                    "name": "John Doe",
                    "date_of_birth": "1990-01-01",
                    "email": "john.doe@example.com",
                    "phone": "+919876543210"
                },
                "photograph": {
                    "path": "./storage/photographs/550e8400-e29b-41d4-a716-446655440000.jpg",
                    "format": "jpg",
                    "width": 800,
                    "height": 800,
                    "file_size": 102400
                }
            }
        }


class ApplicationCreate(BaseModel):
    """Model for creating a new application"""
    applicant_data: ApplicantData
    photograph_base64: str = Field(..., description="Base64 encoded photograph")
    photograph_format: str = Field(..., pattern=r"^(jpg|jpeg|png)$")


class ApplicationStatusResponse(BaseModel):
    """Response model for application status query"""
    application_id: str
    status: ApplicationStatus
    is_duplicate: bool = False
    identity_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

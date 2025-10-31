"""Identity data models"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class IdentityStatus(str, Enum):
    """Identity status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    MERGED = "merged"


class Identity(BaseModel):
    """Identity document model"""
    unique_id: str = Field(..., description="Unique applicant identifier (UUID)")
    status: IdentityStatus = IdentityStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    application_ids: List[str] = Field(default_factory=list, description="List of associated application IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "unique_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "active",
                "application_ids": ["app-123", "app-456"]
            }
        }


class FaceBoundingBox(BaseModel):
    """Face bounding box coordinates"""
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


class EmbeddingMetadata(BaseModel):
    """Metadata for facial embedding"""
    model_version: str = Field(..., description="Face recognition model version")
    quality_score: float = Field(..., ge=0.0, le=1.0)
    face_box: FaceBoundingBox
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IdentityEmbedding(BaseModel):
    """Identity embedding document model"""
    identity_id: str = Field(..., description="Associated identity ID")
    application_id: str = Field(..., description="Source application ID")
    embedding_vector: List[float] = Field(..., description="512-dimensional embedding vector")
    metadata: EmbeddingMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "identity_id": "550e8400-e29b-41d4-a716-446655440000",
                "application_id": "app-123",
                "embedding_vector": [0.1] * 512,
                "metadata": {
                    "model_version": "facenet-v1",
                    "quality_score": 0.95,
                    "face_box": {"x": 100, "y": 100, "width": 200, "height": 200}
                }
            }
        }


class IdentityResponse(BaseModel):
    """Response model for identity queries"""
    unique_id: str
    status: IdentityStatus
    created_at: datetime
    application_count: int = 0

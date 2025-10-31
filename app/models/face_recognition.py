"""Face recognition request and response models"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime


class BoundingBox(BaseModel):
    """Face bounding box coordinates"""
    x: int = Field(..., description="X coordinate of top-left corner")
    y: int = Field(..., description="Y coordinate of top-left corner")
    width: int = Field(..., description="Width of bounding box")
    height: int = Field(..., description="Height of bounding box")
    x2: Optional[int] = Field(None, description="X coordinate of bottom-right corner")
    y2: Optional[int] = Field(None, description="Y coordinate of bottom-right corner")


class QualityAssessment(BaseModel):
    """Face quality assessment results"""
    overall_score: float = Field(..., description="Overall quality score (0.0 to 1.0)")
    blur_score: float = Field(..., description="Blur score (higher is sharper)")
    blur_normalized: float = Field(..., description="Normalized blur score (0.0 to 1.0)")
    lighting_score: float = Field(..., description="Lighting quality score (0.0 to 1.0)")
    size_score: float = Field(..., description="Face size score (0.0 to 1.0)")


class FaceDetectionRequest(BaseModel):
    """Request model for face detection"""
    image_base64: str = Field(..., description="Base64 encoded image (JPEG or PNG)")
    image_format: str = Field(..., description="Image format (jpg, jpeg, png)")
    include_quality: bool = Field(True, description="Include quality assessment in response")
    
    @validator('image_format')
    def validate_format(cls, v):
        """Validate image format"""
        allowed_formats = ['jpg', 'jpeg', 'png']
        if v.lower() not in allowed_formats:
            raise ValueError(f"Image format must be one of: {', '.join(allowed_formats)}")
        return v.lower()
    
    @validator('image_base64')
    def validate_base64(cls, v):
        """Validate base64 string is not empty"""
        if not v or len(v) < 100:
            raise ValueError("Image data is too small or empty")
        return v


class FaceDetectionResponse(BaseModel):
    """Response model for face detection"""
    face_detected: bool = Field(..., description="Whether a face was detected")
    face_count: int = Field(..., description="Number of faces detected")
    bounding_box: Optional[BoundingBox] = Field(None, description="Face bounding box coordinates")
    confidence: Optional[float] = Field(None, description="Detection confidence score (0.0 to 1.0)")
    quality: Optional[QualityAssessment] = Field(None, description="Quality assessment results")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class FaceEmbeddingRequest(BaseModel):
    """Request model for face embedding generation"""
    image_base64: str = Field(..., description="Base64 encoded image (JPEG or PNG)")
    image_format: str = Field(..., description="Image format (jpg, jpeg, png)")
    
    @validator('image_format')
    def validate_format(cls, v):
        """Validate image format"""
        allowed_formats = ['jpg', 'jpeg', 'png']
        if v.lower() not in allowed_formats:
            raise ValueError(f"Image format must be one of: {', '.join(allowed_formats)}")
        return v.lower()
    
    @validator('image_base64')
    def validate_base64(cls, v):
        """Validate base64 string is not empty"""
        if not v or len(v) < 100:
            raise ValueError("Image data is too small or empty")
        return v


class FaceEmbeddingResponse(BaseModel):
    """Response model for face embedding generation"""
    embedding: List[float] = Field(..., description="512-dimensional face embedding vector")
    embedding_dimension: int = Field(..., description="Dimension of embedding vector")
    bounding_box: BoundingBox = Field(..., description="Face bounding box coordinates")
    quality_score: float = Field(..., description="Overall quality score (0.0 to 1.0)")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class FaceComparisonRequest(BaseModel):
    """Request model for face comparison"""
    embedding1: List[float] = Field(..., description="First face embedding vector")
    embedding2: List[float] = Field(..., description="Second face embedding vector")
    
    @validator('embedding1', 'embedding2')
    def validate_embedding(cls, v):
        """Validate embedding dimension"""
        if len(v) != 512:
            raise ValueError("Embedding must be 512-dimensional")
        return v


class FaceComparisonResponse(BaseModel):
    """Response model for face comparison"""
    similarity_score: float = Field(..., description="Similarity score (0.0 to 1.0)")
    is_match: bool = Field(..., description="Whether faces match based on threshold")
    threshold: float = Field(..., description="Threshold used for matching")
    distance: float = Field(..., description="Cosine distance between embeddings")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class FaceComparisonImageRequest(BaseModel):
    """Request model for face comparison using images"""
    image1_base64: str = Field(..., description="Base64 encoded first image")
    image1_format: str = Field(..., description="First image format (jpg, jpeg, png)")
    image2_base64: str = Field(..., description="Base64 encoded second image")
    image2_format: str = Field(..., description="Second image format (jpg, jpeg, png)")
    
    @validator('image1_format', 'image2_format')
    def validate_format(cls, v):
        """Validate image format"""
        allowed_formats = ['jpg', 'jpeg', 'png']
        if v.lower() not in allowed_formats:
            raise ValueError(f"Image format must be one of: {', '.join(allowed_formats)}")
        return v.lower()

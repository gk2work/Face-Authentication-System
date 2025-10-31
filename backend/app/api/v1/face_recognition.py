"""Face recognition API endpoints for detection, embedding, and comparison"""

from fastapi import APIRouter, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import base64
import time
from pathlib import Path
import tempfile
from typing import Optional

from app.models.face_recognition import (
    FaceDetectionRequest,
    FaceDetectionResponse,
    FaceEmbeddingRequest,
    FaceEmbeddingResponse,
    FaceComparisonRequest,
    FaceComparisonResponse,
    FaceComparisonImageRequest,
    BoundingBox,
    QualityAssessment,
)
from app.services.face_detection_service import face_detection_service, FaceDetectionError
from app.services.face_embedding_service import face_embedding_service
from app.services.deduplication_service import deduplication_service
from app.core.config import settings
import numpy as np
from app.core.logging import logger
from app.services.metrics_service import metrics_service, MetricType
from app.utils.error_responses import ErrorCode, create_error_response, handle_exception

router = APIRouter(prefix="/face", tags=["face-recognition"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/detect", response_model=FaceDetectionResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def detect_face(
    request: Request,
    detection_request: FaceDetectionRequest
) -> FaceDetectionResponse:
    """
    Detect face in an image and return bounding box with optional quality assessment.
    
    This endpoint:
    - Detects faces using MTCNN (Multi-task Cascaded Convolutional Networks)
    - Returns bounding box coordinates for the detected face
    - Validates that exactly one face is present
    - Optionally assesses image quality (blur, lighting, face size)
    
    **Requirements:**
    - Image must contain exactly one face
    - Face must meet minimum size requirements (80x80 pixels)
    - Supported formats: JPEG, PNG
    
    **Quality Assessment:**
    - Blur detection using Laplacian variance
    - Lighting quality via histogram analysis
    - Face size relative to image dimensions
    
    **Error Codes:**
    - E001: No face detected
    - E002: Multiple faces detected
    - E003: Image quality too low
    - E004: Face too small
    - E005: Invalid image format
    - E100: Processing failed
    
    Args:
        detection_request: Face detection request with base64 encoded image
        
    Returns:
        FaceDetectionResponse with detection results and optional quality assessment
        
    Raises:
        HTTPException: If detection fails or validation errors occur
    """
    start_time = time.time()
    temp_file_path = None
    
    try:
        logger.info(f"Face detection request received from {request.client.host if request.client else 'unknown'}")
        
        # Decode base64 image
        try:
            image_data = base64.b64decode(detection_request.image_base64)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {str(e)}")
            error_response = create_error_response(
                ErrorCode.E005,
                details={"error": "Invalid base64 encoding"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        # Validate image size
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            logger.warning(f"Image too large: {len(image_data)} bytes")
            error_response = create_error_response(
                ErrorCode.E006,
                details={"file_size": len(image_data), "max_size": 10 * 1024 * 1024}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        # Save to temporary file for processing
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{detection_request.image_format}",
            dir=tempfile.gettempdir()
        ) as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        logger.debug(f"Image saved to temporary file: {temp_file_path}")
        
        # Perform face detection
        if detection_request.include_quality:
            # Full detection with quality assessment
            result = face_detection_service.detect_and_assess(temp_file_path)
            
            # Build response with quality assessment
            response = FaceDetectionResponse(
                face_detected=result["face_detected"],
                face_count=result["face_count"],
                bounding_box=BoundingBox(**result["bounding_box"]),
                confidence=result["confidence"],
                quality=QualityAssessment(**result["quality"]),
                processing_time_ms=(time.time() - start_time) * 1000
            )
        else:
            # Detection only, no quality assessment
            detection_result = face_detection_service.detect_faces(temp_file_path)
            
            response = FaceDetectionResponse(
                face_detected=True,
                face_count=detection_result["face_count"],
                bounding_box=BoundingBox(**detection_result["bounding_boxes"][0]),
                confidence=detection_result["confidences"][0],
                quality=None,
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        metrics_service.record_latency(
            MetricType.FACE_RECOGNITION,
            processing_time_ms,
            metadata={"endpoint": "detect", "include_quality": detection_request.include_quality}
        )
        
        logger.info(f"Face detection completed successfully in {processing_time_ms:.2f}ms")
        
        return response
        
    except FaceDetectionError as e:
        # Handle face detection specific errors
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.warning(f"Face detection error: {e.error_code.value} - {e.message}")
        
        # Record error metric
        metrics_service.record_error(
            MetricType.FACE_RECOGNITION,
            f"{e.error_code.value}: {e.message}"
        )
        
        # Map error code to HTTP status
        status_code_map = {
            ErrorCode.E001: status.HTTP_422_UNPROCESSABLE_ENTITY,  # No face
            ErrorCode.E002: status.HTTP_422_UNPROCESSABLE_ENTITY,  # Multiple faces
            ErrorCode.E003: status.HTTP_422_UNPROCESSABLE_ENTITY,  # Quality too low
            ErrorCode.E004: status.HTTP_422_UNPROCESSABLE_ENTITY,  # Face too small
            ErrorCode.E005: status.HTTP_400_BAD_REQUEST,  # Invalid format
        }
        
        http_status = status_code_map.get(e.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        raise HTTPException(
            status_code=http_status,
            detail=e.error_response.dict()
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        # Handle unexpected errors
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.error(f"Unexpected error in face detection: {str(e)}")
        
        # Record error metric
        metrics_service.record_error(
            MetricType.FACE_RECOGNITION,
            f"Unexpected error: {str(e)}"
        )
        
        error_response = handle_exception(e, context="face_detection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )
        
    finally:
        # Clean up temporary file
        if temp_file_path and Path(temp_file_path).exists():
            try:
                Path(temp_file_path).unlink()
                logger.debug(f"Temporary file deleted: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {str(e)}")



@router.post("/embed", response_model=FaceEmbeddingResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def generate_face_embedding(
    request: Request,
    embedding_request: FaceEmbeddingRequest
) -> FaceEmbeddingResponse:
    """
    Generate face embedding from an image.
    
    This endpoint:
    - Detects face in the image
    - Validates face quality
    - Generates 512-dimensional embedding vector using FaceNet
    - Returns L2-normalized embedding
    
    **Requirements:**
    - Image must contain exactly one face
    - Face must meet quality thresholds
    - Supported formats: JPEG, PNG
    
    **Embedding Details:**
    - Model: InceptionResnetV1 (FaceNet)
    - Pre-trained on: VGGFace2 dataset
    - Dimension: 512
    - Normalization: L2 (unit vector)
    
    **Use Cases:**
    - Face verification (compare two faces)
    - Face identification (search in database)
    - Duplicate detection
    
    **Error Codes:**
    - E001: No face detected
    - E002: Multiple faces detected
    - E003: Image quality too low
    - E004: Face too small
    - E005: Invalid image format
    - E101: Embedding generation failed
    
    Args:
        embedding_request: Face embedding request with base64 encoded image
        
    Returns:
        FaceEmbeddingResponse with 512-dimensional embedding vector
        
    Raises:
        HTTPException: If detection or embedding generation fails
    """
    start_time = time.time()
    temp_file_path = None
    
    try:
        logger.info(f"Face embedding request received from {request.client.host if request.client else 'unknown'}")
        
        # Decode base64 image
        try:
            image_data = base64.b64decode(embedding_request.image_base64)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {str(e)}")
            error_response = create_error_response(
                ErrorCode.E005,
                details={"error": "Invalid base64 encoding"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        # Validate image size
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            logger.warning(f"Image too large: {len(image_data)} bytes")
            error_response = create_error_response(
                ErrorCode.E006,
                details={"file_size": len(image_data), "max_size": 10 * 1024 * 1024}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        # Save to temporary file for processing
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{embedding_request.image_format}",
            dir=tempfile.gettempdir()
        ) as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        logger.debug(f"Image saved to temporary file: {temp_file_path}")
        
        # Step 1: Detect face and assess quality
        detection_result = face_detection_service.detect_and_assess(temp_file_path)
        
        face_tensor = detection_result["face_tensor"]
        bounding_box = detection_result["bounding_box"]
        quality_score = detection_result["quality"]["overall_score"]
        
        logger.info(f"Face detected with quality score: {quality_score:.3f}")
        
        # Step 2: Generate embedding
        try:
            embedding = face_embedding_service.generate_embedding(face_tensor)
            
            # Validate embedding
            if not face_embedding_service.validate_embedding(embedding):
                raise RuntimeError("Generated embedding failed validation")
            
            logger.info(f"Embedding generated successfully. Dimension: {len(embedding)}")
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            error_response = create_error_response(
                ErrorCode.E101,
                details={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response.dict()
            )
        
        # Build response
        response = FaceEmbeddingResponse(
            embedding=embedding.tolist(),
            embedding_dimension=len(embedding),
            bounding_box=BoundingBox(**bounding_box),
            quality_score=quality_score,
            processing_time_ms=(time.time() - start_time) * 1000
        )
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        metrics_service.record_latency(
            MetricType.FACE_RECOGNITION,
            processing_time_ms,
            metadata={"endpoint": "embed", "quality_score": quality_score}
        )
        
        logger.info(f"Face embedding completed successfully in {processing_time_ms:.2f}ms")
        
        return response
        
    except FaceDetectionError as e:
        # Handle face detection specific errors
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.warning(f"Face detection error: {e.error_code.value} - {e.message}")
        
        # Record error metric
        metrics_service.record_error(
            MetricType.FACE_RECOGNITION,
            f"{e.error_code.value}: {e.message}"
        )
        
        # Map error code to HTTP status
        status_code_map = {
            ErrorCode.E001: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.E002: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.E003: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.E004: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.E005: status.HTTP_400_BAD_REQUEST,
        }
        
        http_status = status_code_map.get(e.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        raise HTTPException(
            status_code=http_status,
            detail=e.error_response.dict()
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        # Handle unexpected errors
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.error(f"Unexpected error in face embedding: {str(e)}")
        
        # Record error metric
        metrics_service.record_error(
            MetricType.FACE_RECOGNITION,
            f"Unexpected error: {str(e)}"
        )
        
        error_response = handle_exception(e, context="face_embedding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )
        
    finally:
        # Clean up temporary file
        if temp_file_path and Path(temp_file_path).exists():
            try:
                Path(temp_file_path).unlink()
                logger.debug(f"Temporary file deleted: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {str(e)}")



@router.post("/compare", response_model=FaceComparisonResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def compare_face_embeddings(
    request: Request,
    comparison_request: FaceComparisonRequest
) -> FaceComparisonResponse:
    """
    Compare two face embeddings and return similarity score.
    
    This endpoint:
    - Compares two 512-dimensional face embeddings
    - Calculates cosine similarity
    - Determines if faces match based on threshold
    - Returns similarity score and match decision
    
    **Similarity Calculation:**
    - Method: Cosine similarity
    - Range: 0.0 (completely different) to 1.0 (identical)
    - Threshold: Configurable (default: 0.85)
    
    **Match Decision:**
    - similarity >= threshold: Match (is_match = true)
    - similarity < threshold: No match (is_match = false)
    
    **Use Cases:**
    - Face verification (1:1 comparison)
    - Duplicate detection
    - Identity validation
    
    **Requirements:**
    - Both embeddings must be 512-dimensional
    - Embeddings should be L2-normalized
    
    Args:
        comparison_request: Face comparison request with two embeddings
        
    Returns:
        FaceComparisonResponse with similarity score and match decision
        
    Raises:
        HTTPException: If comparison fails or validation errors occur
    """
    start_time = time.time()
    
    try:
        logger.info(f"Face comparison request received from {request.client.host if request.client else 'unknown'}")
        
        # Convert lists to numpy arrays
        embedding1 = np.array(comparison_request.embedding1, dtype=np.float32)
        embedding2 = np.array(comparison_request.embedding2, dtype=np.float32)
        
        # Validate embeddings
        if not face_embedding_service.validate_embedding(embedding1):
            error_response = create_error_response(
                ErrorCode.E400,
                details={"error": "Invalid embedding1: failed validation"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        if not face_embedding_service.validate_embedding(embedding2):
            error_response = create_error_response(
                ErrorCode.E400,
                details={"error": "Invalid embedding2: failed validation"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        # Calculate similarity using deduplication service
        similarity_score = deduplication_service.calculate_cosine_similarity(embedding1, embedding2)
        
        # Calculate cosine distance (1 - similarity)
        distance = 1.0 - similarity_score
        
        # Determine if faces match based on threshold
        threshold = settings.VERIFICATION_THRESHOLD
        is_match = similarity_score >= threshold
        
        logger.info(f"Comparison complete. Similarity: {similarity_score:.4f}, Match: {is_match}")
        
        # Build response
        response = FaceComparisonResponse(
            similarity_score=float(similarity_score),
            is_match=is_match,
            threshold=threshold,
            distance=float(distance),
            processing_time_ms=(time.time() - start_time) * 1000
        )
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        metrics_service.record_latency(
            MetricType.FACE_RECOGNITION,
            processing_time_ms,
            metadata={"endpoint": "compare", "is_match": is_match, "similarity": similarity_score}
        )
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        # Handle unexpected errors
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.error(f"Unexpected error in face comparison: {str(e)}")
        
        # Record error metric
        metrics_service.record_error(
            MetricType.FACE_RECOGNITION,
            f"Comparison error: {str(e)}"
        )
        
        error_response = handle_exception(e, context="face_comparison")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.post("/compare/images", response_model=FaceComparisonResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def compare_face_images(
    request: Request,
    comparison_request: FaceComparisonImageRequest
) -> FaceComparisonResponse:
    """
    Compare two face images directly and return similarity score.
    
    This endpoint:
    - Detects faces in both images
    - Generates embeddings for both faces
    - Compares embeddings and returns similarity
    - Convenience endpoint that combines detection, embedding, and comparison
    
    **Process:**
    1. Detect face in image 1
    2. Detect face in image 2
    3. Generate embedding for face 1
    4. Generate embedding for face 2
    5. Calculate similarity
    6. Return comparison result
    
    **Requirements:**
    - Both images must contain exactly one face
    - Faces must meet quality thresholds
    - Supported formats: JPEG, PNG
    
    **Use Cases:**
    - Quick face verification without pre-computed embeddings
    - One-time comparisons
    - Testing and validation
    
    **Note:** This endpoint is slower than /compare because it performs
    full face detection and embedding generation for both images.
    For repeated comparisons, use /embed to pre-compute embeddings,
    then use /compare.
    
    Args:
        comparison_request: Face comparison request with two images
        
    Returns:
        FaceComparisonResponse with similarity score and match decision
        
    Raises:
        HTTPException: If detection, embedding, or comparison fails
    """
    start_time = time.time()
    temp_file_path1 = None
    temp_file_path2 = None
    
    try:
        logger.info(f"Face image comparison request received from {request.client.host if request.client else 'unknown'}")
        
        # Decode both images
        try:
            image_data1 = base64.b64decode(comparison_request.image1_base64)
            image_data2 = base64.b64decode(comparison_request.image2_base64)
        except Exception as e:
            logger.error(f"Failed to decode base64 images: {str(e)}")
            error_response = create_error_response(
                ErrorCode.E005,
                details={"error": "Invalid base64 encoding"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        # Validate image sizes
        if len(image_data1) > 10 * 1024 * 1024 or len(image_data2) > 10 * 1024 * 1024:
            error_response = create_error_response(
                ErrorCode.E006,
                details={"error": "One or both images exceed 10MB limit"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.dict()
            )
        
        # Save both images to temporary files
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{comparison_request.image1_format}",
            dir=tempfile.gettempdir()
        ) as temp_file:
            temp_file.write(image_data1)
            temp_file_path1 = temp_file.name
        
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{comparison_request.image2_format}",
            dir=tempfile.gettempdir()
        ) as temp_file:
            temp_file.write(image_data2)
            temp_file_path2 = temp_file.name
        
        logger.debug(f"Images saved to temporary files: {temp_file_path1}, {temp_file_path2}")
        
        # Process image 1: detect face and generate embedding
        detection_result1 = face_detection_service.detect_and_assess(temp_file_path1)
        face_tensor1 = detection_result1["face_tensor"]
        embedding1 = face_embedding_service.generate_embedding(face_tensor1)
        
        logger.info(f"Image 1 processed. Quality: {detection_result1['quality']['overall_score']:.3f}")
        
        # Process image 2: detect face and generate embedding
        detection_result2 = face_detection_service.detect_and_assess(temp_file_path2)
        face_tensor2 = detection_result2["face_tensor"]
        embedding2 = face_embedding_service.generate_embedding(face_tensor2)
        
        logger.info(f"Image 2 processed. Quality: {detection_result2['quality']['overall_score']:.3f}")
        
        # Calculate similarity
        similarity_score = deduplication_service.calculate_cosine_similarity(embedding1, embedding2)
        distance = 1.0 - similarity_score
        
        # Determine if faces match
        threshold = settings.VERIFICATION_THRESHOLD
        is_match = similarity_score >= threshold
        
        logger.info(f"Image comparison complete. Similarity: {similarity_score:.4f}, Match: {is_match}")
        
        # Build response
        response = FaceComparisonResponse(
            similarity_score=float(similarity_score),
            is_match=is_match,
            threshold=threshold,
            distance=float(distance),
            processing_time_ms=(time.time() - start_time) * 1000
        )
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        metrics_service.record_latency(
            MetricType.FACE_RECOGNITION,
            processing_time_ms,
            metadata={"endpoint": "compare_images", "is_match": is_match, "similarity": similarity_score}
        )
        
        return response
        
    except FaceDetectionError as e:
        # Handle face detection specific errors
        logger.warning(f"Face detection error in comparison: {e.error_code.value} - {e.message}")
        
        metrics_service.record_error(
            MetricType.FACE_RECOGNITION,
            f"{e.error_code.value}: {e.message}"
        )
        
        status_code_map = {
            ErrorCode.E001: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.E002: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.E003: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.E004: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ErrorCode.E005: status.HTTP_400_BAD_REQUEST,
        }
        
        http_status = status_code_map.get(e.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        raise HTTPException(
            status_code=http_status,
            detail=e.error_response.dict()
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in image comparison: {str(e)}")
        
        metrics_service.record_error(
            MetricType.FACE_RECOGNITION,
            f"Image comparison error: {str(e)}"
        )
        
        error_response = handle_exception(e, context="face_image_comparison")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )
        
    finally:
        # Clean up temporary files
        for temp_path in [temp_file_path1, temp_file_path2]:
            if temp_path and Path(temp_path).exists():
                try:
                    Path(temp_path).unlink()
                    logger.debug(f"Temporary file deleted: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")

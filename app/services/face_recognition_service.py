"""Face recognition service for detection, quality assessment, and embedding generation"""

import cv2
import numpy as np
import torch
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
from facenet_pytorch import MTCNN, InceptionResnetV1

from app.core.config import settings
from app.core.logging import logger
from app.services.metrics_service import metrics_service, MetricType
from app.utils.error_responses import ErrorCode, create_error_response
import time


class FaceRecognitionError(Exception):
    """Custom exception for face recognition errors"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.error_response = create_error_response(error_code, details)
        super().__init__(message)


class FaceRecognitionService:
    """Service for face detection, quality assessment, and embedding generation"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Face recognition service using device: {self.device}")
        
        # Initialize MTCNN for face detection
        self.mtcnn = MTCNN(
            image_size=160,
            margin=0,
            min_face_size=20,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=False,
            device=self.device,
            keep_all=True
        )
        
        # Initialize InceptionResnetV1 for embedding generation
        self.embedding_model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        
        # Configuration
        self.min_face_size = settings.MIN_FACE_SIZE
        self.blur_threshold = settings.BLUR_THRESHOLD
        self.quality_score_threshold = settings.QUALITY_SCORE_THRESHOLD
        
        logger.info("Face recognition service initialized successfully")
    
    def detect_faces(self, image_path: str) -> Tuple[Optional[np.ndarray], Optional[List[Dict[str, int]]], int]:
        """
        Detect faces in photograph using MTCNN
        
        Args:
            image_path: Path to photograph file
            
        Returns:
            Tuple of (face_tensor, bounding_boxes, face_count)
            
        Raises:
            FaceRecognitionError: If no face or multiple faces detected
        """
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            
            # Detect faces
            boxes, probs = self.mtcnn.detect(image)
            
            # Handle no face detected
            if boxes is None or len(boxes) == 0:
                logger.warning(f"No face detected in image: {image_path}")
                raise FaceRecognitionError(
                    error_code=ErrorCode.E001,
                    message="No face detected in photograph",
                    details={"image_path": image_path}
                )
            
            # Handle multiple faces detected
            if len(boxes) > 1:
                logger.warning(f"Multiple faces detected in image: {image_path}. Count: {len(boxes)}")
                raise FaceRecognitionError(
                    error_code=ErrorCode.E002,
                    message=f"Multiple faces detected ({len(boxes)})",
                    details={"image_path": image_path, "face_count": len(boxes)}
                )
            
            # Extract single face
            box = boxes[0]
            prob = probs[0]
            
            # Convert box coordinates to integers
            x1, y1, x2, y2 = [int(coord) for coord in box]
            
            # Validate face size
            face_width = x2 - x1
            face_height = y2 - y1
            
            if face_width < self.min_face_size or face_height < self.min_face_size:
                logger.warning(f"Face too small: {face_width}x{face_height}")
                raise FaceRecognitionError(
                    error_code=ErrorCode.E004,
                    message=f"Face size too small",
                    details={
                        "face_width": face_width,
                        "face_height": face_height,
                        "min_required": self.min_face_size
                    }
                )
            
            # Create bounding box dictionary
            bounding_box = {
                "x": x1,
                "y": y1,
                "width": face_width,
                "height": face_height
            }
            
            # Extract face region for further processing
            face_img = self.mtcnn(image)
            
            logger.info(f"Face detected successfully. Box: {bounding_box}, Confidence: {prob:.3f}")
            
            return face_img, [bounding_box], 1
            
        except FaceRecognitionError:
            raise
        except Exception as e:
            logger.error(f"Face detection failed: {str(e)}")
            raise FaceRecognitionError(
                error_code=ErrorCode.E100,
                message="Face detection processing failed",
                details={"original_error": str(e)}
            )

    def assess_blur(self, image_path: str, bounding_box: Dict[str, int]) -> float:
        """
        Assess photograph blur using Laplacian variance method
        
        Args:
            image_path: Path to photograph file
            bounding_box: Face bounding box coordinates
            
        Returns:
            Blur score (higher is sharper)
            
        Raises:
            FaceRecognitionError: If image is too blurry
        """
        try:
            # Load image in grayscale
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Extract face region
            x, y, w, h = bounding_box["x"], bounding_box["y"], bounding_box["width"], bounding_box["height"]
            face_region = image[y:y+h, x:x+w]
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(face_region, cv2.CV_64F)
            blur_score = laplacian.var()
            
            logger.info(f"Blur assessment: {blur_score:.2f} (threshold: {self.blur_threshold})")
            
            # Check if image is too blurry
            if blur_score < self.blur_threshold:
                raise FaceRecognitionError(
                    error_code=ErrorCode.E003,
                    message="Photograph quality too low",
                    details={
                        "blur_score": blur_score,
                        "threshold": self.blur_threshold,
                        "reason": "blur"
                    }
                )
            
            return blur_score
            
        except FaceRecognitionError:
            raise
        except Exception as e:
            logger.error(f"Blur assessment failed: {str(e)}")
            raise FaceRecognitionError(
                error_code=ErrorCode.E100,
                message="Quality assessment failed",
                details={"original_error": str(e)}
            )
    
    def assess_lighting(self, image_path: str, bounding_box: Dict[str, int]) -> float:
        """
        Assess photograph lighting quality using histogram analysis
        
        Args:
            image_path: Path to photograph file
            bounding_box: Face bounding box coordinates
            
        Returns:
            Lighting quality score (0.0 to 1.0)
        """
        try:
            # Load image in grayscale
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Extract face region
            x, y, w, h = bounding_box["x"], bounding_box["y"], bounding_box["width"], bounding_box["height"]
            face_region = image[y:y+h, x:x+w]
            
            # Calculate histogram
            hist = cv2.calcHist([face_region], [0], None, [256], [0, 256])
            hist = hist.flatten() / hist.sum()
            
            # Calculate mean brightness
            mean_brightness = np.average(np.arange(256), weights=hist)
            
            # Calculate contrast (standard deviation)
            contrast = np.sqrt(np.average((np.arange(256) - mean_brightness) ** 2, weights=hist))
            
            # Normalize scores
            # Good lighting: mean brightness around 128, contrast > 40
            brightness_score = 1.0 - abs(mean_brightness - 128) / 128
            contrast_score = min(contrast / 60, 1.0)
            
            # Combined lighting quality score
            lighting_score = (brightness_score * 0.6 + contrast_score * 0.4)
            
            logger.info(f"Lighting assessment: {lighting_score:.3f} (brightness: {mean_brightness:.1f}, contrast: {contrast:.1f})")
            
            return lighting_score
            
        except Exception as e:
            logger.warning(f"Lighting assessment failed: {str(e)}")
            # Return neutral score if assessment fails
            return 0.5
    
    def assess_quality(self, image_path: str, bounding_box: Dict[str, int]) -> float:
        """
        Perform comprehensive quality assessment
        
        Args:
            image_path: Path to photograph file
            bounding_box: Face bounding box coordinates
            
        Returns:
            Overall quality score (0.0 to 1.0)
            
        Raises:
            FaceRecognitionError: If quality is below threshold
        """
        try:
            # Assess blur (this will raise exception if too blurry)
            blur_score = self.assess_blur(image_path, bounding_box)
            
            # Normalize blur score to 0-1 range
            blur_normalized = min(blur_score / 500, 1.0)
            
            # Assess lighting
            lighting_score = self.assess_lighting(image_path, bounding_box)
            
            # Calculate overall quality score
            quality_score = (blur_normalized * 0.7 + lighting_score * 0.3)
            
            logger.info(f"Overall quality score: {quality_score:.3f}")
            
            # Check if quality meets threshold
            if quality_score < self.quality_score_threshold:
                raise FaceRecognitionError(
                    error_code=ErrorCode.E003,
                    message="Photograph quality too low",
                    details={
                        "quality_score": quality_score,
                        "threshold": self.quality_score_threshold
                    }
                )
            
            return quality_score
            
        except FaceRecognitionError:
            raise
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            raise FaceRecognitionError(
                error_code=ErrorCode.E100,
                message="Quality assessment failed",
                details={"original_error": str(e)}
            )

    def generate_embedding(self, face_tensor: torch.Tensor) -> np.ndarray:
        """
        Generate 512-dimensional facial embedding using InceptionResnetV1
        
        Args:
            face_tensor: Preprocessed face tensor from MTCNN
            
        Returns:
            512-dimensional embedding vector (L2 normalized)
            
        Raises:
            FaceRecognitionError: If embedding generation fails
        """
        try:
            with torch.no_grad():
                # Ensure face_tensor is on correct device
                if face_tensor.dim() == 3:
                    face_tensor = face_tensor.unsqueeze(0)
                
                face_tensor = face_tensor.to(self.device)
                
                # Generate embedding
                embedding = self.embedding_model(face_tensor)
                
                # Convert to numpy array
                embedding_np = embedding.cpu().numpy().flatten()
                
                # L2 normalization
                embedding_normalized = embedding_np / np.linalg.norm(embedding_np)
                
                logger.info(f"Embedding generated successfully. Shape: {embedding_normalized.shape}, Norm: {np.linalg.norm(embedding_normalized):.3f}")
                
                return embedding_normalized
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise FaceRecognitionError(
                error_code=ErrorCode.E101,
                message="Embedding generation failed",
                details={"original_error": str(e)}
            )
    
    def generate_embeddings_batch(self, face_tensors: List[torch.Tensor]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple faces in batch (optimized for performance)
        
        Args:
            face_tensors: List of preprocessed face tensors from MTCNN
            
        Returns:
            List of 512-dimensional embedding vectors (L2 normalized)
            
        Raises:
            FaceRecognitionError: If batch embedding generation fails
        """
        try:
            if not face_tensors:
                return []
            
            with torch.no_grad():
                # Prepare batch tensor
                batch_tensors = []
                for face_tensor in face_tensors:
                    if face_tensor.dim() == 3:
                        face_tensor = face_tensor.unsqueeze(0)
                    batch_tensors.append(face_tensor)
                
                # Stack into single batch
                batch = torch.cat(batch_tensors, dim=0).to(self.device)
                
                # Generate embeddings in batch
                embeddings = self.embedding_model(batch)
                
                # Convert to numpy and normalize
                embeddings_np = embeddings.cpu().numpy()
                
                # L2 normalization for each embedding
                normalized_embeddings = []
                for embedding in embeddings_np:
                    embedding_normalized = embedding / np.linalg.norm(embedding)
                    normalized_embeddings.append(embedding_normalized)
                
                logger.info(f"Batch embedding generation completed. Generated {len(normalized_embeddings)} embeddings")
                
                return normalized_embeddings
                
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise FaceRecognitionError(
                error_code=ErrorCode.E101,
                message="Batch embedding generation failed",
                details={"original_error": str(e), "batch_size": len(face_tensors)}
            )
    
    def process_photograph(self, image_path: str) -> Dict[str, Any]:
        """
        Complete photograph processing pipeline: detection, quality assessment, and embedding generation
        
        Args:
            image_path: Path to photograph file
            
        Returns:
            Dictionary containing:
                - embedding: 512-dimensional embedding vector
                - bounding_box: Face bounding box coordinates
                - quality_score: Overall quality score
                - face_detected: Boolean indicating successful detection
                
        Raises:
            FaceRecognitionError: If any step fails
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing photograph: {image_path}")
            
            # Step 1: Detect face
            face_tensor, bounding_boxes, face_count = self.detect_faces(image_path)
            bounding_box = bounding_boxes[0]
            
            # Step 2: Assess quality
            quality_score = self.assess_quality(image_path, bounding_box)
            
            # Step 3: Generate embedding
            embedding = self.generate_embedding(face_tensor)
            
            result = {
                "embedding": embedding.tolist(),
                "bounding_box": bounding_box,
                "quality_score": quality_score,
                "face_detected": True,
                "face_count": face_count
            }
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            metrics_service.record_latency(
                MetricType.FACE_RECOGNITION,
                latency_ms,
                metadata={"quality_score": quality_score}
            )
            
            logger.info(f"Photograph processing completed successfully in {latency_ms:.2f}ms")
            
            return result
            
        except FaceRecognitionError as e:
            # Record error metric
            metrics_service.record_error(
                MetricType.FACE_RECOGNITION,
                f"{e.error_code.value}: {e.message}"
            )
            raise
        except Exception as e:
            logger.error(f"Photograph processing failed: {str(e)}")
            metrics_service.record_error(
                MetricType.FACE_RECOGNITION,
                str(e)
            )
            raise FaceRecognitionError(
                error_code=ErrorCode.E100,
                message="Photograph processing failed",
                details={"original_error": str(e)}
            )


# Global face recognition service instance
face_recognition_service = FaceRecognitionService()

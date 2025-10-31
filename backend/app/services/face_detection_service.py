"""Face detection service for detecting faces and assessing image quality"""

import cv2
import numpy as np
import torch
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
from facenet_pytorch import MTCNN

from app.core.config import settings
from app.core.logging import logger
from app.utils.error_responses import ErrorCode, create_error_response


class FaceDetectionError(Exception):
    """Custom exception for face detection errors"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.error_response = create_error_response(error_code, details)
        super().__init__(message)


class FaceDetectionService:
    """
    Service for face detection and quality assessment.
    Handles face detection, bounding box extraction, and quality checks (blur, lighting, size).
    """
    
    def __init__(self):
        """Initialize the face detection service with MTCNN model"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Face detection service using device: {self.device}")
        
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
        
        # Configuration from settings
        self.min_face_size = settings.MIN_FACE_SIZE
        self.blur_threshold = settings.BLUR_THRESHOLD
        self.quality_score_threshold = settings.QUALITY_SCORE_THRESHOLD
        
        logger.info(f"Face detection service initialized. Min face size: {self.min_face_size}px, "
                   f"Blur threshold: {self.blur_threshold}, Quality threshold: {self.quality_score_threshold}")
    
    def detect_faces(self, image_path: str) -> Dict[str, Any]:
        """
        Detect faces in an image and return detection results.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing:
                - face_count: Number of faces detected
                - bounding_boxes: List of bounding box dictionaries
                - confidences: List of detection confidence scores
                - face_tensor: Preprocessed face tensor (for single face)
                
        Raises:
            FaceDetectionError: If no face detected, multiple faces, or detection fails
        """
        try:
            logger.info(f"Detecting faces in image: {image_path}")
            
            # Load image
            image = Image.open(image_path).convert('RGB')
            image_width, image_height = image.size
            
            # Detect faces using MTCNN
            boxes, probs = self.mtcnn.detect(image)
            
            # Handle no face detected
            if boxes is None or len(boxes) == 0:
                logger.warning(f"No face detected in image: {image_path}")
                raise FaceDetectionError(
                    error_code=ErrorCode.E001,
                    message="No face detected in photograph",
                    details={
                        "image_path": image_path,
                        "image_size": f"{image_width}x{image_height}"
                    }
                )
            
            # Handle multiple faces detected
            if len(boxes) > 1:
                logger.warning(f"Multiple faces detected in image: {image_path}. Count: {len(boxes)}")
                raise FaceDetectionError(
                    error_code=ErrorCode.E002,
                    message=f"Multiple faces detected ({len(boxes)}). Please upload an image with a single face.",
                    details={
                        "image_path": image_path,
                        "face_count": len(boxes)
                    }
                )
            
            # Extract single face information
            box = boxes[0]
            prob = probs[0]
            
            # Convert box coordinates to integers and create bounding box
            x1, y1, x2, y2 = [int(coord) for coord in box]
            face_width = x2 - x1
            face_height = y2 - y1
            
            # Validate face size
            if face_width < self.min_face_size or face_height < self.min_face_size:
                logger.warning(f"Face too small: {face_width}x{face_height}px (minimum: {self.min_face_size}px)")
                raise FaceDetectionError(
                    error_code=ErrorCode.E004,
                    message=f"Face size too small. Detected: {face_width}x{face_height}px, Required: {self.min_face_size}px minimum",
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
                "height": face_height,
                "x2": x2,
                "y2": y2
            }
            
            # Extract face region tensor for embedding generation
            face_tensor = self.mtcnn(image)
            
            result = {
                "face_count": 1,
                "bounding_boxes": [bounding_box],
                "confidences": [float(prob)],
                "face_tensor": face_tensor
            }
            
            logger.info(f"Face detected successfully. Box: ({x1}, {y1}, {face_width}, {face_height}), "
                       f"Confidence: {prob:.3f}")
            
            return result
            
        except FaceDetectionError:
            raise
        except Exception as e:
            logger.error(f"Face detection failed: {str(e)}")
            raise FaceDetectionError(
                error_code=ErrorCode.E100,
                message="Face detection processing failed",
                details={"original_error": str(e), "image_path": image_path}
            )
    
    def extract_face_region(self, image_path: str, bounding_box: Dict[str, int]) -> np.ndarray:
        """
        Extract face region from image based on bounding box.
        
        Args:
            image_path: Path to the image file
            bounding_box: Dictionary with x, y, width, height keys
            
        Returns:
            Face region as numpy array (BGR format)
            
        Raises:
            ValueError: If bounding box is invalid or extraction fails
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Extract coordinates
            x = bounding_box["x"]
            y = bounding_box["y"]
            w = bounding_box["width"]
            h = bounding_box["height"]
            
            # Validate coordinates
            img_height, img_width = image.shape[:2]
            if x < 0 or y < 0 or x + w > img_width or y + h > img_height:
                raise ValueError(f"Bounding box out of image bounds: ({x}, {y}, {w}, {h}) for image {img_width}x{img_height}")
            
            # Extract face region
            face_region = image[y:y+h, x:x+w]
            
            logger.debug(f"Extracted face region: {face_region.shape}")
            
            return face_region
            
        except Exception as e:
            logger.error(f"Face extraction failed: {str(e)}")
            raise ValueError(f"Failed to extract face region: {str(e)}")
    
    def assess_blur(self, image_path: str, bounding_box: Dict[str, int]) -> float:
        """
        Assess image blur using Laplacian variance method.
        Higher scores indicate sharper images.
        
        Args:
            image_path: Path to the image file
            bounding_box: Face bounding box coordinates
            
        Returns:
            Blur score (higher is sharper, typically 0-500+)
            
        Raises:
            FaceDetectionError: If image is too blurry
        """
        try:
            # Load image in grayscale
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Extract face region
            x, y, w, h = bounding_box["x"], bounding_box["y"], bounding_box["width"], bounding_box["height"]
            face_region = image[y:y+h, x:x+w]
            
            # Calculate Laplacian variance (measure of blur)
            laplacian = cv2.Laplacian(face_region, cv2.CV_64F)
            blur_score = laplacian.var()
            
            logger.info(f"Blur assessment: {blur_score:.2f} (threshold: {self.blur_threshold})")
            
            # Check if image is too blurry
            if blur_score < self.blur_threshold:
                raise FaceDetectionError(
                    error_code=ErrorCode.E003,
                    message=f"Photograph quality too low due to blur. Score: {blur_score:.2f}, Required: {self.blur_threshold}",
                    details={
                        "blur_score": blur_score,
                        "threshold": self.blur_threshold,
                        "reason": "blur"
                    }
                )
            
            return blur_score
            
        except FaceDetectionError:
            raise
        except Exception as e:
            logger.error(f"Blur assessment failed: {str(e)}")
            raise FaceDetectionError(
                error_code=ErrorCode.E100,
                message="Blur assessment failed",
                details={"original_error": str(e)}
            )
    
    def assess_lighting(self, image_path: str, bounding_box: Dict[str, int]) -> float:
        """
        Assess lighting quality using histogram analysis.
        Evaluates brightness and contrast of the face region.
        
        Args:
            image_path: Path to the image file
            bounding_box: Face bounding box coordinates
            
        Returns:
            Lighting quality score (0.0 to 1.0, higher is better)
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
            # Good lighting: mean brightness around 128 (mid-range), contrast > 40
            brightness_score = 1.0 - abs(mean_brightness - 128) / 128
            contrast_score = min(contrast / 60, 1.0)
            
            # Combined lighting quality score (weighted average)
            lighting_score = (brightness_score * 0.6 + contrast_score * 0.4)
            
            logger.info(f"Lighting assessment: {lighting_score:.3f} "
                       f"(brightness: {mean_brightness:.1f}, contrast: {contrast:.1f})")
            
            return lighting_score
            
        except Exception as e:
            logger.warning(f"Lighting assessment failed: {str(e)}")
            # Return neutral score if assessment fails (non-critical)
            return 0.5
    
    def assess_face_size(self, bounding_box: Dict[str, int], image_width: int, image_height: int) -> float:
        """
        Assess if face size is appropriate relative to image dimensions.
        
        Args:
            bounding_box: Face bounding box coordinates
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            Face size score (0.0 to 1.0, higher is better)
        """
        try:
            face_width = bounding_box["width"]
            face_height = bounding_box["height"]
            
            # Calculate face area as percentage of image area
            face_area = face_width * face_height
            image_area = image_width * image_height
            face_ratio = face_area / image_area
            
            # Optimal face ratio is between 10% and 60% of image
            # Too small: hard to recognize, Too large: might be cropped
            if face_ratio < 0.05:
                size_score = face_ratio / 0.05  # Scale from 0 to 1
            elif face_ratio > 0.60:
                size_score = max(0, 1.0 - (face_ratio - 0.60) / 0.40)  # Decrease after 60%
            else:
                size_score = 1.0  # Optimal range
            
            logger.debug(f"Face size assessment: {size_score:.3f} "
                        f"(face: {face_width}x{face_height}, ratio: {face_ratio:.2%})")
            
            return size_score
            
        except Exception as e:
            logger.warning(f"Face size assessment failed: {str(e)}")
            return 0.5
    
    def assess_quality(self, image_path: str, bounding_box: Dict[str, int]) -> Dict[str, float]:
        """
        Perform comprehensive quality assessment on detected face.
        Evaluates blur, lighting, and face size.
        
        Args:
            image_path: Path to the image file
            bounding_box: Face bounding box coordinates
            
        Returns:
            Dictionary containing:
                - overall_score: Combined quality score (0.0 to 1.0)
                - blur_score: Blur assessment score
                - lighting_score: Lighting quality score (0.0 to 1.0)
                - size_score: Face size score (0.0 to 1.0)
                
        Raises:
            FaceDetectionError: If overall quality is below threshold
        """
        try:
            logger.info("Performing quality assessment")
            
            # Get image dimensions
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            img_height, img_width = image.shape[:2]
            
            # Assess blur (this will raise exception if too blurry)
            blur_score = self.assess_blur(image_path, bounding_box)
            
            # Normalize blur score to 0-1 range (typical range is 0-500+)
            blur_normalized = min(blur_score / 500, 1.0)
            
            # Assess lighting
            lighting_score = self.assess_lighting(image_path, bounding_box)
            
            # Assess face size
            size_score = self.assess_face_size(bounding_box, img_width, img_height)
            
            # Calculate overall quality score (weighted average)
            # Blur is most important (50%), lighting (30%), size (20%)
            overall_score = (blur_normalized * 0.5 + lighting_score * 0.3 + size_score * 0.2)
            
            quality_result = {
                "overall_score": overall_score,
                "blur_score": blur_score,
                "blur_normalized": blur_normalized,
                "lighting_score": lighting_score,
                "size_score": size_score
            }
            
            logger.info(f"Quality assessment complete. Overall: {overall_score:.3f}, "
                       f"Blur: {blur_normalized:.3f}, Lighting: {lighting_score:.3f}, Size: {size_score:.3f}")
            
            # Check if quality meets threshold
            if overall_score < self.quality_score_threshold:
                raise FaceDetectionError(
                    error_code=ErrorCode.E003,
                    message=f"Photograph quality too low. Score: {overall_score:.3f}, Required: {self.quality_score_threshold}",
                    details={
                        "quality_score": overall_score,
                        "threshold": self.quality_score_threshold,
                        "blur_score": blur_normalized,
                        "lighting_score": lighting_score,
                        "size_score": size_score
                    }
                )
            
            return quality_result
            
        except FaceDetectionError:
            raise
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            raise FaceDetectionError(
                error_code=ErrorCode.E100,
                message="Quality assessment failed",
                details={"original_error": str(e)}
            )
    
    def detect_and_assess(self, image_path: str) -> Dict[str, Any]:
        """
        Complete face detection and quality assessment pipeline.
        Convenience method that combines detection and quality checks.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing:
                - face_detected: Boolean indicating successful detection
                - face_count: Number of faces detected
                - bounding_box: Face bounding box coordinates
                - confidence: Detection confidence score
                - quality: Quality assessment results
                - face_tensor: Preprocessed face tensor
                
        Raises:
            FaceDetectionError: If detection or quality assessment fails
        """
        try:
            logger.info(f"Starting face detection and assessment for: {image_path}")
            
            # Step 1: Detect face
            detection_result = self.detect_faces(image_path)
            
            bounding_box = detection_result["bounding_boxes"][0]
            confidence = detection_result["confidences"][0]
            face_tensor = detection_result["face_tensor"]
            
            # Step 2: Assess quality
            quality_result = self.assess_quality(image_path, bounding_box)
            
            # Combine results
            result = {
                "face_detected": True,
                "face_count": 1,
                "bounding_box": bounding_box,
                "confidence": confidence,
                "quality": quality_result,
                "face_tensor": face_tensor
            }
            
            logger.info(f"Face detection and assessment completed successfully. "
                       f"Quality score: {quality_result['overall_score']:.3f}")
            
            return result
            
        except FaceDetectionError:
            raise
        except Exception as e:
            logger.error(f"Face detection and assessment failed: {str(e)}")
            raise FaceDetectionError(
                error_code=ErrorCode.E100,
                message="Face detection and assessment failed",
                details={"original_error": str(e), "image_path": image_path}
            )


# Global face detection service instance
face_detection_service = FaceDetectionService()

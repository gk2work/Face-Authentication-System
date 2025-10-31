"""Photograph validation and storage service"""

import base64
import os
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import io

from app.core.config import settings
from app.core.logging import logger
from app.core.security import security_manager


class PhotographValidationError(Exception):
    """Custom exception for photograph validation errors"""
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class PhotographService:
    """Service for photograph validation and storage"""
    
    def __init__(self):
        self.storage_path = Path(settings.STORAGE_PATH)
        self.supported_formats = ["jpg", "jpeg", "png"]
        self.min_resolution = 300  # Minimum width/height in pixels
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def validate_format(self, photograph_format: str) -> None:
        """
        Validate photograph format
        
        Args:
            photograph_format: Image format (jpg, jpeg, png)
            
        Raises:
            PhotographValidationError: If format is invalid
        """
        if photograph_format.lower() not in self.supported_formats:
            raise PhotographValidationError(
                error_code="E006",
                message=f"Invalid photograph format. Supported formats: {', '.join(self.supported_formats)}"
            )
    
    def validate_size(self, file_size: int) -> None:
        """
        Validate photograph file size
        
        Args:
            file_size: File size in bytes
            
        Raises:
            PhotographValidationError: If file size is invalid
        """
        if file_size > self.max_file_size:
            raise PhotographValidationError(
                error_code="E007",
                message=f"File size exceeds maximum allowed size of {self.max_file_size / (1024*1024)}MB"
            )
        
        if file_size < 1024:  # Less than 1KB
            raise PhotographValidationError(
                error_code="E008",
                message="File size too small, possibly corrupted"
            )
    
    def validate_resolution(self, image: Image.Image) -> Tuple[int, int]:
        """
        Validate photograph resolution
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (width, height)
            
        Raises:
            PhotographValidationError: If resolution is invalid
        """
        width, height = image.size
        
        if width < self.min_resolution or height < self.min_resolution:
            raise PhotographValidationError(
                error_code="E009",
                message=f"Image resolution too low. Minimum required: {self.min_resolution}x{self.min_resolution} pixels"
            )
        
        return width, height
    
    def decode_base64_image(self, base64_string: str) -> Image.Image:
        """
        Decode base64 string to PIL Image
        
        Args:
            base64_string: Base64 encoded image string
            
        Returns:
            PIL Image object
            
        Raises:
            PhotographValidationError: If decoding fails
        """
        try:
            # Remove data URL prefix if present
            if "," in base64_string:
                base64_string = base64_string.split(",")[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_string)
            
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {str(e)}")
            raise PhotographValidationError(
                error_code="E010",
                message="Failed to decode photograph. Invalid base64 encoding"
            )
    
    def validate_photograph(self, base64_string: str, photograph_format: str) -> Tuple[Image.Image, int, int, int]:
        """
        Perform complete photograph validation
        
        Args:
            base64_string: Base64 encoded image
            photograph_format: Expected image format
            
        Returns:
            Tuple of (image, width, height, file_size)
            
        Raises:
            PhotographValidationError: If validation fails
        """
        # Validate format
        self.validate_format(photograph_format)
        
        # Calculate file size
        file_size = len(base64_string)
        self.validate_size(file_size)
        
        # Decode image
        image = self.decode_base64_image(base64_string)
        
        # Validate resolution
        width, height = self.validate_resolution(image)
        
        # Verify image format matches
        image_format = image.format.lower() if image.format else ""
        if image_format not in ["jpeg", "jpg", "png"]:
            raise PhotographValidationError(
                error_code="E011",
                message=f"Image format mismatch. Expected {photograph_format}, got {image_format}"
            )
        
        logger.info(f"Photograph validation successful: {width}x{height}, {file_size} bytes")
        
        return image, width, height, file_size
    
    def save_photograph(self, application_id: str, image: Image.Image, photograph_format: str) -> str:
        """
        Save photograph to local storage
        
        Args:
            application_id: Unique application identifier
            image: PIL Image object
            photograph_format: Image format for saving
            
        Returns:
            File path where photograph was saved
            
        Raises:
            Exception: If save operation fails
        """
        try:
            # Normalize format
            save_format = "JPEG" if photograph_format.lower() in ["jpg", "jpeg"] else "PNG"
            extension = "jpg" if photograph_format.lower() in ["jpg", "jpeg"] else "png"
            
            # Generate file path
            file_path = self.storage_path / f"{application_id}.{extension}"
            
            # Convert RGBA to RGB if saving as JPEG
            if save_format == "JPEG" and image.mode == "RGBA":
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[3] if len(image.split()) == 4 else None)
                image = rgb_image
            
            # Save image
            image.save(file_path, format=save_format, quality=95)
            
            # Set secure file permissions
            security_manager.set_secure_file_permissions(str(file_path))
            
            logger.info(f"Photograph saved with secure permissions: {file_path}")
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save photograph: {str(e)}")
            raise
    
    def get_photograph_path(self, application_id: str, photograph_format: str) -> str:
        """
        Generate photograph file path
        
        Args:
            application_id: Unique application identifier
            photograph_format: Image format
            
        Returns:
            File path for the photograph
        """
        extension = "jpg" if photograph_format.lower() in ["jpg", "jpeg"] else "png"
        return str(self.storage_path / f"{application_id}.{extension}")
    
    def delete_photograph(self, file_path: str) -> bool:
        """
        Delete photograph from storage
        
        Args:
            file_path: Path to photograph file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Photograph deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete photograph: {str(e)}")
            return False
    
    def photograph_exists(self, file_path: str) -> bool:
        """
        Check if photograph exists in storage
        
        Args:
            file_path: Path to photograph file
            
        Returns:
            True if exists, False otherwise
        """
        return Path(file_path).exists()


# Global photograph service instance
photograph_service = PhotographService()

"""Unit tests for face recognition service"""

import pytest
import numpy as np
import torch
from PIL import Image
from pathlib import Path
import tempfile
import os

from app.services.face_recognition_service import (
    FaceRecognitionService,
    FaceRecognitionError
)


@pytest.fixture
def face_recognition_service():
    """Create face recognition service instance"""
    return FaceRecognitionService()


@pytest.fixture
def sample_face_image():
    """Create a sample face image for testing"""
    # Create a simple test image (300x300 RGB)
    img = Image.new('RGB', (300, 300), color='white')
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        img.save(tmp.name, 'JPEG')
        yield tmp.name
    
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def blurry_image():
    """Create a blurry test image"""
    img = Image.new('RGB', (300, 300), color='gray')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        img.save(tmp.name, 'JPEG', quality=10)
        yield tmp.name
    
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


class TestFaceDetection:
    """Tests for face detection functionality"""
    
    def test_detect_faces_no_face(self, face_recognition_service, sample_face_image):
        """Test detection when no face is present"""
        with pytest.raises(FaceRecognitionError) as exc_info:
            face_recognition_service.detect_faces(sample_face_image)
        
        assert exc_info.value.error_code == "E001"
        assert "No face detected" in exc_info.value.message
    
    def test_detect_faces_invalid_path(self, face_recognition_service):
        """Test detection with invalid image path"""
        with pytest.raises(FaceRecognitionError) as exc_info:
            face_recognition_service.detect_faces("/nonexistent/path.jpg")
        
        assert exc_info.value.error_code == "E001"


class TestQualityAssessment:
    """Tests for photograph quality assessment"""
    
    def test_assess_blur_with_bounding_box(self, face_recognition_service, sample_face_image):
        """Test blur assessment with valid bounding box"""
        bounding_box = {"x": 50, "y": 50, "width": 100, "height": 100}
        
        # This should raise error for low quality test image
        with pytest.raises(FaceRecognitionError) as exc_info:
            face_recognition_service.assess_blur(sample_face_image, bounding_box)
        
        assert exc_info.value.error_code == "E003"
    
    def test_assess_lighting(self, face_recognition_service, sample_face_image):
        """Test lighting assessment"""
        bounding_box = {"x": 50, "y": 50, "width": 100, "height": 100}
        
        lighting_score = face_recognition_service.assess_lighting(sample_face_image, bounding_box)
        
        assert isinstance(lighting_score, float)
        assert 0.0 <= lighting_score <= 1.0
    
    def test_assess_quality_low_quality(self, face_recognition_service, sample_face_image):
        """Test quality assessment with low quality image"""
        bounding_box = {"x": 50, "y": 50, "width": 100, "height": 100}
        
        with pytest.raises(FaceRecognitionError) as exc_info:
            face_recognition_service.assess_quality(sample_face_image, bounding_box)
        
        assert exc_info.value.error_code == "E003"


class TestEmbeddingGeneration:
    """Tests for facial embedding generation"""
    
    def test_generate_embedding_valid_tensor(self, face_recognition_service):
        """Test embedding generation with valid face tensor"""
        # Create a mock face tensor (3x160x160)
        face_tensor = torch.randn(3, 160, 160)
        
        embedding = face_recognition_service.generate_embedding(face_tensor)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
        
        # Check L2 normalization
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01
    
    def test_generate_embedding_batch_tensor(self, face_recognition_service):
        """Test embedding generation with batch tensor"""
        # Create a batch tensor (1x3x160x160)
        face_tensor = torch.randn(1, 3, 160, 160)
        
        embedding = face_recognition_service.generate_embedding(face_tensor)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
    
    def test_embedding_consistency(self, face_recognition_service):
        """Test that same input produces same embedding"""
        face_tensor = torch.randn(3, 160, 160)
        
        embedding1 = face_recognition_service.generate_embedding(face_tensor)
        embedding2 = face_recognition_service.generate_embedding(face_tensor)
        
        # Should be identical (deterministic)
        np.testing.assert_array_almost_equal(embedding1, embedding2, decimal=5)


class TestErrorHandling:
    """Tests for error handling in face recognition"""
    
    def test_face_recognition_error_attributes(self):
        """Test FaceRecognitionError has correct attributes"""
        error = FaceRecognitionError("E001", "Test error message")
        
        assert error.error_code == "E001"
        assert error.message == "Test error message"
        assert str(error) == "Test error message"
    
    def test_process_photograph_invalid_path(self, face_recognition_service):
        """Test processing with invalid photograph path"""
        with pytest.raises(FaceRecognitionError):
            face_recognition_service.process_photograph("/invalid/path.jpg")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

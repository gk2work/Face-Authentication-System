#!/usr/bin/env python3
"""
Script to download and verify pre-trained face recognition models.
This ensures all required models are available before the application starts.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch


def ensure_directory_exists(path: str) -> Path:
    """Create directory if it doesn't exist"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def download_mtcnn_model():
    """Download MTCNN face detection model"""
    print("Downloading MTCNN face detection model...")
    try:
        # MTCNN will automatically download weights on first use
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        mtcnn = MTCNN(keep_all=True, device=device)
        print("✓ MTCNN model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load MTCNN model: {e}")
        return False


def download_facenet_model():
    """Download FaceNet (InceptionResnetV1) model"""
    print("Downloading FaceNet embedding model...")
    try:
        # Download pretrained model (VGGFace2 trained)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = InceptionResnetV1(pretrained='vggface2').eval().to(device)
        print("✓ FaceNet model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load FaceNet model: {e}")
        return False


def verify_models():
    """Verify all models are accessible"""
    print("\nVerifying models...")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    try:
        # Test MTCNN
        mtcnn = MTCNN(keep_all=True, device=device)
        print("✓ MTCNN verification passed")
        
        # Test FaceNet
        facenet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
        print("✓ FaceNet verification passed")
        
        return True
    except Exception as e:
        print(f"✗ Model verification failed: {e}")
        return False


def main():
    """Main function to download and verify all models"""
    print("=" * 60)
    print("Face Recognition Model Download Script")
    print("=" * 60)
    
    # Ensure model storage directory exists
    model_dir = ensure_directory_exists(settings.MODEL_STORAGE_PATH)
    print(f"\nModel storage path: {model_dir}")
    
    # Download models
    mtcnn_success = download_mtcnn_model()
    facenet_success = download_facenet_model()
    
    # Verify models
    verification_success = verify_models()
    
    # Summary
    print("\n" + "=" * 60)
    print("Download Summary:")
    print(f"  MTCNN: {'✓' if mtcnn_success else '✗'}")
    print(f"  FaceNet: {'✓' if facenet_success else '✗'}")
    print(f"  Verification: {'✓' if verification_success else '✗'}")
    print("=" * 60)
    
    if mtcnn_success and facenet_success and verification_success:
        print("\n✓ All models downloaded and verified successfully!")
        return 0
    else:
        print("\n✗ Some models failed to download or verify.")
        print("Please check your internet connection and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

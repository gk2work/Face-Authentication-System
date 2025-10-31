"""Face embedding generation service - dedicated service for generating facial embeddings"""

import torch
import numpy as np
from typing import List, Optional
from facenet_pytorch import InceptionResnetV1

from app.core.config import settings
from app.core.logging import logger


class FaceEmbeddingService:
    """
    Service dedicated to generating facial embeddings from face tensors.
    Uses InceptionResnetV1 (FaceNet) pre-trained on VGGFace2 dataset.
    """
    
    def __init__(self):
        """Initialize the face embedding service with pre-trained model"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Face embedding service using device: {self.device}")
        
        # Load pre-trained InceptionResnetV1 model
        self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        
        # Configuration
        self.embedding_dimension = settings.EMBEDDING_DIMENSION  # 512
        
        logger.info(f"Face embedding service initialized. Embedding dimension: {self.embedding_dimension}")
    
    def generate_embedding(self, face_tensor: torch.Tensor) -> np.ndarray:
        """
        Generate a 512-dimensional facial embedding from a face tensor.
        
        Args:
            face_tensor: Preprocessed face tensor (typically from MTCNN)
                        Shape: (3, 160, 160) or (1, 3, 160, 160)
        
        Returns:
            512-dimensional embedding vector (L2 normalized)
        
        Raises:
            ValueError: If face_tensor has invalid shape
            RuntimeError: If embedding generation fails
        """
        try:
            with torch.no_grad():
                # Ensure correct tensor shape
                if face_tensor.dim() == 3:
                    # Add batch dimension if needed
                    face_tensor = face_tensor.unsqueeze(0)
                elif face_tensor.dim() != 4:
                    raise ValueError(f"Invalid face tensor shape: {face_tensor.shape}. Expected (3, 160, 160) or (1, 3, 160, 160)")
                
                # Move to correct device
                face_tensor = face_tensor.to(self.device)
                
                # Generate embedding
                embedding = self.model(face_tensor)
                
                # Convert to numpy array
                embedding_np = embedding.cpu().numpy().flatten()
                
                # Validate embedding dimension
                if len(embedding_np) != self.embedding_dimension:
                    raise RuntimeError(f"Generated embedding has incorrect dimension: {len(embedding_np)}, expected {self.embedding_dimension}")
                
                # L2 normalization
                embedding_normalized = self._normalize_embedding(embedding_np)
                
                logger.debug(f"Embedding generated. Shape: {embedding_normalized.shape}, Norm: {np.linalg.norm(embedding_normalized):.6f}")
                
                return embedding_normalized
        
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
    
    def generate_embeddings_batch(self, face_tensors: List[torch.Tensor]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple faces in a single batch (optimized for performance).
        
        Args:
            face_tensors: List of preprocessed face tensors
        
        Returns:
            List of 512-dimensional embedding vectors (L2 normalized)
        
        Raises:
            ValueError: If face_tensors is empty or contains invalid tensors
            RuntimeError: If batch embedding generation fails
        """
        if not face_tensors:
            raise ValueError("face_tensors list cannot be empty")
        
        try:
            with torch.no_grad():
                # Prepare batch tensor
                batch_tensors = []
                for i, face_tensor in enumerate(face_tensors):
                    if face_tensor.dim() == 3:
                        face_tensor = face_tensor.unsqueeze(0)
                    elif face_tensor.dim() != 4:
                        raise ValueError(f"Invalid face tensor shape at index {i}: {face_tensor.shape}")
                    batch_tensors.append(face_tensor)
                
                # Stack into single batch
                batch = torch.cat(batch_tensors, dim=0).to(self.device)
                
                # Generate embeddings in batch
                embeddings = self.model(batch)
                
                # Convert to numpy
                embeddings_np = embeddings.cpu().numpy()
                
                # Normalize each embedding
                normalized_embeddings = []
                for embedding in embeddings_np:
                    if len(embedding) != self.embedding_dimension:
                        raise RuntimeError(f"Generated embedding has incorrect dimension: {len(embedding)}")
                    
                    embedding_normalized = self._normalize_embedding(embedding)
                    normalized_embeddings.append(embedding_normalized)
                
                logger.info(f"Batch embedding generation completed. Generated {len(normalized_embeddings)} embeddings")
                
                return normalized_embeddings
        
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}")
    
    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding vector using L2 normalization.
        
        Args:
            embedding: Raw embedding vector
        
        Returns:
            L2 normalized embedding vector
        """
        norm = np.linalg.norm(embedding)
        
        if norm == 0:
            logger.warning("Embedding has zero norm, returning original")
            return embedding
        
        return embedding / norm
    
    def validate_embedding(self, embedding: np.ndarray) -> bool:
        """
        Validate that an embedding meets requirements.
        
        Args:
            embedding: Embedding vector to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Check dimension
        if len(embedding) != self.embedding_dimension:
            logger.warning(f"Invalid embedding dimension: {len(embedding)}, expected {self.embedding_dimension}")
            return False
        
        # Check for NaN or Inf values
        if np.isnan(embedding).any() or np.isinf(embedding).any():
            logger.warning("Embedding contains NaN or Inf values")
            return False
        
        # Check if normalized (L2 norm should be close to 1.0)
        norm = np.linalg.norm(embedding)
        if not (0.99 <= norm <= 1.01):
            logger.warning(f"Embedding not properly normalized. Norm: {norm}")
            return False
        
        return True
    
    def get_model_info(self) -> dict:
        """
        Get information about the embedding model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": "InceptionResnetV1",
            "pretrained_dataset": "VGGFace2",
            "embedding_dimension": self.embedding_dimension,
            "device": str(self.device),
            "model_parameters": sum(p.numel() for p in self.model.parameters())
        }


# Global face embedding service instance
face_embedding_service = FaceEmbeddingService()

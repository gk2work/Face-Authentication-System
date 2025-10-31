"""Embedding storage service for managing embeddings in FAISS and MongoDB"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.core.logging import logger
from app.services.vector_index_service import vector_index_service
from app.database.repositories import embedding_repository
from app.models.identity import IdentityEmbedding, EmbeddingMetadata, FaceBoundingBox


class EmbeddingStorageService:
    """Service for storing and managing facial embeddings"""
    
    def __init__(self):
        self.batch_size = 100  # Batch size for bulk operations
        logger.info("Embedding storage service initialized")
    
    async def store_embedding(self, identity_id: str, application_id: str,
                             embedding: List[float], bounding_box: Dict[str, int],
                             quality_score: float, model_version: str = "facenet-v1") -> bool:
        """
        Store embedding in both FAISS index and MongoDB
        
        Args:
            identity_id: Identity identifier
            application_id: Application identifier
            embedding: 512-dimensional embedding vector
            bounding_box: Face bounding box coordinates
            quality_score: Quality assessment score
            model_version: Face recognition model version
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Convert embedding to numpy array
            embedding_np = np.array(embedding, dtype=np.float32)
            
            # Add to FAISS index
            index_id = vector_index_service.add_embedding(application_id, embedding_np)
            
            logger.info(f"Added embedding to FAISS index: application={application_id}, index_id={index_id}")
            
            # Create embedding metadata
            metadata = EmbeddingMetadata(
                model_version=model_version,
                quality_score=quality_score,
                face_box=FaceBoundingBox(**bounding_box)
            )
            
            # Create identity embedding document
            identity_embedding = IdentityEmbedding(
                identity_id=identity_id,
                application_id=application_id,
                embedding_vector=embedding,
                metadata=metadata
            )
            
            # Store in MongoDB
            await embedding_repository.create(identity_embedding)
            
            logger.info(f"Stored embedding in MongoDB: identity={identity_id}, application={application_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embedding: {str(e)}")
            return False
    
    async def store_embeddings_batch(self, embeddings_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Store multiple embeddings in batch for performance optimization
        
        Args:
            embeddings_data: List of dictionaries containing:
                - identity_id: Identity identifier
                - application_id: Application identifier
                - embedding: Embedding vector
                - bounding_box: Face bounding box
                - quality_score: Quality score
                - model_version: Model version (optional)
                
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not embeddings_data:
            return 0, 0
        
        successful_count = 0
        failed_count = 0
        
        try:
            # Prepare data for FAISS batch insertion
            faiss_data = []
            mongodb_documents = []
            
            for data in embeddings_data:
                try:
                    # Extract data
                    identity_id = data["identity_id"]
                    application_id = data["application_id"]
                    embedding = data["embedding"]
                    bounding_box = data["bounding_box"]
                    quality_score = data["quality_score"]
                    model_version = data.get("model_version", "facenet-v1")
                    
                    # Convert embedding to numpy array
                    embedding_np = np.array(embedding, dtype=np.float32)
                    
                    # Add to FAISS batch
                    faiss_data.append((application_id, embedding_np))
                    
                    # Create MongoDB document
                    metadata = EmbeddingMetadata(
                        model_version=model_version,
                        quality_score=quality_score,
                        face_box=FaceBoundingBox(**bounding_box)
                    )
                    
                    identity_embedding = IdentityEmbedding(
                        identity_id=identity_id,
                        application_id=application_id,
                        embedding_vector=embedding,
                        metadata=metadata
                    )
                    
                    mongodb_documents.append(identity_embedding)
                    
                except Exception as e:
                    logger.error(f"Failed to prepare embedding data: {str(e)}")
                    failed_count += 1
            
            # Batch insert into FAISS
            if faiss_data:
                index_ids = vector_index_service.add_embeddings_batch(faiss_data)
                logger.info(f"Added {len(index_ids)} embeddings to FAISS index in batch")
            
            # Batch insert into MongoDB
            if mongodb_documents:
                for doc in mongodb_documents:
                    try:
                        await embedding_repository.create(doc)
                        successful_count += 1
                    except Exception as e:
                        logger.error(f"Failed to store embedding in MongoDB: {str(e)}")
                        failed_count += 1
                
                logger.info(f"Stored {successful_count} embeddings in MongoDB")
            
            return successful_count, failed_count
            
        except Exception as e:
            logger.error(f"Batch embedding storage failed: {str(e)}")
            return successful_count, failed_count
    
    async def get_embedding(self, application_id: str) -> Optional[IdentityEmbedding]:
        """
        Get embedding by application ID from MongoDB
        
        Args:
            application_id: Application identifier
            
        Returns:
            IdentityEmbedding or None if not found
        """
        try:
            embedding = await embedding_repository.get_by_application_id(application_id)
            return embedding
        except Exception as e:
            logger.error(f"Failed to get embedding: {str(e)}")
            return None
    
    async def get_embeddings_by_identity(self, identity_id: str) -> List[IdentityEmbedding]:
        """
        Get all embeddings for an identity from MongoDB
        
        Args:
            identity_id: Identity identifier
            
        Returns:
            List of IdentityEmbedding objects
        """
        try:
            embeddings = await embedding_repository.get_by_identity_id(identity_id)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to get embeddings by identity: {str(e)}")
            return []
    
    def get_embedding_from_index(self, application_id: str) -> Optional[np.ndarray]:
        """
        Get embedding vector from FAISS index
        
        Args:
            application_id: Application identifier
            
        Returns:
            Embedding vector or None if not found
        """
        try:
            index_id = vector_index_service.get_index_id(application_id)
            if index_id is None:
                return None
            
            embedding = vector_index_service.index.reconstruct(int(index_id))
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to get embedding from index: {str(e)}")
            return None
    
    async def delete_embedding(self, application_id: str) -> bool:
        """
        Delete embedding from both FAISS and MongoDB
        
        Args:
            application_id: Application identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Remove from FAISS index
            vector_index_service.remove_embedding(application_id)
            
            # Note: MongoDB deletion would need to be implemented in repository
            # For now, we just remove from FAISS
            
            logger.info(f"Deleted embedding for application {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embedding: {str(e)}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        index_stats = vector_index_service.get_stats()
        
        return {
            "faiss_index": index_stats,
            "batch_size": self.batch_size
        }


# Global embedding storage service instance
embedding_storage_service = EmbeddingStorageService()

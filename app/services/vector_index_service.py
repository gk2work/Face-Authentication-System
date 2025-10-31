"""FAISS vector index service for efficient similarity search"""

import faiss
import numpy as np
import json
import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from app.core.config import settings
from app.core.logging import logger


class VectorIndexService:
    """Service for managing FAISS vector index for facial embeddings"""
    
    def __init__(self):
        self.dimension = settings.EMBEDDING_DIMENSION  # 512
        self.index_path = Path(settings.VECTOR_DB_PATH)
        self.index_file = self.index_path / "faiss.index"
        self.mapping_file = self.index_path / "index_mapping.json"
        
        # Ensure storage directory exists
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load FAISS index
        self.index = None
        self.index_to_application_id: Dict[int, str] = {}
        self.application_id_to_index: Dict[str, int] = {}
        self.next_index_id = 0
        
        self._initialize_index()
        
        logger.info(f"Vector index service initialized. Index size: {self.index.ntotal}")
    
    def _initialize_index(self):
        """Initialize or load existing FAISS index"""
        if self.index_file.exists() and self.mapping_file.exists():
            # Load existing index
            self._load_index()
            logger.info(f"Loaded existing FAISS index from {self.index_file}")
        else:
            # Create new index
            self._create_new_index()
            logger.info(f"Created new FAISS index with dimension {self.dimension}")
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Use IndexFlatL2 for exact L2 distance search
        # For larger datasets, consider IndexIVFFlat for faster approximate search
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add index ID tracking
        self.index = faiss.IndexIDMap(self.index)
        
        self.index_to_application_id = {}
        self.application_id_to_index = {}
        self.next_index_id = 0
        
        # Save empty index
        self._save_index()
    
    def _load_index(self):
        """Load existing FAISS index and mapping from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_file))
            
            # Load mapping
            with open(self.mapping_file, 'r') as f:
                mapping_data = json.load(f)
                
                # Convert string keys back to integers for index_to_application_id
                self.index_to_application_id = {
                    int(k): v for k, v in mapping_data["index_to_application_id"].items()
                }
                self.application_id_to_index = mapping_data["application_id_to_index"]
                self.next_index_id = mapping_data["next_index_id"]
            
            logger.info(f"Loaded index with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            logger.info("Creating new index instead")
            self._create_new_index()
    
    def _save_index(self):
        """Save FAISS index and mapping to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_file))
            
            # Save mapping
            mapping_data = {
                "index_to_application_id": self.index_to_application_id,
                "application_id_to_index": self.application_id_to_index,
                "next_index_id": self.next_index_id
            }
            
            with open(self.mapping_file, 'w') as f:
                json.dump(mapping_data, f, indent=2)
            
            logger.info(f"Saved index with {self.index.ntotal} vectors to {self.index_file}")
            
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            raise
    
    def add_embedding(self, application_id: str, embedding: np.ndarray) -> int:
        """
        Add a single embedding to the index
        
        Args:
            application_id: Unique application identifier
            embedding: 512-dimensional embedding vector
            
        Returns:
            Index ID assigned to the embedding
            
        Raises:
            ValueError: If application_id already exists or embedding dimension is incorrect
        """
        # Check if application already exists
        if application_id in self.application_id_to_index:
            raise ValueError(f"Application {application_id} already exists in index")
        
        # Validate embedding dimension
        if embedding.shape[0] != self.dimension:
            raise ValueError(f"Embedding dimension {embedding.shape[0]} does not match expected {self.dimension}")
        
        # Ensure embedding is 2D array for FAISS
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        
        # Ensure float32 type
        embedding = embedding.astype(np.float32)
        
        # Assign index ID
        index_id = self.next_index_id
        
        # Add to FAISS index
        self.index.add_with_ids(embedding, np.array([index_id], dtype=np.int64))
        
        # Update mappings
        self.index_to_application_id[index_id] = application_id
        self.application_id_to_index[application_id] = index_id
        self.next_index_id += 1
        
        # Save index to disk
        self._save_index()
        
        logger.info(f"Added embedding for application {application_id} with index ID {index_id}")
        
        return index_id
    
    def add_embeddings_batch(self, embeddings_data: List[Tuple[str, np.ndarray]]) -> List[int]:
        """
        Add multiple embeddings to the index in batch
        
        Args:
            embeddings_data: List of tuples (application_id, embedding)
            
        Returns:
            List of index IDs assigned to the embeddings
        """
        if not embeddings_data:
            return []
        
        index_ids = []
        embeddings_array = []
        
        for application_id, embedding in embeddings_data:
            # Check if application already exists
            if application_id in self.application_id_to_index:
                logger.warning(f"Skipping duplicate application {application_id}")
                continue
            
            # Validate embedding dimension
            if embedding.shape[0] != self.dimension:
                logger.warning(f"Skipping embedding with incorrect dimension: {embedding.shape[0]}")
                continue
            
            # Assign index ID
            index_id = self.next_index_id
            index_ids.append(index_id)
            
            # Update mappings
            self.index_to_application_id[index_id] = application_id
            self.application_id_to_index[application_id] = index_id
            self.next_index_id += 1
            
            # Collect embedding
            embeddings_array.append(embedding)
        
        if embeddings_array:
            # Convert to numpy array
            embeddings_np = np.array(embeddings_array, dtype=np.float32)
            index_ids_np = np.array(index_ids, dtype=np.int64)
            
            # Add to FAISS index
            self.index.add_with_ids(embeddings_np, index_ids_np)
            
            # Save index to disk
            self._save_index()
            
            logger.info(f"Added {len(embeddings_array)} embeddings in batch")
        
        return index_ids
    
    def get_index_size(self) -> int:
        """Get the number of vectors in the index"""
        return self.index.ntotal
    
    def get_application_id(self, index_id: int) -> Optional[str]:
        """Get application ID for a given index ID"""
        return self.index_to_application_id.get(index_id)
    
    def get_index_id(self, application_id: str) -> Optional[int]:
        """Get index ID for a given application ID"""
        return self.application_id_to_index.get(application_id)
    
    def remove_embedding(self, application_id: str) -> bool:
        """
        Remove an embedding from the index
        
        Note: FAISS IndexIDMap doesn't support removal, so this requires rebuilding the index
        
        Args:
            application_id: Application identifier to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if application_id not in self.application_id_to_index:
            logger.warning(f"Application {application_id} not found in index")
            return False
        
        # Get index ID
        index_id = self.application_id_to_index[application_id]
        
        # Remove from mappings
        del self.application_id_to_index[application_id]
        del self.index_to_application_id[index_id]
        
        # Rebuild index without this embedding
        # This is expensive but necessary for FAISS
        logger.warning("Removing embedding requires index rebuild - this is an expensive operation")
        
        # For now, just update mappings and mark as removed
        # Full rebuild can be done during maintenance
        self._save_index()
        
        logger.info(f"Removed embedding for application {application_id}")
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics
        
        Returns:
            Dictionary with index statistics
        """
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "next_index_id": self.next_index_id,
            "index_type": type(self.index).__name__,
            "index_file": str(self.index_file),
            "mapping_file": str(self.mapping_file)
        }


# Global vector index service instance
vector_index_service = VectorIndexService()

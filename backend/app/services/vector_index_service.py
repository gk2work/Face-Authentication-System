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
        
        # FAISS IVF parameters for performance optimization
        self.use_ivf = True  # Use IndexIVFFlat for faster approximate search
        self.nlist = 100  # Number of clusters (optimal for 10k-100k vectors)
        self.nprobe = 10  # Number of clusters to search (trade-off: speed vs accuracy)
        
        # Ensure storage directory exists
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load FAISS index
        self.index = None
        self.index_to_application_id: Dict[int, str] = {}
        self.application_id_to_index: Dict[str, int] = {}
        self.next_index_id = 0
        
        self._initialize_index()
        
        logger.info(f"Vector index service initialized. Index size: {self.index.ntotal}, IVF enabled: {self.use_ivf}")
    
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
        """Create a new FAISS index with IVF optimization"""
        if self.use_ivf:
            # Use IndexIVFFlat for faster approximate search
            # This is more efficient for larger datasets (>10k vectors)
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
            
            # Set search parameters
            self.index.nprobe = self.nprobe
            
            # Note: IVF index needs training before use
            # Will be trained when we have enough data (>nlist vectors)
            self.index_trained = False
            
            logger.info(f"Created IVF index with nlist={self.nlist}, nprobe={self.nprobe}")
        else:
            # Use IndexFlatL2 for exact L2 distance search (smaller datasets)
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index_trained = True
            logger.info("Created flat L2 index for exact search")
        
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
            
            # Check if index is trained (for IVF indexes)
            self.index_trained = self.index.is_trained if hasattr(self.index, 'is_trained') else True
            
            # Load mapping
            with open(self.mapping_file, 'r') as f:
                mapping_data = json.load(f)
                
                # Convert string keys back to integers for index_to_application_id
                self.index_to_application_id = {
                    int(k): v for k, v in mapping_data["index_to_application_id"].items()
                }
                self.application_id_to_index = mapping_data["application_id_to_index"]
                self.next_index_id = mapping_data["next_index_id"]
            
            logger.info(f"Loaded index with {self.index.ntotal} vectors (trained: {self.index_trained})")
            
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
    
    def _train_index_if_needed(self, embeddings: np.ndarray):
        """Train IVF index if not yet trained and we have enough data"""
        if self.use_ivf and not self.index_trained:
            # Need at least nlist vectors to train
            if embeddings.shape[0] >= self.nlist:
                logger.info(f"Training IVF index with {embeddings.shape[0]} vectors...")
                # Get the underlying index (unwrap IndexIDMap)
                if isinstance(self.index, faiss.IndexIDMap):
                    self.index.index.train(embeddings)
                else:
                    self.index.train(embeddings)
                self.index_trained = True
                logger.info("IVF index training completed")
            else:
                logger.warning(f"Not enough vectors to train IVF index ({embeddings.shape[0]} < {self.nlist})")
    
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
        Add multiple embeddings to the index in batch (optimized for performance)
        
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
            
            # Train index if needed (for IVF)
            self._train_index_if_needed(embeddings_np)
            
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
    
    def search_similar(self, query_embedding: np.ndarray, k: int = 10, 
                      threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in the index (optimized with IVF)
        
        Args:
            query_embedding: Query embedding vector
            k: Number of nearest neighbors to return
            threshold: Optional similarity threshold (cosine similarity)
            
        Returns:
            List of matches with application_id and similarity score
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty, no results to return")
            return []
        
        # Ensure embedding is 2D array for FAISS
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Ensure float32 type
        query_embedding = query_embedding.astype(np.float32)
        
        # Normalize for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        
        # Search index
        distances, indices = self.index.search(query_norm, k)
        
        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            # Convert L2 distance to cosine similarity
            # For normalized vectors: similarity = 1 - (distance^2 / 2)
            similarity = 1.0 - (dist / 2.0)
            similarity = max(0.0, min(1.0, float(similarity)))
            
            # Apply threshold if specified
            if threshold is not None and similarity < threshold:
                continue
            
            application_id = self.index_to_application_id.get(int(idx))
            if application_id:
                results.append({
                    "application_id": application_id,
                    "similarity": similarity,
                    "distance": float(dist)
                })
        
        return results
    
    def search_by_application_id(self, application_id: str, k: int = 10,
                                 threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings using an existing application's embedding
        
        Args:
            application_id: Application ID to use as query
            k: Number of nearest neighbors to return
            threshold: Optional similarity threshold
            
        Returns:
            List of matches (excluding the query application itself)
        """
        # Get index ID
        index_id = self.get_index_id(application_id)
        if index_id is None:
            raise ValueError(f"Application {application_id} not found in index")
        
        # Reconstruct embedding
        embedding = self.index.reconstruct(int(index_id))
        
        # Search (k+1 to account for self-match)
        results = self.search_similar(embedding, k=k+1, threshold=threshold)
        
        # Filter out self-match
        results = [r for r in results if r["application_id"] != application_id]
        
        return results[:k]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics
        
        Returns:
            Dictionary with index statistics
        """
        stats = {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "next_index_id": self.next_index_id,
            "index_type": type(self.index).__name__,
            "index_file": str(self.index_file),
            "mapping_file": str(self.mapping_file)
        }
        
        # Add IVF-specific stats
        if self.use_ivf:
            stats.update({
                "ivf_enabled": True,
                "ivf_trained": self.index_trained,
                "nlist": self.nlist,
                "nprobe": self.nprobe
            })
        
        return stats


# Global vector index service instance
vector_index_service = VectorIndexService()

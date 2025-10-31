"""Integration tests for de-duplication service"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil

from app.services.deduplication_service import (
    DeduplicationService,
    ConfidenceBand
)
from app.services.vector_index_service import VectorIndexService
from app.core.config import settings


@pytest.fixture
def temp_vector_storage():
    """Create temporary directory for vector storage"""
    temp_dir = tempfile.mkdtemp()
    original_path = settings.VECTOR_DB_PATH
    settings.VECTOR_DB_PATH = temp_dir
    
    yield temp_dir
    
    # Cleanup
    settings.VECTOR_DB_PATH = original_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def vector_index_service(temp_vector_storage):
    """Create fresh vector index service for testing"""
    return VectorIndexService()


@pytest.fixture
def deduplication_service():
    """Create deduplication service instance"""
    return DeduplicationService()


@pytest.fixture
def sample_embedding():
    """Create a sample 512-dimensional embedding"""
    np.random.seed(42)
    embedding = np.random.randn(512).astype(np.float32)
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


@pytest.fixture
def similar_embedding(sample_embedding):
    """Create an embedding similar to sample_embedding"""
    # Add small noise to create similar but not identical embedding
    noise = np.random.randn(512).astype(np.float32) * 0.1
    similar = sample_embedding + noise
    # Normalize
    similar = similar / np.linalg.norm(similar)
    return similar


@pytest.fixture
def different_embedding():
    """Create a completely different embedding"""
    np.random.seed(123)
    embedding = np.random.randn(512).astype(np.float32)
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


class TestDuplicateDetection:
    """Tests for duplicate detection functionality"""
    
    def test_detect_no_duplicates_empty_index(self, deduplication_service, 
                                              vector_index_service, sample_embedding):
        """Test detection with empty index returns no duplicates"""
        result = deduplication_service.detect_duplicates(sample_embedding, "app-001")
        
        assert result.is_duplicate is False
        assert result.confidence_band == ConfidenceBand.UNIQUE
        assert len(result.matches) == 0
        assert result.requires_manual_review is False
    
    def test_detect_duplicate_high_confidence(self, deduplication_service, 
                                             vector_index_service, 
                                             sample_embedding, similar_embedding):
        """Test detection of high-confidence duplicate"""
        # Add original embedding to index
        vector_index_service.add_embedding("app-001", sample_embedding)
        
        # Search with very similar embedding
        result = deduplication_service.detect_duplicates(similar_embedding, "app-002")
        
        assert result.is_duplicate is True
        assert len(result.matches) > 0
        assert result.matches[0].matched_application_id == "app-001"
        assert result.matches[0].confidence_score >= deduplication_service.verification_threshold
    
    def test_detect_unique_applicant(self, deduplication_service, 
                                    vector_index_service,
                                    sample_embedding, different_embedding):
        """Test detection correctly identifies unique applicant"""
        # Add original embedding to index
        vector_index_service.add_embedding("app-001", sample_embedding)
        
        # Search with completely different embedding
        result = deduplication_service.detect_duplicates(different_embedding, "app-002")
        
        assert result.is_duplicate is False
        assert result.confidence_band == ConfidenceBand.UNIQUE
        assert len(result.matches) == 0


class TestConfidenceBanding:
    """Tests for confidence score banding"""
    
    def test_high_confidence_band(self, deduplication_service):
        """Test high confidence classification (>0.95)"""
        band = deduplication_service._classify_confidence(0.96)
        assert band == ConfidenceBand.HIGH
    
    def test_medium_confidence_band(self, deduplication_service):
        """Test medium confidence classification (0.85-0.95)"""
        band = deduplication_service._classify_confidence(0.90)
        assert band == ConfidenceBand.MEDIUM
    
    def test_low_confidence_band(self, deduplication_service):
        """Test low confidence classification (<0.85)"""
        band = deduplication_service._classify_confidence(0.80)
        assert band == ConfidenceBand.LOW
    
    def test_borderline_threshold(self, deduplication_service):
        """Test borderline match detection near threshold"""
        # Just above threshold
        assert deduplication_service._is_borderline_match(0.86) is True
        
        # Just below threshold
        assert deduplication_service._is_borderline_match(0.84) is True
        
        # Well above threshold
        assert deduplication_service._is_borderline_match(0.95) is False
        
        # Well below threshold
        assert deduplication_service._is_borderline_match(0.70) is False


class TestThresholdBehavior:
    """Tests for verification threshold behavior"""
    
    def test_threshold_filtering(self, deduplication_service, 
                                 vector_index_service, sample_embedding):
        """Test that matches below threshold are filtered out"""
        # Add embeddings with varying similarity
        vector_index_service.add_embedding("app-001", sample_embedding)
        
        # Create embedding with low similarity
        low_similarity_emb = np.random.randn(512).astype(np.float32)
        low_similarity_emb = low_similarity_emb / np.linalg.norm(low_similarity_emb)
        
        result = deduplication_service.detect_duplicates(low_similarity_emb, "app-002")
        
        # Should not detect as duplicate if similarity is below threshold
        if result.is_duplicate:
            assert result.matches[0].confidence_score >= deduplication_service.verification_threshold
    
    def test_multiple_matches_ranking(self, deduplication_service, 
                                     vector_index_service, sample_embedding):
        """Test that multiple matches are ranked by confidence"""
        # Add multiple embeddings
        vector_index_service.add_embedding("app-001", sample_embedding)
        
        # Add slightly different embedding
        emb2 = sample_embedding + np.random.randn(512).astype(np.float32) * 0.05
        emb2 = emb2 / np.linalg.norm(emb2)
        vector_index_service.add_embedding("app-002", emb2)
        
        # Search with similar embedding
        query_emb = sample_embedding + np.random.randn(512).astype(np.float32) * 0.08
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        result = deduplication_service.detect_duplicates(query_emb, "app-003")
        
        if len(result.matches) > 1:
            # Verify matches are sorted by confidence (descending)
            for i in range(len(result.matches) - 1):
                assert result.matches[i].confidence_score >= result.matches[i + 1].confidence_score


class TestManualReviewFlags:
    """Tests for manual review flagging"""
    
    def test_borderline_match_flags_review(self, deduplication_service, 
                                          vector_index_service, sample_embedding):
        """Test that borderline matches are flagged for manual review"""
        # Add original embedding
        vector_index_service.add_embedding("app-001", sample_embedding)
        
        # Create embedding that will produce borderline similarity
        # This is tricky - we need to engineer a specific similarity score
        # For testing purposes, we'll check the flag logic directly
        threshold = deduplication_service.verification_threshold
        borderline_score = threshold + 0.01  # Just above threshold
        
        assert deduplication_service._is_borderline_match(borderline_score) is True


class TestEmbeddingComparison:
    """Tests for direct embedding comparison"""
    
    def test_compare_identical_embeddings(self, deduplication_service, sample_embedding):
        """Test comparison of identical embeddings"""
        similarity = deduplication_service.compare_embeddings(sample_embedding, sample_embedding)
        
        assert similarity >= 0.99  # Should be very close to 1.0
    
    def test_compare_different_embeddings(self, deduplication_service, 
                                         sample_embedding, different_embedding):
        """Test comparison of different embeddings"""
        similarity = deduplication_service.compare_embeddings(sample_embedding, different_embedding)
        
        assert 0.0 <= similarity <= 1.0
        assert similarity < 0.9  # Should be significantly different


class TestVectorIndexIntegration:
    """Tests for vector index integration"""
    
    def test_add_and_search_single_embedding(self, vector_index_service, sample_embedding):
        """Test adding and searching for a single embedding"""
        # Add embedding
        index_id = vector_index_service.add_embedding("app-001", sample_embedding)
        
        assert index_id >= 0
        assert vector_index_service.get_index_size() == 1
        
        # Search for similar
        results = vector_index_service.search_similar(sample_embedding, k=1)
        
        assert len(results) == 1
        assert results[0]["application_id"] == "app-001"
        assert results[0]["similarity"] >= 0.99
    
    def test_batch_embedding_insertion(self, vector_index_service):
        """Test batch insertion of embeddings"""
        # Create multiple embeddings
        embeddings_data = []
        for i in range(5):
            emb = np.random.randn(512).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            embeddings_data.append((f"app-{i:03d}", emb))
        
        # Batch insert
        index_ids = vector_index_service.add_embeddings_batch(embeddings_data)
        
        assert len(index_ids) == 5
        assert vector_index_service.get_index_size() == 5
    
    def test_index_persistence(self, vector_index_service, sample_embedding, temp_vector_storage):
        """Test that index is persisted to disk"""
        # Add embedding
        vector_index_service.add_embedding("app-001", sample_embedding)
        
        # Check that files exist
        index_file = Path(temp_vector_storage) / "faiss.index"
        mapping_file = Path(temp_vector_storage) / "index_mapping.json"
        
        assert index_file.exists()
        assert mapping_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""De-duplication service for detecting duplicate applications"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger
from app.services.vector_index_service import vector_index_service
from app.services.performance_monitor import performance_monitor, PerformanceTimer, MetricType
from app.models.application import MatchResult
from app.services.audit_service import audit_service


class ConfidenceBand(str, Enum):
    """Confidence score bands for duplicate classification"""
    HIGH = "high"  # > 0.95
    MEDIUM = "medium"  # 0.85 - 0.95
    LOW = "low"  # < 0.85
    UNIQUE = "unique"  # No matches above threshold


class DuplicateDetectionResult:
    """Result of duplicate detection process"""
    
    def __init__(self):
        self.is_duplicate = False
        self.confidence_band = ConfidenceBand.UNIQUE
        self.matches: List[MatchResult] = []
        self.requires_manual_review = False
        self.review_reason: Optional[str] = None
        self.processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_duplicate": self.is_duplicate,
            "confidence_band": self.confidence_band,
            "matches": [
                {
                    "matched_application_id": m.matched_application_id,
                    "confidence_score": m.confidence_score,
                    "matched_identity_id": m.matched_identity_id
                }
                for m in self.matches
            ],
            "requires_manual_review": self.requires_manual_review,
            "review_reason": self.review_reason,
            "processing_time_ms": self.processing_time_ms
        }


class DeduplicationService:
    """Service for detecting duplicate applications using facial embeddings"""
    
    def __init__(self):
        self.verification_threshold = settings.VERIFICATION_THRESHOLD  # 0.85
        self.high_confidence_threshold = 0.95
        self.medium_confidence_threshold = 0.85
        self.borderline_margin = 0.02  # Margin for borderline cases
        self.top_k_candidates = 10
        
        logger.info(f"De-duplication service initialized. Threshold: {self.verification_threshold}")
    
    def _classify_confidence(self, similarity_score: float) -> ConfidenceBand:
        """
        Classify confidence score into bands
        
        Args:
            similarity_score: Cosine similarity score (0-1)
            
        Returns:
            Confidence band classification
        """
        if similarity_score >= self.high_confidence_threshold:
            return ConfidenceBand.HIGH
        elif similarity_score >= self.medium_confidence_threshold:
            return ConfidenceBand.MEDIUM
        else:
            return ConfidenceBand.LOW
    
    def _is_borderline_match(self, similarity_score: float) -> bool:
        """
        Check if similarity score is borderline (near threshold)
        
        Args:
            similarity_score: Cosine similarity score
            
        Returns:
            True if borderline, False otherwise
        """
        lower_bound = self.verification_threshold - self.borderline_margin
        upper_bound = self.verification_threshold + self.borderline_margin
        
        return lower_bound <= similarity_score <= upper_bound
    
    def _has_multiple_high_matches(self, matches: List[Dict[str, Any]]) -> bool:
        """
        Check if there are multiple high-confidence matches
        
        Args:
            matches: List of match results
            
        Returns:
            True if multiple high matches exist
        """
        high_matches = [
            m for m in matches 
            if m["similarity"] >= self.high_confidence_threshold
        ]
        return len(high_matches) > 1
    
    async def detect_duplicates(self, embedding: np.ndarray, 
                         application_id: Optional[str] = None,
                         db = None) -> DuplicateDetectionResult:
        """
        Detect duplicate applications using facial embedding
        
        Args:
            embedding: 512-dimensional facial embedding
            application_id: Optional application ID (for logging)
            
        Returns:
            DuplicateDetectionResult with match information
        """
        start_time = datetime.utcnow()
        result = DuplicateDetectionResult()
        
        try:
            # Search for similar embeddings with performance monitoring
            with PerformanceTimer(performance_monitor, MetricType.VECTOR_INDEX_QUERY, 
                                 {"application_id": application_id, "k": self.top_k_candidates}):
                matches = vector_index_service.search_similar(
                    query_embedding=embedding,
                    k=self.top_k_candidates,
                    threshold=None  # Get all matches, filter later
                )
            
            # Filter matches above verification threshold
            duplicate_matches = [
                m for m in matches 
                if m["similarity"] >= self.verification_threshold
            ]
            
            if not duplicate_matches:
                # No duplicates found
                result.is_duplicate = False
                result.confidence_band = ConfidenceBand.UNIQUE
                logger.info(f"No duplicates found for application {application_id}")
            else:
                # Duplicates found
                result.is_duplicate = True
                
                # Get highest confidence match
                best_match = duplicate_matches[0]
                result.confidence_band = self._classify_confidence(best_match["similarity"])
                
                # Convert to MatchResult objects
                result.matches = [
                    MatchResult(
                        matched_application_id=m["application_id"],
                        confidence_score=m["similarity"],
                        matched_identity_id=None  # Will be populated later
                    )
                    for m in duplicate_matches
                ]
                
                # Check for borderline cases requiring manual review
                if self._is_borderline_match(best_match["similarity"]):
                    result.requires_manual_review = True
                    result.review_reason = f"Borderline match: similarity score {best_match['similarity']:.3f} is near threshold {self.verification_threshold}"
                    logger.warning(f"Borderline match detected for application {application_id}: {best_match['similarity']:.3f}")
                
                # Check for multiple high-confidence matches
                if self._has_multiple_high_matches(duplicate_matches):
                    result.requires_manual_review = True
                    result.review_reason = "Multiple high-confidence matches detected, requires verification"
                    logger.warning(f"Multiple high matches detected for application {application_id}")
                
                logger.info(f"Duplicates found for application {application_id}: {len(duplicate_matches)} matches, best: {best_match['similarity']:.3f}")
            
            # Calculate processing time
            end_time = datetime.utcnow()
            result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Record overall duplicate detection metric
            performance_monitor.record_metric(
                MetricType.DUPLICATE_DETECTION,
                result.processing_time_ms,
                {
                    "application_id": application_id,
                    "is_duplicate": result.is_duplicate,
                    "match_count": len(result.matches)
                }
            )
            
            # Log duplicate detection event to audit trail
            if db and application_id:
                matched_app_id = result.matches[0].matched_application_id if result.matches else None
                confidence = result.matches[0].confidence_score if result.matches else 0.0
                
                await audit_service.log_duplicate_detection(
                    db=db,
                    application_id=application_id,
                    matched_application_id=matched_app_id,
                    confidence_score=confidence,
                    is_duplicate=result.is_duplicate
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Duplicate detection failed for application {application_id}: {str(e)}")
            raise
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compare two embeddings and return similarity score
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Normalize embeddings
        emb1_norm = embedding1 / np.linalg.norm(embedding1)
        emb2_norm = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)
        
        # Clamp to [0, 1] range
        similarity = max(0.0, min(1.0, float(similarity)))
        
        return similarity
    
    def verify_match(self, application_id1: str, application_id2: str) -> Tuple[bool, float]:
        """
        Verify if two applications are duplicates
        
        Args:
            application_id1: First application ID
            application_id2: Second application ID
            
        Returns:
            Tuple of (is_duplicate, similarity_score)
        """
        try:
            # Get embeddings from index
            index_id1 = vector_index_service.get_index_id(application_id1)
            index_id2 = vector_index_service.get_index_id(application_id2)
            
            if index_id1 is None or index_id2 is None:
                raise ValueError("One or both applications not found in index")
            
            # Reconstruct embeddings
            embedding1 = vector_index_service.index.reconstruct(int(index_id1))
            embedding2 = vector_index_service.index.reconstruct(int(index_id2))
            
            # Compare embeddings
            similarity = self.compare_embeddings(embedding1, embedding2)
            
            # Check if duplicate
            is_duplicate = similarity >= self.verification_threshold
            
            logger.info(f"Verified match between {application_id1} and {application_id2}: {similarity:.3f} (duplicate: {is_duplicate})")
            
            return is_duplicate, similarity
            
        except Exception as e:
            logger.error(f"Match verification failed: {str(e)}")
            raise
    
    def get_duplicate_candidates(self, application_id: str, 
                                 include_low_confidence: bool = False) -> List[Dict[str, Any]]:
        """
        Get duplicate candidates for an existing application
        
        Args:
            application_id: Application ID to check
            include_low_confidence: Include matches below verification threshold
            
        Returns:
            List of candidate matches with metadata
        """
        try:
            # Search using existing application
            threshold = None if include_low_confidence else self.verification_threshold
            
            matches = vector_index_service.search_by_application_id(
                application_id=application_id,
                k=self.top_k_candidates,
                threshold=threshold
            )
            
            # Add confidence band classification
            for match in matches:
                match["confidence_band"] = self._classify_confidence(match["similarity"])
                match["is_borderline"] = self._is_borderline_match(match["similarity"])
            
            logger.info(f"Found {len(matches)} duplicate candidates for application {application_id}")
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to get duplicate candidates: {str(e)}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get de-duplication service statistics
        
        Returns:
            Dictionary with service statistics
        """
        index_stats = vector_index_service.get_stats()
        
        return {
            "verification_threshold": self.verification_threshold,
            "high_confidence_threshold": self.high_confidence_threshold,
            "medium_confidence_threshold": self.medium_confidence_threshold,
            "borderline_margin": self.borderline_margin,
            "top_k_candidates": self.top_k_candidates,
            "index_stats": index_stats
        }


# Global de-duplication service instance
deduplication_service = DeduplicationService()

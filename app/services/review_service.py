"""Review service for duplicate case presentation and comparison"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from app.core.logging import logger
from app.database.repositories import application_repository
from app.models.application import Application


class ReviewService:
    """Service for building duplicate case presentations"""
    
    def __init__(self):
        logger.info("Review service initialized")
    
    def _build_application_summary(self, application: Application) -> Dict[str, Any]:
        """
        Build summary data for an application
        
        Args:
            application: Application object
            
        Returns:
            Dictionary with application summary
        """
        return {
            "application_id": application.application_id,
            "applicant_data": {
                "name": application.applicant_data.name,
                "email": application.applicant_data.email,
                "phone": application.applicant_data.phone,
                "date_of_birth": application.applicant_data.date_of_birth,
                "address": application.applicant_data.address
            },
            "photograph": {
                "path": application.photograph.path,
                "url": application.photograph.url,
                "format": application.photograph.format,
                "width": application.photograph.width,
                "height": application.photograph.height,
                "uploaded_at": application.photograph.uploaded_at.isoformat()
            },
            "processing": {
                "status": application.processing.status,
                "face_detected": application.processing.face_detected,
                "quality_score": application.processing.quality_score,
                "error_code": application.processing.error_code,
                "error_message": application.processing.error_message
            },
            "created_at": application.created_at.isoformat(),
            "updated_at": application.updated_at.isoformat()
        }
    
    def _calculate_similarity_indicators(self, confidence_score: float,
                                        current_quality: Optional[float],
                                        matched_quality: Optional[float]) -> Dict[str, Any]:
        """
        Calculate visual similarity indicators
        
        Args:
            confidence_score: Match confidence score
            current_quality: Quality score of current application
            matched_quality: Quality score of matched application
            
        Returns:
            Dictionary with similarity indicators
        """
        # Determine confidence band
        if confidence_score >= 0.95:
            confidence_band = "high"
            confidence_label = "Very High Confidence"
            confidence_color = "green"
        elif confidence_score >= 0.85:
            confidence_band = "medium"
            confidence_label = "Medium Confidence"
            confidence_color = "yellow"
        else:
            confidence_band = "low"
            confidence_label = "Low Confidence"
            confidence_color = "red"
        
        # Calculate quality comparison
        quality_diff = 0.0
        if current_quality is not None and matched_quality is not None:
            quality_diff = abs(current_quality - matched_quality)
        
        # Determine if borderline
        is_borderline = 0.83 <= confidence_score <= 0.87
        
        return {
            "confidence_score": confidence_score,
            "confidence_percentage": round(confidence_score * 100, 2),
            "confidence_band": confidence_band,
            "confidence_label": confidence_label,
            "confidence_color": confidence_color,
            "is_borderline": is_borderline,
            "quality_comparison": {
                "current_quality": current_quality or 0.0,
                "matched_quality": matched_quality or 0.0,
                "quality_difference": quality_diff,
                "quality_similar": quality_diff < 0.1
            },
            "visual_indicators": {
                "face_match_icon": "✓" if confidence_score >= 0.85 else "✗",
                "quality_match_icon": "✓" if quality_diff < 0.1 else "⚠",
                "review_required_icon": "⚠" if is_borderline else ""
            }
        }
    
    async def build_comparison_view(self, application_id: str) -> Dict[str, Any]:
        """
        Build comprehensive comparison view for duplicate case
        
        Args:
            application_id: Application ID to build comparison for
            
        Returns:
            Dictionary with comparison view data
            
        Raises:
            ValueError: If application not found or not a duplicate
        """
        try:
            # Get current application
            current_app = await application_repository.get_by_id(application_id)
            
            if not current_app:
                raise ValueError(f"Application {application_id} not found")
            
            # Check if it's a duplicate
            if not current_app.result.is_duplicate:
                raise ValueError(f"Application {application_id} is not marked as duplicate")
            
            # Get matched application
            matched_app = None
            confidence_score = 0.0
            
            if current_app.result.matched_applications and len(current_app.result.matched_applications) > 0:
                matched_app_id = current_app.result.matched_applications[0].matched_application_id
                confidence_score = current_app.result.matched_applications[0].confidence_score
                matched_app = await application_repository.get_by_id(matched_app_id)
            
            if not matched_app:
                raise ValueError(f"Matched application not found for {application_id}")
            
            # Build application summaries
            current_summary = self._build_application_summary(current_app)
            matched_summary = self._build_application_summary(matched_app)
            
            # Calculate similarity indicators
            similarity_indicators = self._calculate_similarity_indicators(
                confidence_score=confidence_score,
                current_quality=current_app.processing.quality_score,
                matched_quality=matched_app.processing.quality_score
            )
            
            # Build comparison view
            comparison_view = {
                "case_id": application_id,
                "current_application": current_summary,
                "matched_application": matched_summary,
                "similarity_indicators": similarity_indicators,
                "review_metadata": {
                    "requires_review": is_borderline or confidence_score < 0.90,
                    "review_priority": "high" if similarity_indicators["is_borderline"] else "normal",
                    "reviewed": current_app.result.reviewed_by is not None,
                    "reviewed_by": current_app.result.reviewed_by,
                    "review_notes": current_app.result.review_notes,
                    "reviewed_at": current_app.result.reviewed_at.isoformat() if current_app.result.reviewed_at else None
                },
                "comparison_fields": self._build_field_comparison(current_app, matched_app)
            }
            
            logger.info(f"Built comparison view for case: {application_id}")
            
            return comparison_view
            
        except Exception as e:
            logger.error(f"Failed to build comparison view: {str(e)}")
            raise ValueError(f"Failed to build comparison view: {str(e)}")
    
    def _build_field_comparison(self, current_app: Application, 
                                matched_app: Application) -> Dict[str, Any]:
        """
        Build field-by-field comparison
        
        Args:
            current_app: Current application
            matched_app: Matched application
            
        Returns:
            Dictionary with field comparisons
        """
        return {
            "name": {
                "current": current_app.applicant_data.name,
                "matched": matched_app.applicant_data.name,
                "match": current_app.applicant_data.name.lower() == matched_app.applicant_data.name.lower()
            },
            "email": {
                "current": current_app.applicant_data.email,
                "matched": matched_app.applicant_data.email,
                "match": current_app.applicant_data.email.lower() == matched_app.applicant_data.email.lower()
            },
            "phone": {
                "current": current_app.applicant_data.phone,
                "matched": matched_app.applicant_data.phone,
                "match": current_app.applicant_data.phone == matched_app.applicant_data.phone
            },
            "date_of_birth": {
                "current": current_app.applicant_data.date_of_birth,
                "matched": matched_app.applicant_data.date_of_birth,
                "match": current_app.applicant_data.date_of_birth == matched_app.applicant_data.date_of_birth
            }
        }
    
    def get_photograph_paths(self, application_id: str, 
                            matched_application_id: str) -> Dict[str, str]:
        """
        Get local file paths for photographs
        
        Args:
            application_id: Current application ID
            matched_application_id: Matched application ID
            
        Returns:
            Dictionary with photograph paths
        """
        from app.core.config import settings
        
        storage_path = Path(settings.STORAGE_PATH)
        
        return {
            "current_photograph": str(storage_path / f"{application_id}.jpg"),
            "matched_photograph": str(storage_path / f"{matched_application_id}.jpg"),
            "storage_base_path": str(storage_path)
        }
    
    async def get_review_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about cases requiring review
        
        Returns:
            Dictionary with review statistics
        """
        try:
            # This would require additional repository methods
            # For now, return placeholder data
            return {
                "total_duplicates": 0,
                "pending_review": 0,
                "reviewed": 0,
                "high_priority": 0,
                "borderline_cases": 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get review statistics: {str(e)}")
            return {}


# Global review service instance
review_service = ReviewService()

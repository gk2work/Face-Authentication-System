"""Admin API endpoints for duplicate review and override"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.application import Application, ApplicationStatus
from app.models.audit import AuditLog, EventType, ActorType, ResourceType
from app.database.mongodb import get_database
from app.database.repositories import ApplicationRepository, AuditLogRepository
from app.core.logging import logger

router = APIRouter(prefix="/admin", tags=["admin"])


class DuplicateCaseResponse(BaseModel):
    """Response model for duplicate case"""
    case_id: str
    application_id: str
    matched_application_id: str
    confidence_score: float
    status: ApplicationStatus
    requires_review: bool
    applicant_name: str
    created_at: datetime
    photograph_path: str


class DuplicateCaseDetailResponse(BaseModel):
    """Detailed response model for duplicate case"""
    case_id: str
    current_application: Dict[str, Any]
    matched_application: Dict[str, Any]
    confidence_score: float
    similarity_indicators: Dict[str, Any]
    review_status: str
    created_at: datetime


class OverrideDecisionRequest(BaseModel):
    """Request model for override decision"""
    decision: str = Field(..., description="Decision: 'approve_duplicate', 'reject_duplicate', 'flag_for_further_review'")
    justification: str = Field(..., min_length=10, description="Justification for the decision")
    admin_id: str = Field(..., description="Admin user ID")


class OverrideDecisionResponse(BaseModel):
    """Response model for override decision"""
    case_id: str
    decision: str
    success: bool
    message: str
    updated_at: datetime


class PaginatedDuplicatesResponse(BaseModel):
    """Paginated response for duplicate cases"""
    total: int
    page: int
    page_size: int
    total_pages: int
    cases: List[DuplicateCaseResponse]


@router.get("/duplicates", response_model=PaginatedDuplicatesResponse)
async def get_duplicate_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    requires_review: Optional[bool] = Query(None, description="Filter by review requirement"),
    db=Depends(get_database)
) -> PaginatedDuplicatesResponse:
    """
    Get paginated list of duplicate cases for review
    
    - **page**: Page number (starting from 1)
    - **page_size**: Number of items per page (max 100)
    - **status_filter**: Optional status filter
    - **requires_review**: Optional filter for cases requiring manual review
    
    Returns paginated list of duplicate cases
    """
    try:
        app_repo = ApplicationRepository(db)
        
        # Calculate skip value for pagination
        skip = (page - 1) * page_size
        
        # Get duplicate applications
        # Note: This is a simplified version - in production, you'd want a more efficient query
        duplicate_applications = await app_repo.get_by_status(
            ApplicationStatus.DUPLICATE,
            limit=page_size,
            skip=skip
        )
        
        # Build response cases
        cases = []
        for app in duplicate_applications:
            # Get matched application info from result
            matched_app_id = None
            confidence_score = 0.0
            
            if app.result.matched_applications and len(app.result.matched_applications) > 0:
                matched_app_id = app.result.matched_applications[0].matched_application_id
                confidence_score = app.result.matched_applications[0].confidence_score
            
            # Check if requires review (from processing metadata or result)
            requires_review = False
            if hasattr(app.processing, 'requires_manual_review'):
                requires_review = app.processing.requires_manual_review
            
            case = DuplicateCaseResponse(
                case_id=app.application_id,
                application_id=app.application_id,
                matched_application_id=matched_app_id or "unknown",
                confidence_score=confidence_score,
                status=app.processing.status,
                requires_review=requires_review,
                applicant_name=app.applicant_data.name,
                created_at=app.created_at,
                photograph_path=app.photograph.path or ""
            )
            cases.append(case)
        
        # Calculate total (simplified - in production, use count query)
        total = len(cases)
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(f"Retrieved {len(cases)} duplicate cases (page {page})")
        
        return PaginatedDuplicatesResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(1, total_pages),
            cases=cases
        )
        
    except Exception as e:
        logger.error(f"Error retrieving duplicate cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve duplicate cases"
        )


@router.get("/duplicates/{case_id}", response_model=DuplicateCaseDetailResponse)
async def get_duplicate_case_details(
    case_id: str,
    db=Depends(get_database)
) -> DuplicateCaseDetailResponse:
    """
    Get detailed information about a specific duplicate case
    
    - **case_id**: Unique case identifier (application ID)
    
    Returns detailed case information including both applications and comparison data
    """
    try:
        app_repo = ApplicationRepository(db)
        
        # Get current application
        current_app = await app_repo.get_by_id(case_id)
        
        if not current_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {case_id} not found"
            )
        
        # Get matched application
        matched_app = None
        matched_app_id = None
        confidence_score = 0.0
        
        if current_app.result.matched_applications and len(current_app.result.matched_applications) > 0:
            matched_app_id = current_app.result.matched_applications[0].matched_application_id
            confidence_score = current_app.result.matched_applications[0].confidence_score
            matched_app = await app_repo.get_by_id(matched_app_id)
        
        # Build current application data
        current_app_data = {
            "application_id": current_app.application_id,
            "applicant_name": current_app.applicant_data.name,
            "applicant_email": current_app.applicant_data.email,
            "applicant_phone": current_app.applicant_data.phone,
            "date_of_birth": current_app.applicant_data.date_of_birth,
            "photograph_path": current_app.photograph.path,
            "photograph_url": current_app.photograph.url,
            "quality_score": current_app.processing.quality_score,
            "created_at": current_app.created_at.isoformat(),
            "status": current_app.processing.status
        }
        
        # Build matched application data
        matched_app_data = {}
        if matched_app:
            matched_app_data = {
                "application_id": matched_app.application_id,
                "applicant_name": matched_app.applicant_data.name,
                "applicant_email": matched_app.applicant_data.email,
                "applicant_phone": matched_app.applicant_data.phone,
                "date_of_birth": matched_app.applicant_data.date_of_birth,
                "photograph_path": matched_app.photograph.path,
                "photograph_url": matched_app.photograph.url,
                "quality_score": matched_app.processing.quality_score,
                "created_at": matched_app.created_at.isoformat(),
                "status": matched_app.processing.status
            }
        
        # Build similarity indicators
        similarity_indicators = {
            "confidence_score": confidence_score,
            "confidence_band": "high" if confidence_score >= 0.95 else "medium" if confidence_score >= 0.85 else "low",
            "face_match": confidence_score >= 0.85,
            "quality_comparison": {
                "current": current_app.processing.quality_score or 0.0,
                "matched": matched_app.processing.quality_score if matched_app else 0.0
            }
        }
        
        # Determine review status
        review_status = "pending"
        if current_app.result.reviewed_by:
            review_status = "reviewed"
        elif hasattr(current_app.processing, 'requires_manual_review') and current_app.processing.requires_manual_review:
            review_status = "requires_review"
        
        logger.info(f"Retrieved detailed case information: {case_id}")
        
        return DuplicateCaseDetailResponse(
            case_id=case_id,
            current_application=current_app_data,
            matched_application=matched_app_data,
            confidence_score=confidence_score,
            similarity_indicators=similarity_indicators,
            review_status=review_status,
            created_at=current_app.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving case details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve case details"
        )


@router.post("/duplicates/{case_id}/override", response_model=OverrideDecisionResponse)
async def override_duplicate_decision(
    case_id: str,
    decision_request: OverrideDecisionRequest,
    db=Depends(get_database)
) -> OverrideDecisionResponse:
    """
    Override automatic duplicate detection decision
    
    - **case_id**: Unique case identifier (application ID)
    - **decision**: Override decision (approve_duplicate, reject_duplicate, flag_for_further_review)
    - **justification**: Justification for the override decision
    - **admin_id**: Admin user ID making the decision
    
    Returns override decision result
    """
    try:
        app_repo = ApplicationRepository(db)
        audit_repo = AuditLogRepository(db)
        
        # Get application
        application = await app_repo.get_by_id(case_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {case_id} not found"
            )
        
        # Validate decision
        valid_decisions = ["approve_duplicate", "reject_duplicate", "flag_for_further_review"]
        if decision_request.decision not in valid_decisions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}"
            )
        
        # Apply decision
        new_status = application.processing.status
        result_data = {}
        
        if decision_request.decision == "approve_duplicate":
            # Keep as duplicate
            new_status = ApplicationStatus.DUPLICATE
            result_data = {
                "final_status": ApplicationStatus.DUPLICATE,
                "reviewed_by": decision_request.admin_id,
                "review_notes": decision_request.justification,
                "reviewed_at": datetime.utcnow()
            }
        elif decision_request.decision == "reject_duplicate":
            # Mark as verified (not a duplicate)
            new_status = ApplicationStatus.VERIFIED
            result_data = {
                "is_duplicate": False,
                "final_status": ApplicationStatus.VERIFIED,
                "reviewed_by": decision_request.admin_id,
                "review_notes": decision_request.justification,
                "reviewed_at": datetime.utcnow()
            }
        elif decision_request.decision == "flag_for_further_review":
            # Keep current status but flag for review
            result_data = {
                "reviewed_by": decision_request.admin_id,
                "review_notes": decision_request.justification,
                "reviewed_at": datetime.utcnow()
            }
        
        # Update application
        await app_repo.update_status(case_id, new_status)
        await app_repo.update_result(case_id, result_data)
        
        # Create audit log
        audit_log = AuditLog(
            event_type=EventType.DUPLICATE_OVERRIDE,
            actor_id=decision_request.admin_id,
            actor_type=ActorType.ADMIN,
            resource_id=case_id,
            resource_type=ResourceType.APPLICATION,
            action=f"Override decision: {decision_request.decision}",
            details={
                "decision": decision_request.decision,
                "justification": decision_request.justification,
                "previous_status": application.processing.status,
                "new_status": new_status
            },
            success=True
        )
        await audit_repo.create(audit_log)
        
        logger.info(f"Override decision applied: {case_id} - {decision_request.decision}")
        
        return OverrideDecisionResponse(
            case_id=case_id,
            decision=decision_request.decision,
            success=True,
            message=f"Override decision '{decision_request.decision}' applied successfully",
            updated_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying override decision: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply override decision"
        )

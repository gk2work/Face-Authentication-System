"""Identity management API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Any
from datetime import datetime

from app.models.identity import Identity, IdentityResponse, IdentityStatus
from app.database.mongodb import get_database
from app.database.repositories import IdentityRepository
from app.core.logging import logger
from app.utils.error_responses import ErrorCode, create_error_response, handle_exception

router = APIRouter(prefix="/identities", tags=["identities"])


@router.get("", response_model=Dict[str, Any])
async def list_identities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    status_filter: str = Query(None, description="Filter by status"),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    List all identities with pagination
    
    Returns paginated list of identities
    """
    try:
        skip = (page - 1) * page_size
        
        # Build query
        query = {}
        if status_filter:
            query["status"] = status_filter
        
        # Get total count
        total = await db.identities.count_documents(query)
        
        # Get identities
        cursor = db.identities.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        
        identities = []
        async for doc in cursor:
            # Get application count for this identity
            app_count = len(doc.get("application_ids", []))
            
            identities.append({
                "unique_id": doc.get("unique_id"),
                "status": doc.get("status"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "application_count": app_count
            })
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": identities,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error listing identities: {str(e)}")
        error_response = handle_exception(e, context="list_identities")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.get("/{unique_id}/applications", response_model=List[Dict[str, Any]])
async def get_identity_applications(
    unique_id: str,
    db=Depends(get_database)
) -> List[Dict[str, Any]]:
    """
    Get all applications for a specific identity
    
    Returns list of applications associated with this identity
    """
    try:
        identity_repo = IdentityRepository(db)
        identity = await identity_repo.get_by_unique_id(unique_id)
        
        if not identity:
            error_response = create_error_response(
                ErrorCode.E203,
                details={"unique_id": unique_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response.dict()
            )
        
        # Get associated applications
        applications = []
        for app_id in identity.application_ids:
            app_doc = await db.applications.find_one({"application_id": app_id})
            if app_doc:
                applications.append({
                    "application_id": app_doc.get("application_id"),
                    "status": app_doc.get("processing", {}).get("status"),
                    "created_at": app_doc.get("created_at").isoformat() if app_doc.get("created_at") else None,
                    "applicant_name": app_doc.get("applicant_data", {}).get("name"),
                    "applicant_email": app_doc.get("applicant_data", {}).get("email"),
                    "is_duplicate": app_doc.get("result", {}).get("is_duplicate", False)
                })
        
        return applications
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting identity applications: {str(e)}")
        error_response = handle_exception(e, context="get_identity_applications")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.get("/{unique_id}", response_model=Dict[str, Any])
async def get_identity(
    unique_id: str,
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Get identity details by unique ID
    
    Returns identity information and associated applications
    """
    try:
        identity_repo = IdentityRepository(db)
        identity = await identity_repo.get_by_unique_id(unique_id)
        
        if not identity:
            error_response = create_error_response(
                ErrorCode.E203,
                details={"unique_id": unique_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response.dict()
            )
        
        # Get associated applications
        applications = []
        for app_id in identity.application_ids:
            app_doc = await db.applications.find_one({"application_id": app_id})
            if app_doc:
                applications.append({
                    "application_id": app_doc.get("application_id"),
                    "status": app_doc.get("processing", {}).get("status"),
                    "created_at": app_doc.get("created_at").isoformat() if app_doc.get("created_at") else None,
                    "applicant_name": app_doc.get("applicant_data", {}).get("name")
                })
        
        return {
            "unique_id": identity.unique_id,
            "status": identity.status,
            "created_at": identity.created_at.isoformat(),
            "updated_at": identity.updated_at.isoformat(),
            "application_count": len(identity.application_ids),
            "applications": applications,
            "metadata": identity.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting identity: {str(e)}")
        error_response = handle_exception(e, context="get_identity")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

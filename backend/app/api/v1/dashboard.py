"""Dashboard API endpoints for statistics and overview"""

from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.database.mongodb import get_database
from app.models.application import ApplicationStatus
from app.core.logging import logger

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/statistics")
async def get_dashboard_statistics(db=Depends(get_database)) -> Dict[str, Any]:
    """
    Get dashboard statistics
    
    Returns:
    - Total applications
    - Total identities
    - Duplicate count
    - Processing status breakdown
    """
    try:
        # Get total applications
        total_applications = await db.applications.count_documents({})
        
        # Get total identities
        total_identities = await db.identities.count_documents({})
        
        # Get duplicate count
        duplicate_count = await db.applications.count_documents({"result.is_duplicate": True})
        
        # Get status breakdown
        pending = await db.applications.count_documents({"processing.status": ApplicationStatus.PENDING})
        processing = await db.applications.count_documents({"processing.status": ApplicationStatus.PROCESSING})
        verified = await db.applications.count_documents({"processing.status": ApplicationStatus.VERIFIED})
        duplicate = await db.applications.count_documents({"processing.status": ApplicationStatus.DUPLICATE})
        rejected = await db.applications.count_documents({"processing.status": ApplicationStatus.REJECTED})
        failed = await db.applications.count_documents({"processing.status": ApplicationStatus.FAILED})
        
        return {
            "total_applications": total_applications,
            "total_identities": total_identities,
            "duplicate_count": duplicate_count,
            "unique_count": total_applications - duplicate_count,
            "status_breakdown": {
                "pending": pending,
                "processing": processing,
                "verified": verified,
                "duplicate": duplicate,
                "rejected": rejected,
                "failed": failed
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {str(e)}")
        return {
            "total_applications": 0,
            "total_identities": 0,
            "duplicate_count": 0,
            "unique_count": 0,
            "status_breakdown": {
                "pending": 0,
                "processing": 0,
                "verified": 0,
                "duplicate": 0,
                "rejected": 0,
                "failed": 0
            }
        }


@router.get("/timeline")
async def get_dashboard_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db=Depends(get_database)
) -> List[Dict[str, Any]]:
    """
    Get timeline data for dashboard charts
    
    Returns daily application submission counts
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Aggregate by day
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1},
                    "duplicates": {
                        "$sum": {
                            "$cond": [{"$eq": ["$result.is_duplicate", True]}, 1, 0]
                        }
                    }
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = await db.applications.aggregate(pipeline).to_list(length=days)
        
        # Format response
        timeline = []
        for result in results:
            timeline.append({
                "date": result["_id"],
                "total": result["count"],
                "duplicates": result["duplicates"],
                "unique": result["count"] - result["duplicates"]
            })
        
        return timeline
    except Exception as e:
        logger.error(f"Error getting dashboard timeline: {str(e)}")
        return []


@router.get("/recent-applications")
async def get_recent_applications(
    limit: int = Query(10, ge=1, le=50, description="Number of recent applications"),
    db=Depends(get_database)
) -> List[Dict[str, Any]]:
    """
    Get recent applications for dashboard
    
    Returns most recent applications with basic info
    """
    try:
        cursor = db.applications.find({}).sort("created_at", -1).limit(limit)
        
        applications = []
        async for doc in cursor:
            applications.append({
                "application_id": doc.get("application_id"),
                "status": doc.get("processing", {}).get("status"),
                "is_duplicate": doc.get("result", {}).get("is_duplicate", False),
                "identity_id": doc.get("result", {}).get("identity_id"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "applicant_name": doc.get("applicant_data", {}).get("name")
            })
        
        return applications
    except Exception as e:
        logger.error(f"Error getting recent applications: {str(e)}")
        return []

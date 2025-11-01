"""Superadmin service for managing admin users"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import logger
from app.database.repositories import UserRepository, ApplicationRepository, AuditLogRepository
from app.models.user import User, UserCreate, UserRole
from app.models.audit import EventType, ActorType, ResourceType
from app.services.audit_service import audit_service
from app.services.auth_service import auth_service


class SuperadminService:
    """Service for superadmin operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.user_repo = UserRepository(db)
        self.app_repo = ApplicationRepository(db)
        self.audit_repo = AuditLogRepository(db)
        logger.info("Superadmin service initialized")
    
    async def get_admin_users(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get paginated list of admin users with search and filters
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Search query for username, email, or full name
            role: Filter by role
            is_active: Filter by active status
            created_after: Filter by creation date (after)
            created_before: Filter by creation date (before)
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
            
        Returns:
            Tuple of (list of users with application counts, total count)
        """
        try:
            # Build query
            query = {}
            
            # Search filter
            if search:
                query["$or"] = [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"full_name": {"$regex": search, "$options": "i"}}
                ]
            
            # Role filter
            if role:
                query["roles"] = role
            
            # Active status filter
            if is_active is not None:
                query["is_active"] = is_active
            
            # Date range filter
            if created_after or created_before:
                query["created_at"] = {}
                if created_after:
                    query["created_at"]["$gte"] = created_after
                if created_before:
                    query["created_at"]["$lte"] = created_before
            
            # Get total count
            total = await self.db.users.count_documents(query)
            
            # Calculate skip
            skip = (page - 1) * page_size
            
            # Sort direction
            sort_direction = -1 if sort_order == "desc" else 1
            
            # Get users with application count aggregation
            pipeline = [
                {"$match": query},
                {"$sort": {sort_by: sort_direction}},
                {"$skip": skip},
                {"$limit": page_size},
                {
                    "$lookup": {
                        "from": "applications",
                        "let": {"username": "$username"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": ["$processing.processed_by", "$$username"]
                                    }
                                }
                            },
                            {"$count": "count"}
                        ],
                        "as": "app_count"
                    }
                },
                {
                    "$addFields": {
                        "application_count": {
                            "$ifNull": [
                                {"$arrayElemAt": ["$app_count.count", 0]},
                                0
                            ]
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "username": 1,
                        "email": 1,
                        "full_name": 1,
                        "roles": 1,
                        "is_active": 1,
                        "created_at": 1,
                        "updated_at": 1,
                        "last_login": 1,
                        "application_count": 1
                    }
                }
            ]
            
            users = []
            async for doc in self.db.users.aggregate(pipeline):
                users.append(doc)
            
            logger.info(f"Retrieved {len(users)} admin users (page {page}, total {total})")
            return users, total
            
        except Exception as e:
            logger.error(f"Failed to get admin users: {str(e)}")
            raise

    async def get_admin_user_stats(self, username: str) -> Dict[str, Any]:
        """
        Get statistics for a specific admin user
        
        Args:
            username: Username of the admin user
            
        Returns:
            Dictionary with user statistics
        """
        try:
            # Get user
            user = await self.user_repo.get_by_username(username)
            if not user:
                raise ValueError(f"User {username} not found")
            
            # Calculate date 30 days ago
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # Get applications by status
            applications_pipeline = [
                {
                    "$match": {
                        "processing.processed_by": username
                    }
                },
                {
                    "$group": {
                        "_id": "$processing.status",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            applications_by_status = {}
            async for doc in self.db.applications.aggregate(applications_pipeline):
                applications_by_status[doc["_id"]] = doc["count"]
            
            total_applications = sum(applications_by_status.values())
            
            # Get applications in last 30 days
            last_30_days_pipeline = [
                {
                    "$match": {
                        "processing.processed_by": username,
                        "created_at": {"$gte": thirty_days_ago}
                    }
                },
                {"$count": "count"}
            ]
            
            last_30_days_result = await self.db.applications.aggregate(last_30_days_pipeline).to_list(1)
            last_30_days_total = last_30_days_result[0]["count"] if last_30_days_result else 0
            
            # Get override decisions from audit logs
            override_pipeline = [
                {
                    "$match": {
                        "actor_id": username,
                        "event_type": {"$in": ["DUPLICATE_OVERRIDE", "MANUAL_OVERRIDE", "OVERRIDE_DECISION"]}
                    }
                },
                {
                    "$group": {
                        "_id": "$details.decision",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            overrides_by_decision = {}
            total_overrides = 0
            async for doc in self.db.audit_logs.aggregate(override_pipeline):
                decision = doc["_id"] or "unknown"
                count = doc["count"]
                overrides_by_decision[decision] = count
                total_overrides += count
            
            # Generate 30-day activity timeline
            activity_pipeline = [
                {
                    "$match": {
                        "processing.processed_by": username,
                        "created_at": {"$gte": thirty_days_ago}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$created_at"
                                }
                            },
                            "status": "$processing.status"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.date": 1}}
            ]
            
            activity_timeline = []
            activity_by_date = {}
            
            async for doc in self.db.applications.aggregate(activity_pipeline):
                date = doc["_id"]["date"]
                status = doc["_id"]["status"]
                count = doc["count"]
                
                if date not in activity_by_date:
                    activity_by_date[date] = {
                        "date": date,
                        "applications_processed": 0,
                        "verified": 0,
                        "duplicate": 0,
                        "rejected": 0
                    }
                
                activity_by_date[date]["applications_processed"] += count
                
                if status == "verified":
                    activity_by_date[date]["verified"] = count
                elif status == "duplicate":
                    activity_by_date[date]["duplicate"] = count
                elif status == "rejected":
                    activity_by_date[date]["rejected"] = count
            
            activity_timeline = list(activity_by_date.values())
            
            stats = {
                "username": username,
                "total_applications": total_applications,
                "applications_by_status": applications_by_status,
                "total_overrides": total_overrides,
                "overrides_by_decision": overrides_by_decision,
                "activity_timeline": activity_timeline,
                "last_30_days_total": last_30_days_total
            }
            
            logger.info(f"Retrieved stats for admin user: {username}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get admin user stats: {str(e)}")
            raise
    
    async def get_aggregate_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics for all admin users
        
        Returns:
            Dictionary with aggregate statistics
        """
        try:
            # Get total active/inactive users
            total_admin_users = await self.db.users.count_documents({})
            active_admin_users = await self.db.users.count_documents({"is_active": True})
            inactive_admin_users = total_admin_users - active_admin_users
            
            # Get users by role breakdown
            role_pipeline = [
                {"$unwind": "$roles"},
                {
                    "$group": {
                        "_id": "$roles",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            users_by_role = {}
            async for doc in self.db.users.aggregate(role_pipeline):
                users_by_role[doc["_id"]] = doc["count"]
            
            # Get total applications in last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            total_applications_last_30_days = await self.db.applications.count_documents({
                "created_at": {"$gte": thirty_days_ago}
            })
            
            # Get most active users (top 5)
            most_active_pipeline = [
                {
                    "$match": {
                        "processing.processed_by": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$processing.processed_by",
                        "application_count": {"$sum": 1}
                    }
                },
                {"$sort": {"application_count": -1}},
                {"$limit": 5},
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "_id",
                        "foreignField": "username",
                        "as": "user"
                    }
                },
                {
                    "$project": {
                        "username": "$_id",
                        "full_name": {"$arrayElemAt": ["$user.full_name", 0]},
                        "application_count": 1
                    }
                }
            ]
            
            most_active_users = []
            async for doc in self.db.applications.aggregate(most_active_pipeline):
                most_active_users.append({
                    "username": doc["username"],
                    "full_name": doc.get("full_name", "Unknown"),
                    "application_count": doc["application_count"]
                })
            
            stats = {
                "total_admin_users": total_admin_users,
                "active_admin_users": active_admin_users,
                "inactive_admin_users": inactive_admin_users,
                "users_by_role": users_by_role,
                "total_applications_last_30_days": total_applications_last_30_days,
                "most_active_users": most_active_users
            }
            
            logger.info("Retrieved aggregate admin statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get aggregate stats: {str(e)}")
            raise

    async def create_admin_user(
        self,
        user_data: UserCreate,
        created_by: str
    ) -> User:
        """
        Create a new admin user and log the action
        
        Args:
            user_data: User creation data
            created_by: Username of the superadmin creating the user
            
        Returns:
            Created user
        """
        try:
            # Check if username already exists
            existing_user = await self.user_repo.get_by_username(user_data.username)
            if existing_user:
                raise ValueError(f"Username {user_data.username} already exists")
            
            # Hash password
            hashed_password = auth_service.get_password_hash(user_data.password)
            
            # Create user
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                roles=user_data.roles,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database
            await self.user_repo.create(user)
            
            # Log creation event
            await audit_service.create_audit_log(
                db=self.db,
                event_type=EventType.DATA_ACCESS,
                actor_id=created_by,
                actor_type=ActorType.ADMIN,
                resource_id=user_data.username,
                resource_type=ResourceType.USER,
                action=f"Created admin user: {user_data.username}",
                details={
                    "username": user_data.username,
                    "email": user_data.email,
                    "full_name": user_data.full_name,
                    "roles": [role.value for role in user_data.roles]
                },
                success=True
            )
            
            logger.info(f"Created admin user: {user_data.username} by {created_by}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create admin user: {str(e)}")
            raise
    
    async def update_admin_user(
        self,
        username: str,
        update_data: Dict[str, Any],
        updated_by: str
    ) -> User:
        """
        Update admin user and log the action
        
        Args:
            username: Username of the user to update
            update_data: Dictionary with fields to update
            updated_by: Username of the superadmin updating the user
            
        Returns:
            Updated user
        """
        try:
            # Get existing user
            user = await self.user_repo.get_by_username(username)
            if not user:
                raise ValueError(f"User {username} not found")
            
            # Prevent self-modification of active status
            if username == updated_by and "is_active" in update_data:
                raise ValueError("Cannot modify your own active status")
            
            # Track changed fields
            changed_fields = {}
            for key, value in update_data.items():
                if hasattr(user, key) and getattr(user, key) != value:
                    changed_fields[key] = {
                        "old": getattr(user, key),
                        "new": value
                    }
            
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update user
            await self.user_repo.update(username, update_data)
            
            # Log modification event
            await audit_service.create_audit_log(
                db=self.db,
                event_type=EventType.DATA_ACCESS,
                actor_id=updated_by,
                actor_type=ActorType.ADMIN,
                resource_id=username,
                resource_type=ResourceType.USER,
                action=f"Updated admin user: {username}",
                details={
                    "username": username,
                    "changed_fields": changed_fields
                },
                success=True
            )
            
            # Get updated user
            updated_user = await self.user_repo.get_by_username(username)
            
            logger.info(f"Updated admin user: {username} by {updated_by}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to update admin user: {str(e)}")
            raise
    
    async def deactivate_admin_user(
        self,
        username: str,
        deactivated_by: str
    ) -> bool:
        """
        Deactivate admin user and log the action
        
        Args:
            username: Username of the user to deactivate
            deactivated_by: Username of the superadmin deactivating the user
            
        Returns:
            True if successful
        """
        try:
            # Prevent self-deactivation
            if username == deactivated_by:
                raise ValueError("Cannot deactivate your own account")
            
            # Get user
            user = await self.user_repo.get_by_username(username)
            if not user:
                raise ValueError(f"User {username} not found")
            
            # Deactivate user
            await self.user_repo.update(username, {
                "is_active": False,
                "updated_at": datetime.utcnow()
            })
            
            # Log deactivation event
            await audit_service.create_audit_log(
                db=self.db,
                event_type=EventType.DATA_ACCESS,
                actor_id=deactivated_by,
                actor_type=ActorType.ADMIN,
                resource_id=username,
                resource_type=ResourceType.USER,
                action=f"Deactivated admin user: {username}",
                details={
                    "username": username,
                    "deactivated_by": deactivated_by
                },
                success=True
            )
            
            logger.info(f"Deactivated admin user: {username} by {deactivated_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate admin user: {str(e)}")
            raise

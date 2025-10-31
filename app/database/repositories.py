"""Database repository classes for CRUD operations"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from app.models.application import Application, ApplicationStatus
from app.models.identity import Identity, IdentityEmbedding, IdentityStatus
from app.models.audit import AuditLog, EventType
from app.models.user import User
from app.core.logging import logger


class ApplicationRepository:
    """Repository for application CRUD operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.applications
    
    async def create(self, application: Application) -> str:
        """Create a new application"""
        try:
            application_dict = application.model_dump()
            result = await self.collection.insert_one(application_dict)
            logger.info(f"Created application: {application.application_id}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.error(f"Duplicate application_id: {application.application_id}")
            raise ValueError(f"Application with ID {application.application_id} already exists")
    
    async def get_by_id(self, application_id: str) -> Optional[Application]:
        """Get application by ID"""
        doc = await self.collection.find_one({"application_id": application_id})
        if doc:
            doc.pop("_id", None)
            return Application(**doc)
        return None
    
    async def update_status(self, application_id: str, status: ApplicationStatus, 
                           error_code: Optional[str] = None, 
                           error_message: Optional[str] = None) -> bool:
        """Update application processing status"""
        update_data = {
            "processing.status": status,
            "updated_at": datetime.utcnow()
        }
        
        if error_code:
            update_data["processing.error_code"] = error_code
        if error_message:
            update_data["processing.error_message"] = error_message
        
        result = await self.collection.update_one(
            {"application_id": application_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def update_processing_metadata(self, application_id: str, 
                                        metadata: Dict[str, Any]) -> bool:
        """Update processing metadata"""
        update_data = {f"processing.{k}": v for k, v in metadata.items()}
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"application_id": application_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def update_result(self, application_id: str, result_data: Dict[str, Any]) -> bool:
        """Update application result"""
        update_data = {f"result.{k}": v for k, v in result_data.items()}
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"application_id": application_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def get_by_status(self, status: ApplicationStatus, 
                           limit: int = 100, skip: int = 0) -> List[Application]:
        """Get applications by status"""
        cursor = self.collection.find({"processing.status": status}).skip(skip).limit(limit)
        applications = []
        async for doc in cursor:
            doc.pop("_id", None)
            applications.append(Application(**doc))
        return applications
    
    async def get_by_identity_id(self, identity_id: str) -> List[Application]:
        """Get all applications for an identity"""
        cursor = self.collection.find({"result.identity_id": identity_id})
        applications = []
        async for doc in cursor:
            doc.pop("_id", None)
            applications.append(Application(**doc))
        return applications
    
    async def update_processing_status(self, application_id: str, status: ApplicationStatus,
                                      processing_started_at: Optional[datetime] = None) -> bool:
        """Update application processing status and start time"""
        update_data = {
            "processing.status": status,
            "updated_at": datetime.utcnow()
        }
        
        if processing_started_at:
            update_data["processing.processing_started_at"] = processing_started_at
        
        result = await self.collection.update_one(
            {"application_id": application_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def update_face_recognition_results(self, application_id: str, embedding: List[float],
                                             bounding_box: Dict[str, int], quality_score: float,
                                             face_detected: bool) -> bool:
        """Update application with face recognition results"""
        update_data = {
            "processing.face_detected": face_detected,
            "processing.quality_score": quality_score,
            "processing.embedding_generated": True,
            "processing.processing_completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {"application_id": application_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def update_processing_error(self, application_id: str, status: ApplicationStatus,
                                     error_code: str, error_message: str) -> bool:
        """Update application with processing error"""
        update_data = {
            "processing.status": status,
            "processing.error_code": error_code,
            "processing.error_message": error_message,
            "processing.processing_completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {"application_id": application_id},
            {"$set": update_data}
        )
        return result.modified_count > 0


class IdentityRepository:
    """Repository for identity CRUD operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.identities
    
    async def create(self, identity: Identity) -> str:
        """Create a new identity"""
        try:
            identity_dict = identity.model_dump()
            result = await self.collection.insert_one(identity_dict)
            logger.info(f"Created identity: {identity.unique_id}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.error(f"Duplicate unique_id: {identity.unique_id}")
            raise ValueError(f"Identity with ID {identity.unique_id} already exists")
    
    async def get_by_unique_id(self, unique_id: str) -> Optional[Identity]:
        """Get identity by unique ID"""
        doc = await self.collection.find_one({"unique_id": unique_id})
        if doc:
            doc.pop("_id", None)
            return Identity(**doc)
        return None
    
    async def update_status(self, unique_id: str, status: IdentityStatus) -> bool:
        """Update identity status"""
        result = await self.collection.update_one(
            {"unique_id": unique_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def add_application_id(self, unique_id: str, application_id: str) -> bool:
        """Add application ID to identity"""
        result = await self.collection.update_one(
            {"unique_id": unique_id},
            {
                "$addToSet": {"application_ids": application_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    async def update_metadata(self, unique_id: str, metadata: Dict[str, Any]) -> bool:
        """Update identity metadata"""
        result = await self.collection.update_one(
            {"unique_id": unique_id},
            {
                "$set": {
                    "metadata": metadata,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0


class EmbeddingRepository:
    """Repository for embedding CRUD operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.identity_embeddings
    
    async def create(self, embedding: IdentityEmbedding) -> str:
        """Create a new embedding"""
        try:
            embedding_dict = embedding.model_dump()
            result = await self.collection.insert_one(embedding_dict)
            logger.info(f"Created embedding for application: {embedding.application_id}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.error(f"Duplicate embedding for application_id: {embedding.application_id}")
            raise ValueError(f"Embedding for application {embedding.application_id} already exists")
    
    async def get_by_application_id(self, application_id: str) -> Optional[IdentityEmbedding]:
        """Get embedding by application ID"""
        doc = await self.collection.find_one({"application_id": application_id})
        if doc:
            doc.pop("_id", None)
            return IdentityEmbedding(**doc)
        return None
    
    async def get_by_identity_id(self, identity_id: str) -> List[IdentityEmbedding]:
        """Get all embeddings for an identity"""
        cursor = self.collection.find({"identity_id": identity_id})
        embeddings = []
        async for doc in cursor:
            doc.pop("_id", None)
            embeddings.append(IdentityEmbedding(**doc))
        return embeddings


class AuditLogRepository:
    """Repository for audit log operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.audit_logs
    
    async def create(self, audit_log: AuditLog) -> str:
        """Create a new audit log entry"""
        audit_dict = audit_log.model_dump()
        result = await self.collection.insert_one(audit_dict)
        return str(result.inserted_id)
    
    async def get_by_event_type(self, event_type: EventType, 
                                limit: int = 100, skip: int = 0) -> List[AuditLog]:
        """Get audit logs by event type"""
        cursor = self.collection.find({"event_type": event_type}).sort("timestamp", -1).skip(skip).limit(limit)
        logs = []
        async for doc in cursor:
            doc.pop("_id", None)
            logs.append(AuditLog(**doc))
        return logs
    
    async def get_by_resource_id(self, resource_id: str, 
                                 limit: int = 100, skip: int = 0) -> List[AuditLog]:
        """Get audit logs by resource ID"""
        cursor = self.collection.find({"resource_id": resource_id}).sort("timestamp", -1).skip(skip).limit(limit)
        logs = []
        async for doc in cursor:
            doc.pop("_id", None)
            logs.append(AuditLog(**doc))
        return logs
    
    async def query(self, filters: Dict[str, Any], 
                   limit: int = 100, skip: int = 0) -> tuple[List[AuditLog], int]:
        """Query audit logs with filters"""
        # Build query
        query = {}
        if "event_type" in filters:
            query["event_type"] = filters["event_type"]
        if "actor_id" in filters:
            query["actor_id"] = filters["actor_id"]
        if "resource_id" in filters:
            query["resource_id"] = filters["resource_id"]
        if "start_date" in filters or "end_date" in filters:
            query["timestamp"] = {}
            if "start_date" in filters:
                query["timestamp"]["$gte"] = filters["start_date"]
            if "end_date" in filters:
                query["timestamp"]["$lte"] = filters["end_date"]
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Get logs
        cursor = self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        logs = []
        async for doc in cursor:
            doc.pop("_id", None)
            logs.append(AuditLog(**doc))
        
        return logs, total


class UserRepository:
    """Repository for user CRUD operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.users
    
    async def create(self, user: User) -> str:
        """Create a new user"""
        try:
            user_dict = user.model_dump()
            result = await self.collection.insert_one(user_dict)
            logger.info(f"Created user: {user.username}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.error(f"Duplicate username or email: {user.username}")
            raise ValueError(f"User with username {user.username} already exists")
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        doc = await self.collection.find_one({"username": username})
        if doc:
            doc.pop("_id", None)
            return User(**doc)
        return None
    
    async def update_last_login(self, username: str) -> bool:
        """Update user's last login timestamp"""
        result = await self.collection.update_one(
            {"username": username},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return result.modified_count > 0

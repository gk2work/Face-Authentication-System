"""MongoDB connection manager with connection pooling and error handling"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import asyncio
from app.core.config import settings
from app.core.logging import logger


class MongoDBManager:
    """MongoDB connection manager with connection pooling"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self._connection_retries = 3
        self._retry_delay = 2  # seconds
    
    async def connect(self):
        """Establish connection to MongoDB with retry logic"""
        for attempt in range(self._connection_retries):
            try:
                logger.info(f"Attempting MongoDB connection (attempt {attempt + 1}/{self._connection_retries})")
                
                # Create client with connection pooling
                self.client = AsyncIOMotorClient(
                    settings.MONGODB_URI,
                    maxPoolSize=50,
                    minPoolSize=10,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    retryWrites=True,
                )
                
                # Verify connection
                await self.client.admin.command('ping')
                
                # Get database
                self.db = self.client[settings.MONGODB_DATABASE]
                
                logger.info(f"Successfully connected to MongoDB: {settings.MONGODB_DATABASE}")
                
                # Initialize collections and indexes
                await self._initialize_collections()
                
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"MongoDB connection attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self._connection_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                else:
                    logger.error("Failed to connect to MongoDB after all retries")
                    raise
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def _initialize_collections(self):
        """Initialize collections and create indexes"""
        try:
            # Create indexes for applications collection
            await self.db.applications.create_index("application_id", unique=True)
            await self.db.applications.create_index("identity_id")
            await self.db.applications.create_index("status")
            await self.db.applications.create_index("created_at")
            await self.db.applications.create_index([("status", 1), ("created_at", -1)])
            
            # Compound indexes for frequently queried fields (performance optimization)
            await self.db.applications.create_index([("processing.status", 1), ("created_at", -1)])
            await self.db.applications.create_index([("result.identity_id", 1), ("created_at", -1)])
            await self.db.applications.create_index([("processing.status", 1), ("result.is_duplicate", 1)])
            
            # Create indexes for identities collection
            await self.db.identities.create_index("unique_id", unique=True)
            await self.db.identities.create_index("status")
            await self.db.identities.create_index("created_at")
            
            # Compound index for identity queries
            await self.db.identities.create_index([("status", 1), ("created_at", -1)])
            
            # Create indexes for identity_embeddings collection
            await self.db.identity_embeddings.create_index("identity_id")
            await self.db.identity_embeddings.create_index("application_id", unique=True)
            await self.db.identity_embeddings.create_index("created_at")
            
            # Compound index for embedding queries
            await self.db.identity_embeddings.create_index([("identity_id", 1), ("created_at", -1)])
            
            # Create indexes for audit_logs collection
            await self.db.audit_logs.create_index("event_type")
            await self.db.audit_logs.create_index("actor_id")
            await self.db.audit_logs.create_index("resource_id")
            await self.db.audit_logs.create_index("timestamp")
            await self.db.audit_logs.create_index([("event_type", 1), ("timestamp", -1)])
            
            # Compound indexes for audit log queries
            await self.db.audit_logs.create_index([("resource_id", 1), ("timestamp", -1)])
            await self.db.audit_logs.create_index([("actor_id", 1), ("event_type", 1), ("timestamp", -1)])
            
            # Create indexes for users collection (for authentication)
            await self.db.users.create_index("username", unique=True)
            await self.db.users.create_index("email", unique=True)
            
            logger.info("MongoDB indexes created successfully (including compound indexes for performance)")
            
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {str(e)}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection"""
        if not self.db:
            raise RuntimeError("MongoDB not connected")
        return self.db[collection_name]
    
    async def health_check(self) -> bool:
        """Check if MongoDB connection is healthy"""
        try:
            if not self.client:
                return False
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            return False


# Global MongoDB manager instance
mongodb_manager = MongoDBManager()


async def get_database():
    """Dependency to get database instance"""
    if not mongodb_manager.db:
        await mongodb_manager.connect()
    return mongodb_manager.db

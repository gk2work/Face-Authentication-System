"""Embedding cache service for performance optimization"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
import json

from app.core.config import settings
from app.core.logging import logger


class EmbeddingCacheService:
    """Service for caching facial embeddings"""
    
    def __init__(self):
        self.cache_ttl = settings.CACHE_TTL  # 1 hour default
        self.use_redis = False
        self.redis_client = None
        self.local_cache: Dict[str, Dict[str, Any]] = {}
        
        # Try to connect to Redis
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Embedding cache using Redis")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {str(e)}")
            self.use_redis = False
    
    def _generate_cache_key(self, application_id: str) -> str:
        """
        Generate cache key for application
        
        Args:
            application_id: Application identifier
            
        Returns:
            Cache key string
        """
        return f"embedding:{application_id}"
    
    def _is_expired(self, cached_at: float) -> bool:
        """
        Check if cache entry is expired
        
        Args:
            cached_at: Timestamp when entry was cached
            
        Returns:
            True if expired, False otherwise
        """
        age = time.time() - cached_at
        return age > self.cache_ttl
    
    async def get(self, application_id: str) -> Optional[List[float]]:
        """
        Get embedding from cache
        
        Args:
            application_id: Application identifier
            
        Returns:
            Embedding vector or None if not found/expired
        """
        cache_key = self._generate_cache_key(application_id)
        
        try:
            if self.use_redis:
                # Get from Redis
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    embedding = json.loads(cached_data)
                    logger.debug(f"Cache hit (Redis): {application_id}")
                    return embedding
            else:
                # Get from local cache
                if cache_key in self.local_cache:
                    cached_entry = self.local_cache[cache_key]
                    
                    # Check if expired
                    if not self._is_expired(cached_entry["cached_at"]):
                        logger.debug(f"Cache hit (local): {application_id}")
                        return cached_entry["embedding"]
                    else:
                        # Remove expired entry
                        del self.local_cache[cache_key]
                        logger.debug(f"Cache expired: {application_id}")
            
            logger.debug(f"Cache miss: {application_id}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, application_id: str, embedding: List[float]) -> bool:
        """
        Store embedding in cache
        
        Args:
            application_id: Application identifier
            embedding: Embedding vector to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        cache_key = self._generate_cache_key(application_id)
        
        try:
            if self.use_redis:
                # Store in Redis with TTL
                cached_data = json.dumps(embedding)
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    cached_data
                )
                logger.debug(f"Cached in Redis: {application_id}")
            else:
                # Store in local cache
                self.local_cache[cache_key] = {
                    "embedding": embedding,
                    "cached_at": time.time()
                }
                logger.debug(f"Cached locally: {application_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, application_id: str) -> bool:
        """
        Delete embedding from cache
        
        Args:
            application_id: Application identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        cache_key = self._generate_cache_key(application_id)
        
        try:
            if self.use_redis:
                self.redis_client.delete(cache_key)
            else:
                if cache_key in self.local_cache:
                    del self.local_cache[cache_key]
            
            logger.debug(f"Cache deleted: {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    async def clear(self) -> int:
        """
        Clear all cached embeddings
        
        Returns:
            Number of entries cleared
        """
        try:
            if self.use_redis:
                # Delete all embedding keys
                pattern = "embedding:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
                    logger.info(f"Cleared {count} entries from Redis cache")
                    return count
                return 0
            else:
                count = len(self.local_cache)
                self.local_cache.clear()
                logger.info(f"Cleared {count} entries from local cache")
                return count
                
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            if self.use_redis:
                # Get Redis info
                info = self.redis_client.info("stats")
                pattern = "embedding:*"
                key_count = len(self.redis_client.keys(pattern))
                
                return {
                    "cache_type": "redis",
                    "entry_count": key_count,
                    "ttl_seconds": self.cache_ttl,
                    "redis_connected": True
                }
            else:
                # Clean expired entries first
                expired_keys = [
                    key for key, entry in self.local_cache.items()
                    if self._is_expired(entry["cached_at"])
                ]
                for key in expired_keys:
                    del self.local_cache[key]
                
                return {
                    "cache_type": "local",
                    "entry_count": len(self.local_cache),
                    "ttl_seconds": self.cache_ttl,
                    "redis_connected": False
                }
                
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {
                "cache_type": "unknown",
                "entry_count": 0,
                "error": str(e)
            }


# Global embedding cache service instance
embedding_cache_service = EmbeddingCacheService()

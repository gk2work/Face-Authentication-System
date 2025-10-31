"""Simple in-memory cache service with TTL support"""

import time
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from app.core.logging import logger


class CacheEntry:
    """Cache entry with TTL support"""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expiry_time = time.time() + ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > self.expiry_time


class SimpleCacheService:
    """Simple in-memory cache with TTL support for read-heavy operations"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache service
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(f"Cache service initialized with default TTL: {default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            self._evictions += 1
            return None
        
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        self._cache[key] = CacheEntry(value, ttl_seconds)
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._evictions += 1
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        self._hits = 0
        self._misses = 0
        self._evictions = 0


# Global cache service instance
cache_service = SimpleCacheService(default_ttl=3600)  # 1 hour default TTL

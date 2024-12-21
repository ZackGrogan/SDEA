from functools import lru_cache
import redis
from typing import Any, Optional, Dict, Union
import json
from datetime import datetime, timedelta
from .logger import cache_logger

class CacheManager:
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        """Initialize cache manager with Redis and in-memory LRU cache"""
        try:
            self.redis_client = redis.from_url(redis_url)
            self._initialize_cache()
        except Exception as e:
            cache_logger.warning(f"Redis connection failed: {e}. Using in-memory cache only.")
            self.redis_client = None
    
    def _initialize_cache(self):
        """Initialize cache settings"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                cache_logger.info("Redis cache initialized successfully")
        except redis.ConnectionError as e:
            cache_logger.warning(f"Redis connection failed: {str(e)}. Using in-memory cache only.")
            self.redis_client = None
    
    @lru_cache(maxsize=1000)
    def get_cached_filing(self, filing_id: str) -> Optional[Dict]:
        """Get filing from cache"""
        return self._get_from_redis(f"filing:{filing_id}")
    
    @lru_cache(maxsize=100)
    def get_cached_market_data(self, ticker: str) -> Optional[Dict]:
        """Get market data from cache"""
        return self._get_from_redis(f"market:{ticker}")
    
    def _get_from_redis(self, key: str) -> Optional[Dict]:
        """Get data from Redis with error handling"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except (redis.RedisError, json.JSONDecodeError) as e:
            cache_logger.error(f"Redis get error for key {key}: {str(e)}")
            return None
    
    def set_cached_filing(self, filing_id: str, data: Dict, expire_seconds: int = 3600):
        """Set filing data in both Redis and LRU cache"""
        self._set_in_redis(f"filing:{filing_id}", data, expire_seconds)
        self.get_cached_filing.cache_clear()  # Clear LRU cache to maintain consistency
    
    def _set_in_redis(self, key: str, data: Dict, expire_seconds: int = 3600):
        """Set data in Redis with error handling"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(key, expire_seconds, json.dumps(data))
        except redis.RedisError as e:
            cache_logger.error(f"Redis set error for key {key}: {str(e)}")

    def delete(self, key: str):
        """Delete a specific key from cache"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(key)
            cache_logger.info(f"Deleted cache key: {key}")
        except redis.RedisError as e:
            cache_logger.error(f"Error deleting cache key {key}: {str(e)}")
    
    def clear_all_caches(self):
        """Clear all caches, including Redis and LRU"""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                cache_logger.info("Cleared entire Redis database")
            except redis.RedisError as e:
                cache_logger.error(f"Error clearing Redis database: {str(e)}")
        
        # Clear LRU caches
        self.get_cached_filing.cache_clear()
        self.get_cached_market_data.cache_clear()
    
    def get(self, key: str, default: Optional[Any] = None) -> Optional[Dict]:
        """
        Generic get method with optional default value
        
        :param key: Cache key to retrieve
        :param default: Default value to return if key not found
        :return: Cached value or default
        """
        result = self._get_from_redis(key)
        return result if result is not None else default
    
    def set(self, key: str, value: Union[Dict, str], expire_seconds: int = 3600):
        """
        Generic set method for caching
        
        :param key: Cache key to set
        :param value: Value to cache
        :param expire_seconds: Expiration time in seconds
        """
        self._set_in_redis(key, value, expire_seconds)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit, close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
            except Exception as e:
                cache_logger.error(f"Error closing Redis connection: {e}")

# Singleton instance for easy import and use
cache_manager = CacheManager()

"""
Caching utilities using Redis.

Provides high-level caching functions for intelligence data,
API responses, and computed results with TTL management.
"""

from flask_redis import FlaskRedis
from typing import Optional, Any, Callable
import json
import hashlib
import pickle
from datetime import timedelta


class CacheManager:
    """
    Redis-based cache manager for Radar application.
    
    Handles caching of intelligence data, API responses, and
    expensive computations with configurable TTLs and invalidation.
    """
    
    def __init__(self, redis_client: FlaskRedis):
        """
        Initialize cache manager with Redis client.
        
        Args:
            redis_client: FlaskRedis client instance
        """
        self.redis = redis_client
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        cached = self.redis.get(key)
        if cached is None:
            return default
        
        try:
            # Try JSON deserialization first
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            # Fall back to pickle for complex objects
            try:
                return pickle.loads(cached)
            except Exception:
                # Return raw string if deserialization fails
                return cached
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_json: bool = True
    ):
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
            use_json: If True, use JSON serialization (faster, limited types)
                     If False, use pickle (slower, supports all types)
        """
        try:
            if use_json:
                serialized = json.dumps(value, default=str)
            else:
                serialized = pickle.dumps(value)
            
            if ttl:
                self.redis.setex(key, ttl, serialized)
            else:
                self.redis.set(key, serialized)
        except (TypeError, ValueError) as e:
            # Fall back to pickle if JSON fails
            if use_json:
                serialized = pickle.dumps(value)
                if ttl:
                    self.redis.setex(key, ttl, serialized)
                else:
                    self.redis.set(key, serialized)
            else:
                raise
    
    def delete(self, key: str):
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
        """
        self.redis.delete(key)
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return self.redis.exists(key) > 0
    
    def get_or_set(
        self,
        key: str,
        callable_func: Callable[[], Any],
        ttl: Optional[int] = None,
        use_json: bool = True
    ) -> Any:
        """
        Get value from cache, or compute and cache if not found.
        
        Useful for caching expensive computations or API calls.
        
        Args:
            key: Cache key
            callable_func: Function to call if cache miss
            ttl: Time to live in seconds
            use_json: Use JSON serialization
            
        Returns:
            Cached or computed value
        """
        cached = self.get(key)
        if cached is not None:
            return cached
        
        value = callable_func()
        self.set(key, value, ttl=ttl, use_json=use_json)
        return value
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., 'intelligence:*')
        """
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Creates consistent, collision-resistant keys from function arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Sort kwargs for consistent ordering
        sorted_kwargs = sorted(kwargs.items())
        
        # Create string representation
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
        key_string = "|".join(key_parts)
        
        # Hash for fixed-length keys
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"cache:{key_hash}"


def cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate cache key with prefix.
    
    Args:
        prefix: Key prefix (e.g., 'intelligence', 'financial')
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    import hashlib
    import json
    
    # Sort kwargs for consistent ordering
    sorted_kwargs = sorted(kwargs.items())
    
    # Create string representation
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
    key_string = "|".join(key_parts)
    
    # Hash for fixed-length keys
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"

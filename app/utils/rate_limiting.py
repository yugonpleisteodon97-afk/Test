"""
Rate limiting utilities using Redis.

Implements token bucket and fixed window rate limiting algorithms
for API endpoints and user actions.
"""

from flask import request, current_app
from flask_redis import FlaskRedis
from typing import Optional, Tuple
import time
import json
from datetime import timedelta


class RateLimiter:
    """
    Redis-based rate limiter implementation.
    
    Supports both token bucket and fixed window algorithms.
    Used for API rate limiting, login attempt limiting, and
    general request throttling.
    """
    
    def __init__(self, redis_client: FlaskRedis):
        """
        Initialize rate limiter with Redis client.
        
        Args:
            redis_client: FlaskRedis client instance
        """
        self.redis = redis_client
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        algorithm: str = 'fixed_window'
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique identifier for rate limit (e.g., user_id, ip_address)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
            algorithm: Rate limiting algorithm ('fixed_window' or 'token_bucket')
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time)
        """
        if algorithm == 'fixed_window':
            return self._fixed_window(key, max_requests, window_seconds)
        elif algorithm == 'token_bucket':
            return self._token_bucket(key, max_requests, window_seconds)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _fixed_window(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        Fixed window rate limiting algorithm.
        
        Simple and efficient, but can allow bursts at window boundaries.
        """
        redis_key = f"ratelimit:fixed:{key}"
        current_time = int(time.time())
        window_start = current_time - (current_time % window_seconds)
        
        # Get current count
        count = self.redis.get(redis_key)
        if count is None:
            count = 0
        else:
            count = int(count)
        
        # Check if limit exceeded
        if count >= max_requests:
            reset_time = window_start + window_seconds
            return False, 0, reset_time
        
        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, window_seconds)
        pipe.execute()
        
        remaining = max(0, max_requests - count - 1)
        reset_time = window_start + window_seconds
        
        return True, remaining, reset_time
    
    def _token_bucket(self, key: str, max_tokens: int, refill_seconds: int) -> Tuple[bool, int, int]:
        """
        Token bucket rate limiting algorithm.
        
        Allows bursts but smooths out traffic over time.
        More complex but better for API rate limiting.
        """
        redis_key = f"ratelimit:bucket:{key}"
        current_time = time.time()
        
        # Get bucket state
        bucket_data = self.redis.get(redis_key)
        if bucket_data:
            bucket = json.loads(bucket_data)
            tokens = bucket['tokens']
            last_refill = bucket['last_refill']
        else:
            tokens = max_tokens
            last_refill = current_time
        
        # Refill tokens based on elapsed time
        elapsed = current_time - last_refill
        refill_rate = max_tokens / refill_seconds
        tokens_to_add = elapsed * refill_rate
        tokens = min(max_tokens, tokens + tokens_to_add)
        last_refill = current_time
        
        # Check if token available
        if tokens < 1:
            reset_time = int(current_time + (1 - tokens) / refill_rate)
            return False, 0, reset_time
        
        # Consume token
        tokens -= 1
        bucket = {
            'tokens': tokens,
            'last_refill': last_refill
        }
        self.redis.setex(
            redis_key,
            refill_seconds * 2,  # Expire after 2x refill window
            json.dumps(bucket)
        )
        
        remaining = int(tokens)
        reset_time = int(current_time + (max_tokens - tokens) / refill_rate)
        
        return True, remaining, reset_time
    
    def reset_rate_limit(self, key: str, algorithm: str = 'fixed_window'):
        """
        Reset rate limit for a key (admin function).
        
        Args:
            key: Rate limit key to reset
            algorithm: Algorithm type ('fixed_window' or 'token_bucket')
        """
        if algorithm == 'fixed_window':
            redis_key = f"ratelimit:fixed:{key}"
        else:
            redis_key = f"ratelimit:bucket:{key}"
        
        self.redis.delete(redis_key)


def get_client_ip() -> str:
    """
    Get client IP address from request.
    
    Handles proxies and forwarded headers correctly.
    
    Returns:
        Client IP address string
    """
    if request.headers.get('X-Forwarded-For'):
        # Get first IP from X-Forwarded-For header
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr or 'unknown'
    
    return ip

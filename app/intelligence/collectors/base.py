"""
Base collector class for intelligence data collection.

All collectors inherit from this base class which provides:
- Rate limiting enforcement
- Error handling and retries (exponential backoff)
- Data validation
- Caching logic (Redis with TTL)
- Confidence scoring
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from app.extensions import redis_client
from app.utils.caching import CacheManager
from app.utils.rate_limiting import RateLimiter
import time
import logging
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for intelligence collectors.
    
    All collectors must implement the collect() method to fetch
    data from their respective APIs or data sources.
    """
    
    def __init__(self, name: str, cache_ttl: int = 3600):
        """
        Initialize collector.
        
        Args:
            name: Collector name (e.g., 'financial', 'patents')
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.name = name
        self.cache_ttl = cache_ttl
        self.cache_manager = CacheManager(redis_client)
        self.rate_limiter = RateLimiter(redis_client)
    
    @abstractmethod
    def collect(self, competitor_id: str, competitor_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float, str]:
        """
        Collect intelligence data for a competitor.
        
        This method must be implemented by all collectors.
        
        Args:
            competitor_id: Competitor ID
            competitor_data: Competitor metadata (name, website_url, etc.)
            
        Returns:
            Tuple of (data, confidence_score, error_message)
            - data: Collected data dictionary or None if failed
            - confidence_score: Confidence score (0-100)
            - error_message: Error message if failed, empty string if successful
        """
        pass
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data if available and not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        return self.cache_manager.get(cache_key)
    
    def cache_data(self, cache_key: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache data with TTL.
        
        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (default: self.cache_ttl)
        """
        ttl = ttl or self.cache_ttl
        self.cache_manager.set(cache_key, data, ttl=ttl)
    
    def execute_with_retry(
        self,
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ) -> Tuple[Optional[Any], bool]:
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds
            backoff_factor: Backoff multiplier
            
        Returns:
            Tuple of (result, success)
        """
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                result = func()
                return result, True
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries exceeded for {self.name}: {str(e)}")
                    return None, False
                
                logger.warning(f"Attempt {attempt + 1} failed for {self.name}: {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= backoff_factor
        
        return None, False
    
    def validate_data(self, data: Dict[str, Any], required_fields: list) -> Tuple[bool, str]:
        """
        Validate collected data has required fields.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not data:
            return False, "Data is None or empty"
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, ""
    
    def calculate_confidence_score(
        self,
        data_quality: float,
        source_reliability: float,
        data_completeness: float
    ) -> float:
        """
        Calculate confidence score from multiple factors.
        
        Args:
            data_quality: Data quality score (0-1)
            source_reliability: Source reliability score (0-1)
            data_completeness: Data completeness score (0-1)
            
        Returns:
            Confidence score (0-100)
        """
        # Weighted average
        score = (
            data_quality * 0.4 +
            source_reliability * 0.4 +
            data_completeness * 0.2
        ) * 100
        
        return min(100, max(0, score))

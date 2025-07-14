
import json
import redis
from typing import List, Optional, Dict, Any
import logging

from ..models.response_models import Suggestion
from ..utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.cache_prefix = "ai_completion:"
        self.default_ttl = 3600  # 1 hour
    
    async def get_cached_suggestions(self, context_hash: str) -> Optional[List[Suggestion]]:
        """Get cached suggestions by context hash"""
        key = f"{self.cache_prefix}{context_hash}"
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                # Update TTL
                self.redis_client.expire(key, self.default_ttl)
                
                # Parse cached data
                suggestions_data = json.loads(cached_data)
                return [Suggestion(**suggestion) for suggestion in suggestions_data]
                
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def cache_suggestions(self, context_hash: str, suggestions: List[Suggestion]):
        """Cache suggestions with TTL"""
        key = f"{self.cache_prefix}{context_hash}"
        
        try:
            # Convert suggestions to dict for JSON serialization
            suggestions_data = [suggestion.dict() for suggestion in suggestions]
            
            self.redis_client.setex(
                key,
                self.default_ttl,
                json.dumps(suggestions_data)
            )
            
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def invalidate_cache(self, pattern: str = "*"):
        """Invalidate cache entries"""
        try:
            keys = self.redis_client.keys(f"{self.cache_prefix}{pattern}")
            if keys:
                self.redis_client.delete(*keys)
                
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
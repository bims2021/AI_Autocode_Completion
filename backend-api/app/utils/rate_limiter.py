
import redis
from typing import Dict, Any
import time
import logging

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB + 1,  # Use different DB for rate limiting
            decode_responses=True
        )
        self.limits = {
            'default': {
                'requests': settings.RATE_LIMIT_REQUESTS,
                'window': settings.RATE_LIMIT_WINDOW
            },
            'premium': {'requests': 1000, 'window': 3600},
            'enterprise': {'requests': 10000, 'window': 3600}
        }
    
    async def check_rate_limit(self, user_id: str, tier: str = 'default') -> Dict[str, Any]:
        """Check if user has exceeded rate limit"""
        if tier not in self.limits:
            tier = 'default'
        
        limit_config = self.limits[tier]
        key = f"rate_limit:{user_id}:{tier}"
        
        try:
            # Get current count
            current_count = self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= limit_config['requests']:
                # Get TTL for reset time
                ttl = self.redis_client.ttl(key)
                return {
                    'allowed': False,
                    'limit': limit_config['requests'],
                    'remaining': 0,
                    'reset_in': ttl if ttl > 0 else limit_config['window']
                }
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, limit_config['window'])
            pipe.execute()
            
            return {
                'allowed': True,
                'limit': limit_config['requests'],
                'remaining': limit_config['requests'] - current_count - 1,
                'reset_in': limit_config['window']
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiter fails
            return {
                'allowed': True,
                'limit': limit_config['requests'],
                'remaining': limit_config['requests'],
                'reset_in': limit_config['window']
            }

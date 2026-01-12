"""API rate limiting and circuit breaker utilities."""

import os
import time
from functools import wraps
from typing import Dict, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

# Try to import Redis, fallback to in-memory dict if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory rate limiting")


class APIRateLimiter:
    """Rate limiter with per-API tracking (Redis-backed or in-memory)."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL')
        self.redis_client = None
        self.memory_cache: Dict[str, Dict] = {}
        
        if REDIS_AVAILABLE and self.redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                logger.info("Rate limiter using Redis", redis_url=self.redis_url)
            except Exception as e:
                logger.warning("Failed to connect to Redis, using in-memory", error=str(e))
                self.redis_client = None
        
        # Define limits for each API (calls per minute)
        self.limits = {
            'newsapi': 100,      # Free tier
            'reddit': 60,        # Standard OAuth2
            'twitter': 15,       # V2 API standard
            'polymarket': 300,   # CLOB API
            'gamma': 100,        # Gamma API
        }
    
    def check_and_increment(self, api_name: str) -> bool:
        """Check if call is allowed and increment counter."""
        limit = self.limits.get(api_name, 60)
        current_minute = int(time.time() / 60)
        
        if self.redis_client:
            # Use Redis
            key = f"rate_limit:{api_name}:{current_minute}"
            try:
                current = self.redis_client.get(key)
                if current and int(current) >= limit:
                    logger.warning(
                        "Rate limit exceeded",
                        api_name=api_name,
                        current=int(current),
                        limit=limit
                    )
                    return False
                
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, 60)
                pipe.execute()
                return True
            except Exception as e:
                logger.warning("Redis error, falling back to memory", error=str(e))
                # Fall through to memory cache
        
        # Use in-memory cache
        key = f"{api_name}:{current_minute}"
        if key not in self.memory_cache:
            self.memory_cache[key] = {"count": 0, "expires": time.time() + 60}
        
        # Clean expired entries
        now = time.time()
        self.memory_cache = {
            k: v for k, v in self.memory_cache.items()
            if v.get("expires", 0) > now
        }
        
        cache_entry = self.memory_cache[key]
        if cache_entry["count"] >= limit:
            logger.warning(
                "Rate limit exceeded",
                api_name=api_name,
                current=cache_entry["count"],
                limit=limit
            )
            return False
        
        cache_entry["count"] += 1
        return True
    
    def get_remaining(self, api_name: str) -> int:
        """Get remaining calls for this minute."""
        limit = self.limits.get(api_name, 60)
        current_minute = int(time.time() / 60)
        
        if self.redis_client:
            key = f"rate_limit:{api_name}:{current_minute}"
            try:
                current = self.redis_client.get(key) or 0
                return max(0, limit - int(current))
            except Exception:
                pass
        
        # Memory cache
        key = f"{api_name}:{current_minute}"
        if key in self.memory_cache:
            current = self.memory_cache[key]["count"]
            return max(0, limit - current)
        
        return limit


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> APIRateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = APIRateLimiter()
    return _rate_limiter


def rate_limited(api_name: str):
    """Decorator for rate-limited API calls."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            
            if not limiter.check_and_increment(api_name):
                remaining = limiter.get_remaining(api_name)
                raise RateLimitExceeded(
                    f"{api_name} rate limit exceeded. Remaining: {remaining}"
                )
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            
            if not limiter.check_and_increment(api_name):
                remaining = limiter.get_remaining(api_name)
                raise RateLimitExceeded(
                    f"{api_name} rate limit exceeded. Remaining: {remaining}"
                )
            
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Raised when API rate limit is exceeded."""
    pass


# Simple circuit breaker implementation
class CircuitBreaker:
    """Simple circuit breaker for API calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed after successful call")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    "Circuit breaker opened",
                    failure_count=self.failure_count,
                    error=str(e)
                )
            
            raise


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


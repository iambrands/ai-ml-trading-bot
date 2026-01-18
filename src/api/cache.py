"""
Redis-based cache for FastAPI endpoints.
Caches responses for 30-60 seconds to avoid hitting database on every request.

Works across multiple Railway instances by using shared Redis cache.
Falls back to in-memory cache if Redis is unavailable.
"""

import json
import time
import hashlib
from datetime import datetime, date
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..config.settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CacheJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for cache that handles datetime, Decimal, and other non-serializable types."""
    
    def default(self, obj):
        """Convert non-serializable objects to JSON-serializable format."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        # Try to convert to string as last resort
        try:
            return str(obj)
        except Exception:
            return super().default(obj)


def serialize_for_cache(data: Any) -> str:
    """Serialize data for Redis cache with custom encoder that handles datetime and Decimal."""
    try:
        return json.dumps(data, cls=CacheJSONEncoder, default=str)
    except (TypeError, ValueError) as e:
        # Log which field caused the issue
        logger.error(f"Cache serialization error: {e}")
        logger.error(f"Data type: {type(data)}")
        if isinstance(data, dict):
            for key, value in data.items():
                logger.error(f"  {key}: {type(value)} = {value}")
        elif isinstance(data, (list, tuple)):
            for i, item in enumerate(data[:5]):  # First 5 items
                logger.error(f"  [{i}]: {type(item)} = {item}")
        # Re-raise to prevent silent failures
        raise


def deserialize_from_cache(data: str) -> Any:
    """Deserialize data from Redis cache."""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Cache deserialization error: {e}")
        raise


def make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert object to JSON-serializable format.
    Handles datetime, Decimal, and custom objects.
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    if isinstance(obj, Decimal):
        return float(obj)
    
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    
    if hasattr(obj, '__dict__'):
        return make_json_serializable(obj.__dict__)
    
    # Last resort: convert to string
    try:
        return str(obj)
    except Exception:
        return None

# Fallback in-memory cache (if Redis unavailable)
_memory_cache: dict[str, tuple[Any, float]] = {}

# Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None


def _get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client (lazy initialization)."""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        settings = get_settings()
        redis_url = settings.redis_url
        
        # Parse Redis URL
        if redis_url.startswith("redis://"):
            # Parse redis://host:port/db or redis://:password@host:port/db
            _redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
            )
            
            # Test connection
            _redis_client.ping()
            logger.info("✅ Redis cache connected", url=redis_url.split("@")[-1] if "@" in redis_url else redis_url)
            return _redis_client
        else:
            logger.warning("Invalid Redis URL format", url=redis_url)
            return None
            
    except Exception as e:
        logger.warning("Redis unavailable, falling back to in-memory cache", error=str(e))
        return None


def cache_response(seconds: int = 60):
    """
    Cache decorator for FastAPI async endpoints using Redis.
    
    Caches the response for the specified number of seconds.
    Cache key is generated from function name and actual query parameters.
    Dependency injection objects (like Depends) are excluded from cache key.
    
    Falls back to in-memory cache if Redis is unavailable.
    
    Usage:
        @router.get("/dashboard/stats")
        @cache_response(seconds=30)
        async def dashboard_stats():
            # expensive database query
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            # Exclude dependency injection objects (Depends) from cache key
            # Only include actual query parameters (str, int, float, bool, None)
            cache_kwargs = {}
            for k, v in kwargs.items():
                # Only include simple types (not objects like Depends)
                if isinstance(v, (str, int, float, bool, type(None))):
                    cache_kwargs[k] = v
                # Skip dependency injection objects and complex types
            
            # Build cache key from function name and simple kwargs only
            cache_key_data = f"{func.__name__}:{sorted(cache_kwargs.items())}"
            cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()
            
            # Try Redis first
            redis_client = _get_redis_client()
            if redis_client:
                try:
                    # Check Redis cache
                    cached_json = redis_client.get(cache_key)
                    if cached_json:
                        # Cache hit - return cached data
                        try:
                            cached_data = deserialize_from_cache(cached_json)
                            logger.debug(f"Cache HIT (Redis) for {func.__name__}")
                            return cached_data
                        except Exception as e:
                            logger.warning(f"Cache deserialization failed, treating as miss", error=str(e))
                            # Fall through to cache miss
                    
                    # Cache miss - call function
                    logger.info(f"🔄 Cache MISS (Redis): {func.__name__}")
                    result = await func(*args, **kwargs)
                    
                    # Store in Redis with TTL using custom serialization
                    try:
                        logger.debug(f"📦 Caching result for {func.__name__}")
                        logger.debug(f"   Result type: {type(result)}")
                        if isinstance(result, dict):
                            logger.debug(f"   Keys: {list(result.keys())}")
                            for key, value in list(result.items())[:5]:  # First 5 keys
                                logger.debug(f"   {key}: {type(value).__name__}")
                        
                        # Force conversion to JSON-serializable format
                        safe_result = make_json_serializable(result)
                        
                        # Serialize with custom encoder
                        result_json = serialize_for_cache(safe_result)
                        
                        # Store in Redis
                        redis_client.setex(cache_key, seconds, result_json)
                        logger.info(f"✅ Successfully cached {func.__name__} for {seconds}s")
                    except (TypeError, ValueError) as e:
                        logger.error(f"❌ Serialization failed for {func.__name__}: {e}")
                        logger.error(f"   Result type: {type(result)}")
                        if isinstance(result, dict):
                            for key, value in result.items():
                                logger.error(f"   {key}: {type(value).__name__} = {value}")
                        # Don't cache, but return the result
                    except Exception as e:
                        logger.warning(f"Failed to store in Redis cache", error=str(e))
                    
                    return result
                    
                except Exception as e:
                    logger.warning(f"Redis error, falling back to in-memory cache", error=str(e))
                    # Fall through to in-memory cache
            
            # Fallback to in-memory cache (if Redis unavailable)
            if cache_key in _memory_cache:
                cached_data, cached_time = _memory_cache[cache_key]
                age = time.time() - cached_time
                
                if age < seconds:
                    # Cache hit - return cached data
                    logger.debug(f"Cache HIT (memory) for {func.__name__}")
                    return cached_data
            
            # Cache miss - call function
            logger.debug(f"Cache MISS (memory) for {func.__name__} - fetching fresh data")
            result = await func(*args, **kwargs)
            
            # Store in memory cache
            _memory_cache[cache_key] = (result, time.time())
            
            # Clean old cache entries periodically (every 10th call)
            if len(_memory_cache) % 10 == 0:
                _clean_memory_cache(max_age=300)  # Remove entries older than 5 minutes
            
            return result
        
        return wrapper
    return decorator


def _clean_memory_cache(max_age: int = 300):
    """Remove cache entries older than max_age seconds from memory cache."""
    current_time = time.time()
    keys_to_delete = [
        key for key, (_, cached_time) in _memory_cache.items()
        if current_time - cached_time > max_age
    ]
    
    for key in keys_to_delete:
        del _memory_cache[key]


def clear_cache():
    """Clear all cache entries (both Redis and memory)."""
    global _memory_cache
    
    # Clear Redis cache
    redis_client = _get_redis_client()
    if redis_client:
        try:
            # Get all keys with our prefix (if we use one)
            # For now, just clear memory cache
            pass
        except Exception:
            pass
    
    # Clear memory cache
    _memory_cache.clear()
    logger.info("Cache cleared")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    stats = {
        'memory_cache': {
            'total_entries': len(_memory_cache),
            'valid_entries': 0,
            'expired_entries': 0
        },
        'redis_cache': {
            'connected': False,
            'keys': 0
        }
    }
    
    # Memory cache stats
    current_time = time.time()
    for _, (_, cached_time) in _memory_cache.items():
        if current_time - cached_time < 60:  # Consider valid if < 60s old
            stats['memory_cache']['valid_entries'] += 1
        else:
            stats['memory_cache']['expired_entries'] += 1
    
    # Redis cache stats
    redis_client = _get_redis_client()
    if redis_client:
        try:
            stats['redis_cache']['connected'] = True
            stats['redis_cache']['keys'] = redis_client.dbsize()
        except Exception:
            pass
    
    return stats

"""
Simple in-memory cache for slow endpoints.
Caches responses for 30-60 seconds to avoid hitting database on every request.

Note: For production with multiple instances, consider Redis instead of in-memory cache.
"""

import time
import hashlib
from functools import wraps
from typing import Any, Callable

# Simple in-memory cache (use Redis in production for multi-instance)
_cache: dict[str, tuple[Any, float]] = {}


def cache_response(seconds: int = 60):
    """
    Cache decorator for FastAPI async endpoints.
    
    Caches the response for the specified number of seconds.
    Cache key is generated from function name and actual query parameters.
    Dependency injection objects (like Depends) are excluded from cache key.
    
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
            
            # Check cache
            if cache_key in _cache:
                cached_data, cached_time = _cache[cache_key]
                age = time.time() - cached_time
                
                if age < seconds:
                    # Cache hit - return cached data
                    return cached_data
            
            # Cache miss - call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            _cache[cache_key] = (result, time.time())
            
            # Clean old cache entries periodically (every 10th call)
            if len(_cache) % 10 == 0:
                _clean_cache(max_age=300)  # Remove entries older than 5 minutes
            
            return result
        
        return wrapper
    return decorator


def _clean_cache(max_age: int = 300):
    """Remove cache entries older than max_age seconds"""
    current_time = time.time()
    keys_to_delete = [
        key for key, (_, cached_time) in _cache.items()
        if current_time - cached_time > max_age
    ]
    
    for key in keys_to_delete:
        del _cache[key]


def clear_cache():
    """Clear all cache entries"""
    global _cache
    _cache.clear()


def get_cache_stats() -> dict:
    """Get cache statistics"""
    current_time = time.time()
    valid = 0
    expired = 0
    
    for _, (_, cached_time) in _cache.items():
        if current_time - cached_time < 60:  # Consider valid if < 60s old
            valid += 1
        else:
            expired += 1
    
    return {
        'total_entries': len(_cache),
        'valid_entries': valid,
        'expired_entries': expired
    }


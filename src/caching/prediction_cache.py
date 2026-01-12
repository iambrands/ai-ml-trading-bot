"""Intelligent prediction caching to reduce API costs."""

import os
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


class IntelligentPredictionCache:
    """Smart caching that only regenerates when needed."""
    
    def __init__(self, ttl_minutes: int = 5, price_change_threshold: float = 0.05):
        self.cache: Dict[str, Tuple[float, datetime, float]] = {}  # market_id -> (prediction, timestamp, price)
        self.ttl = ttl_minutes * 60
        self.price_threshold = price_change_threshold
    
    async def should_regenerate(
        self, 
        market_id: str, 
        current_price: float,
        resolution_date: Optional[datetime] = None
    ) -> bool:
        """
        Only regenerate if:
        1. Market not in cache
        2. Cache expired (TTL)
        3. Price moved >threshold from cached prediction
        4. Market is closing soon (<24 hours)
        """
        if market_id not in self.cache:
            logger.debug("Market not in cache", market_id=market_id[:20])
            return True
        
        cached_timestamp, cached_prediction, cached_price = self.cache[market_id]
        age = time.time() - cached_timestamp
        
        # Check TTL expiration
        if age > self.ttl:
            logger.debug("Cache expired", market_id=market_id[:20], age_seconds=age)
            return True
        
        # Check if price moved significantly
        if cached_price > 0:
            price_change = abs(current_price - cached_price) / cached_price
            if price_change > self.price_threshold:
                logger.debug(
                    "Price moved significantly",
                    market_id=market_id[:20],
                    price_change=f"{price_change:.2%}",
                    threshold=f"{self.price_threshold:.2%}"
                )
                return True
        
        # Check if market closing soon (regenerate more frequently)
        if resolution_date:
            time_to_resolution = (resolution_date - datetime.now()).total_seconds()
            if time_to_resolution < 86400:  # Less than 24 hours
                # Reduce TTL for markets closing soon
                reduced_ttl = self.ttl / 2
                if age > reduced_ttl:
                    logger.debug(
                        "Market closing soon, regenerating",
                        market_id=market_id[:20],
                        hours_until_resolution=time_to_resolution / 3600
                    )
                    return True
        
        logger.debug("Using cached prediction", market_id=market_id[:20])
        return False
    
    def update_cache(self, market_id: str, prediction: float, market_price: float):
        """Update cache with new prediction."""
        self.cache[market_id] = (time.time(), prediction, market_price)
        logger.debug(
            "Cache updated",
            market_id=market_id[:20],
            prediction=f"{prediction:.2%}",
            price=f"{market_price:.2%}"
        )
    
    def get_cached(self, market_id: str) -> Optional[float]:
        """Get cached prediction if available and not expired."""
        if market_id not in self.cache:
            return None
        
        cached_timestamp, prediction, _ = self.cache[market_id]
        age = time.time() - cached_timestamp
        
        if age < self.ttl:
            return prediction
        
        # Expired, remove from cache
        del self.cache[market_id]
        return None
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance metrics."""
        now = time.time()
        total = len(self.cache)
        expired = sum(
            1 for _, (cached_time, _, _) in self.cache.items()
            if now - cached_time > self.ttl
        )
        
        # Clean expired entries
        self.cache = {
            k: v for k, v in self.cache.items()
            if now - v[0] <= self.ttl
        }
        
        return {
            "total_cached": total,
            "expired": expired,
            "active": total - expired,
            "ttl_minutes": self.ttl / 60,
            "price_threshold": f"{self.price_threshold:.2%}",
        }
    
    def clear_cache(self):
        """Clear all cached predictions."""
        self.cache.clear()
        logger.info("Prediction cache cleared")


# Global cache instance
_prediction_cache = None


def get_prediction_cache() -> IntelligentPredictionCache:
    """Get or create global prediction cache instance."""
    global _prediction_cache
    if _prediction_cache is None:
        _prediction_cache = IntelligentPredictionCache(
            ttl_minutes=int(os.getenv('PREDICTION_CACHE_TTL_MINUTES', '5')),
            price_change_threshold=float(os.getenv('PREDICTION_CACHE_PRICE_THRESHOLD', '0.05'))
        )
    return _prediction_cache


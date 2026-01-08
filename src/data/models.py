"""Data models for markets, news, social media, etc."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np


@dataclass
class Market:
    """Polymarket market data."""

    id: str
    condition_id: str
    question: str
    category: Optional[str] = None
    resolution_date: Optional[datetime] = None
    outcome: Optional[str] = None  # YES/NO
    yes_price: float = 0.0
    no_price: float = 0.0
    volume_24h: float = 0.0
    liquidity: float = 0.0
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


@dataclass
class NewsArticle:
    """News article data."""

    title: str
    description: str
    content: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class SocialPost:
    """Social media post (Twitter/Reddit)."""

    id: str
    platform: str  # "twitter" or "reddit"
    text: str
    author: str
    created_at: datetime
    engagement: int = 0  # Likes/upvotes
    sentiment_score: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class SocialSentiment:
    """Aggregated social sentiment."""

    platform: str
    average_sentiment: float
    sentiment_std: float
    volume: int
    velocity: float  # Rate of change
    top_posts: List[SocialPost] = field(default_factory=list)


@dataclass
class WhaleTrade:
    """Large trader activity."""

    market_id: str
    trader_address: str
    side: str  # YES or NO
    size: float
    price: float
    timestamp: datetime
    is_smart_money: bool = False  # Based on historical accuracy


@dataclass
class MarketData:
    """Current market state."""

    market: Market
    timestamp: datetime
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    spread: Optional[float] = None
    orderbook_depth: Optional[float] = None


@dataclass
class AggregatedData:
    """All aggregated data for a market."""

    market: MarketData
    news: List[NewsArticle] = field(default_factory=list)
    social: Optional[SocialSentiment] = None
    whales: List[WhaleTrade] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FeatureVector:
    """Feature vector for model input."""

    market_id: str
    timestamp: datetime
    features: Dict[str, float] = field(default_factory=dict)
    embeddings: Dict[str, np.ndarray] = field(default_factory=dict)

    def to_array(self, feature_names: List[str]) -> np.ndarray:
        """Convert features to numpy array."""
        return np.array([self.features.get(name, 0.0) for name in feature_names])


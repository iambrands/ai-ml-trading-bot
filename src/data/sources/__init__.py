"""Data source modules."""

from .aggregator import DataAggregator
from .polymarket import PolymarketDataSource
from .news import NewsDataSource
from .twitter import TwitterDataSource
from .reddit import RedditDataSource

__all__ = [
    "DataAggregator",
    "PolymarketDataSource",
    "NewsDataSource",
    "TwitterDataSource",
    "RedditDataSource",
]




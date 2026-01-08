"""Unified data aggregator for all data sources."""

import asyncio
from typing import Dict, List, Optional

from ..models import AggregatedData, Market, MarketData, NewsArticle, SocialSentiment, WhaleTrade
from .news import NewsDataSource
from .polymarket import PolymarketDataSource
from .reddit import RedditDataSource
from .twitter import TwitterDataSource
from ...utils.async_utils import gather_with_exceptions
from ...utils.logging import get_logger

logger = get_logger(__name__)


class DataAggregator:
    """Unified interface for all data sources with async fetching and caching."""

    def __init__(
        self,
        polymarket: Optional[PolymarketDataSource] = None,
        news: Optional[NewsDataSource] = None,
        twitter: Optional[TwitterDataSource] = None,
        reddit: Optional[RedditDataSource] = None,
    ):
        """
        Initialize data aggregator.

        Args:
            polymarket: Polymarket data source
            news: News data source
            twitter: Twitter data source
            reddit: Reddit data source
        """
        self.polymarket = polymarket or PolymarketDataSource()
        self.news = news or NewsDataSource()
        self.twitter = twitter or TwitterDataSource()
        self.reddit = reddit or RedditDataSource()

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from market question for news/social search.

        Args:
            text: Market question text

        Returns:
            List of keywords
        """
        # Simple keyword extraction
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "will",
            "be",
            "is",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            "do",
            "does",
            "did",
            "this",
            "that",
            "these",
            "those",
        }
        words = text.lower().replace("?", "").replace(".", "").split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return keywords[:5]  # Top 5 keywords

    async def fetch_market_data(self, market_id: str) -> Optional[MarketData]:
        """
        Fetch current market data.

        Args:
            market_id: Market ID

        Returns:
            MarketData object or None
        """
        return await self.polymarket.fetch_market_data(market_id)

    async def fetch_news(self, query: str, days_back: int = 7) -> List[NewsArticle]:
        """
        Fetch relevant news articles.

        Args:
            query: Search query
            days_back: Days to look back

        Returns:
            List of NewsArticle objects
        """
        from datetime import datetime, timedelta

        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=days_back)

        return await self.news.fetch_articles(query, from_date=from_date, to_date=to_date)

    async def fetch_social_sentiment(self, query: str) -> Optional[SocialSentiment]:
        """
        Fetch aggregated social sentiment from Twitter and Reddit.

        Args:
            query: Search query

        Returns:
            SocialSentiment object or None
        """
        # Fetch from both sources in parallel
        twitter_sentiment, reddit_sentiment = await gather_with_exceptions(
            self.twitter.fetch_sentiment(query), self.reddit.fetch_sentiment(query)
        )

        # Aggregate sentiments
        sentiments = []
        if twitter_sentiment and not isinstance(twitter_sentiment, Exception):
            sentiments.append(twitter_sentiment)
        if reddit_sentiment and not isinstance(reddit_sentiment, Exception):
            sentiments.append(reddit_sentiment)

        if not sentiments:
            return None

        # Combine multiple platform sentiments
        # Simple average for now (could weight by volume)
        total_volume = sum(s.volume for s in sentiments)
        if total_volume == 0:
            return None

        weighted_sentiment = sum(s.average_sentiment * s.volume for s in sentiments) / total_volume

        import numpy as np

        all_scores = []
        all_posts = []
        for s in sentiments:
            all_scores.extend([p.sentiment_score for p in s.top_posts if p.sentiment_score is not None])
            all_posts.extend(s.top_posts)

        return SocialSentiment(
            platform="aggregated",
            average_sentiment=float(weighted_sentiment),
            sentiment_std=float(np.std(all_scores)) if all_scores else 0.0,
            volume=total_volume,
            velocity=0.0,
            top_posts=sorted(all_posts, key=lambda x: x.engagement, reverse=True)[:20],
        )

    async def fetch_whale_activity(self, market_id: str) -> List[WhaleTrade]:
        """
        Fetch large trader activity (placeholder implementation).

        Args:
            market_id: Market ID

        Returns:
            List of WhaleTrade objects
        """
        # Placeholder - would integrate with on-chain data or Polymarket API
        # to track large trades and identify smart money
        logger.debug("Whale activity tracking not yet implemented", market_id=market_id)
        return []

    async def fetch_all_for_market(self, market: Market) -> AggregatedData:
        """
        Fetch all relevant data for a market in parallel.

        Args:
            market: Market object

        Returns:
            AggregatedData object with all fetched data
        """
        # Extract search terms from market question
        keywords = self.extract_keywords(market.question)
        query = " ".join(keywords)

        logger.info("Fetching all data for market", market_id=market.id, query=query)

        # Fetch all data sources in parallel
        results = await gather_with_exceptions(
            self.fetch_market_data(market.id),
            self.fetch_news(query, days_back=7),
            self.fetch_social_sentiment(query),
            self.fetch_whale_activity(market.id),
        )

        market_data, news, social, whales = results

        # Handle exceptions
        if isinstance(market_data, Exception) or market_data is None:
            logger.warning("Failed to fetch market data", market_id=market.id)
            # Create minimal market data
            from datetime import datetime
        market_data = MarketData(market=market, timestamp=datetime.utcnow())

        if isinstance(news, Exception):
            news = []
        if isinstance(social, Exception):
            social = None
        if isinstance(whales, Exception):
            whales = []

        from datetime import datetime
        return AggregatedData(
            market=market_data if not isinstance(market_data, Exception) else MarketData(market=market, timestamp=datetime.utcnow()),
            news=news if not isinstance(news, Exception) else [],
            social=social if not isinstance(social, Exception) else None,
            whales=whales if not isinstance(whales, Exception) else [],
        )


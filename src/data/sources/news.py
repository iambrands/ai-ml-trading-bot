"""NewsAPI data source for fetching news articles."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from newsapi import NewsApiClient

from ..models import NewsArticle
from ...config.settings import get_settings
from ...utils.logging import get_logger

logger = get_logger(__name__)


class DataSource(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    async def fetch(self, query: str, **kwargs) -> List[Dict]:
        """Fetch data from source."""
        pass


class NewsDataSource(DataSource):
    """NewsAPI integration for fetching relevant news articles."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NewsAPI data source.

        Args:
            api_key: NewsAPI key (or from settings)
        """
        settings = get_settings()
        self.api_key = api_key or settings.newsapi_key
        if not self.api_key:
            logger.warning("NewsAPI key not provided, news fetching will be disabled")
            self.client = None
        else:
            self.client = NewsApiClient(api_key=self.api_key)

    async def fetch(
        self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, **kwargs
    ) -> List[Dict]:
        """
        Fetch news articles.

        Args:
            query: Search query
            from_date: Start date
            to_date: End date

        Returns:
            List of news articles as dictionaries
        """
        if not self.client:
            return []

        try:
            # NewsAPI free tier limitations
            if not from_date:
                from_date = datetime.utcnow() - timedelta(days=1)
            if not to_date:
                to_date = datetime.utcnow()

            # Format dates for NewsAPI
            from_str = from_date.strftime("%Y-%m-%d")
            to_str = to_date.strftime("%Y-%m-%d")

            # Fetch articles
            response = self.client.get_everything(
                q=query,
                from_param=from_str,
                to=to_str,
                language="en",
                sort_by="publishedAt",
                page_size=kwargs.get("max_articles", 50),
            )

            articles = []
            for article in response.get("articles", []):
                articles.append(
                    {
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "content": article.get("content", ""),
                        "source": article.get("source", {}).get("name", ""),
                        "url": article.get("url", ""),
                        "published_at": self._parse_date(article.get("publishedAt")),
                    }
                )

            logger.info("Fetched news articles", query=query, count=len(articles))
            return articles

        except Exception as e:
            logger.error("Failed to fetch news", query=query, error=str(e))
            return []

    async def fetch_articles(
        self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None
    ) -> List[NewsArticle]:
        """
        Fetch news articles and return as NewsArticle objects.

        Args:
            query: Search query
            from_date: Start date
            to_date: End date

        Returns:
            List of NewsArticle objects
        """
        articles_data = await self.fetch(query, from_date=from_date, to_date=to_date)
        return [self._parse_article(data) for data in articles_data]

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for news search.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Simple keyword extraction (can be enhanced with NLP)
        # Remove common words and extract meaningful terms
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return keywords[:5]  # Limit to top 5 keywords

    def _parse_article(self, data: Dict) -> NewsArticle:
        """Parse article data into NewsArticle object."""
        return NewsArticle(
            title=data.get("title", ""),
            description=data.get("description", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            url=data.get("url", ""),
            published_at=data.get("published_at", datetime.utcnow()),
        )

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse ISO date string."""
        if not date_str:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.utcnow()


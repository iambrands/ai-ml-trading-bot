"""RSS-based news data source (free alternative to NewsAPI)."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import quote, urlencode
import xml.etree.ElementTree as ET

import aiohttp

from ..models import NewsArticle
from ...config.settings import get_settings
from ...utils.logging import get_logger

logger = get_logger(__name__)


class RSSNewsDataSource:
    """RSS-based news source using Google News and other RSS feeds."""

    def __init__(self):
        """Initialize RSS news data source."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.sources = {
            "google_news": "https://news.google.com/rss/search",
            "reuters": "https://www.reuters.com/rssFeed",
            "bbc": "https://feeds.bbci.co.uk/news/rss.xml",
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def fetch(
        self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, **kwargs
    ) -> List[Dict]:
        """
        Fetch news articles from RSS feeds.

        Args:
            query: Search query
            from_date: Start date (not used for RSS, but kept for compatibility)
            to_date: End date (not used for RSS, but kept for compatibility)
            **kwargs: Additional parameters

        Returns:
            List of news articles as dictionaries
        """
        from ...utils.rate_limiter import rate_limited, RateLimitExceeded
        
        if not self.session:
            self.session = aiohttp.ClientSession()

        max_articles = kwargs.get("max_articles", 50)
        articles = []

        try:
            # Try Google News RSS first (best for search queries)
            google_articles = await self._fetch_google_news(query, max_articles)
            articles.extend(google_articles)

            # If we need more, try other sources
            if len(articles) < max_articles:
                reuters_articles = await self._fetch_reuters(query, max_articles - len(articles))
                articles.extend(reuters_articles)

            logger.info("Fetched news articles from RSS", query=query, count=len(articles))
            return articles[:max_articles]

        except Exception as e:
            logger.error("Failed to fetch RSS news", query=query, error=str(e))
            return []

    async def _fetch_google_news(self, query: str, max_articles: int = 50) -> List[Dict]:
        """Fetch articles from Google News RSS."""
        try:
            # Google News RSS format
            params = {
                "q": query,
                "hl": "en",
                "gl": "US",
                "ceid": "US:en",
            }
            url = f"{self.sources['google_news']}?{urlencode(params)}"

            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.warning("Google News RSS returned non-200 status", status=response.status)
                    return []

                text = await response.text()
                root = ET.fromstring(text)

                articles = []
                for item in root.findall(".//item")[:max_articles]:
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    description = item.find("description")
                    source = item.find("source")

                    if title is not None and link is not None:
                        articles.append(
                            {
                                "title": title.text or "",
                                "description": description.text if description is not None else "",
                                "content": description.text if description is not None else "",
                                "source": source.text if source is not None else "Google News",
                                "url": link.text or "",
                                "published_at": self._parse_rss_date(pub_date.text if pub_date is not None else None),
                            }
                        )

                return articles

        except Exception as e:
            logger.warning("Failed to fetch Google News RSS", error=str(e))
            return []

    async def _fetch_reuters(self, query: str, max_articles: int = 50) -> List[Dict]:
        """Fetch articles from Reuters RSS (general feed, not searchable)."""
        try:
            # Reuters doesn't support search in RSS, so we get general feed
            # and filter by keywords
            url = self.sources["reuters"]

            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return []

                text = await response.text()
                root = ET.fromstring(text)

                query_keywords = set(query.lower().split())
                articles = []

                for item in root.findall(".//item"):
                    if len(articles) >= max_articles:
                        break

                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    description = item.find("description")

                    if title is None or link is None:
                        continue

                    # Simple keyword matching
                    title_text = (title.text or "").lower()
                    desc_text = (description.text if description is not None else "").lower()
                    combined_text = title_text + " " + desc_text

                    # Check if any query keywords appear in title/description
                    if any(keyword in combined_text for keyword in query_keywords if len(keyword) > 3):
                        articles.append(
                            {
                                "title": title.text or "",
                                "description": description.text if description is not None else "",
                                "content": description.text if description is not None else "",
                                "source": "Reuters",
                                "url": link.text or "",
                                "published_at": self._parse_rss_date(pub_date.text if pub_date is not None else None),
                            }
                        )

                return articles

        except Exception as e:
            logger.warning("Failed to fetch Reuters RSS", error=str(e))
            return []

    def _parse_rss_date(self, date_str: Optional[str]) -> datetime:
        """Parse RSS date string (RFC 822 format)."""
        if not date_str:
            return datetime.now(timezone.utc)

        try:
            # Try common RSS date formats
            from email.utils import parsedate_to_datetime

            if date_str:
                dt = parsedate_to_datetime(date_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
        except (ValueError, TypeError):
            pass

        return datetime.now(timezone.utc)

    async def fetch_articles(
        self, query: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None
    ) -> List[NewsArticle]:
        """
        Fetch news articles and return as NewsArticle objects.

        Args:
            query: Search query
            from_date: Start date (for compatibility, not used in RSS)
            to_date: End date (for compatibility, not used in RSS)

        Returns:
            List of NewsArticle objects
        """
        articles_data = await self.fetch(query, from_date=from_date, to_date=to_date)
        return [self._parse_article(data) for data in articles_data]

    def _parse_article(self, data: Dict) -> NewsArticle:
        """Parse article data into NewsArticle object."""
        return NewsArticle(
            title=data.get("title", ""),
            description=data.get("description", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            url=data.get("url", ""),
            published_at=data.get("published_at", datetime.now(timezone.utc)),
        )

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for news search.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return keywords[:5]  # Limit to top 5 keywords




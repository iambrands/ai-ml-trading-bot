"""News Aggregation Feed Service."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import NewsArticle, NewsMarketLink, Market
from ..utils.logging import get_logger

logger = get_logger(__name__)


class NewsAggregationService:
    """Aggregates and links news articles to prediction markets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_article(
        self,
        title: str,
        source: str,
        url: str,
        summary: Optional[str] = None,
        content_snippet: Optional[str] = None,
        author: Optional[str] = None,
        category: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        sentiment_label: Optional[str] = None,
        relevance_score: Optional[float] = None,
        image_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ) -> Optional[Dict]:
        """Add a news article to the feed."""
        try:
            article = NewsArticle(
                title=title,
                source=source,
                url=url,
                summary=summary,
                content_snippet=content_snippet,
                author=author,
                category=category,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                relevance_score=relevance_score,
                image_url=image_url,
                published_at=published_at or datetime.now(timezone.utc),
            )
            self.db.add(article)
            await self.db.commit()
            await self.db.refresh(article)
            return self._article_to_dict(article)
        except Exception as e:
            logger.error("Failed to add article", title=title, error=str(e))
            await self.db.rollback()
            return None

    async def link_article_to_market(
        self,
        article_id: int,
        market_id: str,
        relevance_score: float = 0.5,
        impact_direction: Optional[str] = None,
    ) -> bool:
        """Link a news article to a market."""
        try:
            link = NewsMarketLink(
                article_id=article_id,
                market_id=market_id,
                relevance_score=relevance_score,
                impact_direction=impact_direction,
            )
            self.db.add(link)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error("Failed to link article to market", error=str(e))
            await self.db.rollback()
            return False

    async def get_feed(
        self,
        category: Optional[str] = None,
        source: Optional[str] = None,
        sentiment: Optional[str] = None,
        hours: int = 48,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Get the news feed with optional filters."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = select(NewsArticle).where(NewsArticle.published_at >= cutoff)

            if category:
                query = query.where(NewsArticle.category == category)
            if source:
                query = query.where(NewsArticle.source == source)
            if sentiment:
                query = query.where(NewsArticle.sentiment_label == sentiment.upper())

            query = query.order_by(desc(NewsArticle.published_at)).limit(limit).offset(offset)

            result = await self.db.execute(query)
            articles = result.scalars().all()
            return [self._article_to_dict(a) for a in articles]
        except Exception as e:
            logger.error("Failed to get news feed", error=str(e))
            return []

    async def get_market_news(self, market_id: str, limit: int = 20) -> List[Dict]:
        """Get news articles linked to a specific market."""
        try:
            result = await self.db.execute(
                select(NewsArticle)
                .join(NewsMarketLink)
                .where(NewsMarketLink.market_id == market_id)
                .order_by(desc(NewsArticle.published_at))
                .limit(limit)
            )
            articles = result.scalars().all()
            return [self._article_to_dict(a) for a in articles]
        except Exception as e:
            logger.error("Failed to get market news", error=str(e))
            return []

    async def get_trending_topics(self, hours: int = 24, limit: int = 10) -> List[Dict]:
        """Get trending news topics and categories."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

            result = await self.db.execute(
                select(
                    NewsArticle.category,
                    func.count(NewsArticle.id).label("count"),
                    func.avg(NewsArticle.sentiment_score).label("avg_sentiment"),
                )
                .where(
                    NewsArticle.published_at >= cutoff,
                    NewsArticle.category.isnot(None),
                )
                .group_by(NewsArticle.category)
                .order_by(desc("count"))
                .limit(limit)
            )
            rows = result.all()

            return [
                {
                    "category": row[0],
                    "article_count": row[1],
                    "avg_sentiment": round(float(row[2]), 4) if row[2] else None,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get trending topics", error=str(e))
            return []

    async def get_sentiment_overview(self, hours: int = 24) -> Dict:
        """Get sentiment overview across all recent news."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

            result = await self.db.execute(
                select(
                    func.count(NewsArticle.id),
                    func.avg(NewsArticle.sentiment_score),
                    func.count(NewsArticle.id).filter(NewsArticle.sentiment_label == "POSITIVE"),
                    func.count(NewsArticle.id).filter(NewsArticle.sentiment_label == "NEGATIVE"),
                    func.count(NewsArticle.id).filter(NewsArticle.sentiment_label == "NEUTRAL"),
                )
                .where(NewsArticle.published_at >= cutoff)
            )
            row = result.one()

            total = row[0] or 0
            return {
                "total_articles": total,
                "avg_sentiment_score": round(float(row[1]), 4) if row[1] else None,
                "positive_count": row[2] or 0,
                "negative_count": row[3] or 0,
                "neutral_count": row[4] or 0,
                "positive_pct": round((row[2] or 0) / total * 100, 1) if total > 0 else 0,
                "negative_pct": round((row[3] or 0) / total * 100, 1) if total > 0 else 0,
                "timespan_hours": hours,
                "market_mood": "BULLISH" if (row[1] or 0.5) > 0.6 else "BEARISH" if (row[1] or 0.5) < 0.4 else "NEUTRAL",
            }
        except Exception as e:
            logger.error("Failed to get sentiment overview", error=str(e))
            return {"total_articles": 0, "timespan_hours": hours}

    async def get_sources(self) -> List[Dict]:
        """Get list of news sources with article counts."""
        try:
            result = await self.db.execute(
                select(
                    NewsArticle.source,
                    func.count(NewsArticle.id).label("count"),
                    func.max(NewsArticle.published_at).label("latest"),
                )
                .group_by(NewsArticle.source)
                .order_by(desc("count"))
            )
            rows = result.all()
            return [
                {
                    "source": row[0],
                    "article_count": row[1],
                    "latest_article": row[2].isoformat() if row[2] else None,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get sources", error=str(e))
            return []

    async def auto_link_articles(self, limit: int = 50) -> int:
        """Automatically link unlinked articles to relevant markets based on keyword matching."""
        linked_count = 0
        try:
            articles_result = await self.db.execute(
                select(NewsArticle)
                .outerjoin(NewsMarketLink)
                .where(NewsMarketLink.id.is_(None))
                .order_by(desc(NewsArticle.published_at))
                .limit(limit)
            )
            articles = articles_result.scalars().all()

            markets_result = await self.db.execute(
                select(Market.market_id, Market.question, Market.category)
                .limit(200)
            )
            markets = markets_result.all()

            for article in articles:
                title_lower = (article.title or "").lower()
                for market_id, question, category in markets:
                    q_words = set((question or "").lower().split())
                    t_words = set(title_lower.split())
                    common = q_words & t_words - {"the", "a", "an", "is", "will", "be", "to", "of", "in", "for", "and", "or", "on", "at", "by"}
                    if len(common) >= 3:
                        relevance = min(1.0, len(common) / 5)
                        try:
                            link = NewsMarketLink(
                                article_id=article.id,
                                market_id=market_id,
                                relevance_score=relevance,
                            )
                            self.db.add(link)
                            linked_count += 1
                        except Exception:
                            continue

            if linked_count > 0:
                await self.db.commit()
            logger.info("Auto-linked articles to markets", linked=linked_count)
            return linked_count
        except Exception as e:
            logger.error("Failed to auto-link articles", error=str(e))
            await self.db.rollback()
            return 0

    def _article_to_dict(self, article: NewsArticle) -> Dict:
        return {
            "id": article.id,
            "title": article.title,
            "source": article.source,
            "url": article.url,
            "summary": article.summary,
            "content_snippet": article.content_snippet,
            "author": article.author,
            "category": article.category,
            "sentiment_score": float(article.sentiment_score) if article.sentiment_score else None,
            "sentiment_label": article.sentiment_label,
            "relevance_score": float(article.relevance_score) if article.relevance_score else None,
            "image_url": article.image_url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
        }

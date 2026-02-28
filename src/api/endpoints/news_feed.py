"""News Aggregation Feed API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.news_aggregation_service import NewsAggregationService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/news", tags=["news-feed"])


class AddArticleRequest(BaseModel):
    title: str
    source: str
    url: str
    summary: Optional[str] = None
    content_snippet: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[datetime] = None


class LinkArticleRequest(BaseModel):
    article_id: int
    market_id: str
    relevance_score: float = 0.5
    impact_direction: Optional[str] = None


@router.get("/feed")
async def get_news_feed(
    category: Optional[str] = None,
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    hours: int = Query(default=48, ge=1, le=720),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get the news feed with optional filters."""
    service = NewsAggregationService(db)
    return await service.get_feed(
        category=category, source=source, sentiment=sentiment,
        hours=hours, limit=limit, offset=offset,
    )


@router.get("/market/{market_id}")
async def get_market_news(
    market_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get news articles linked to a specific market."""
    service = NewsAggregationService(db)
    return await service.get_market_news(market_id, limit=limit)


@router.get("/trending")
async def get_trending_topics(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get trending news topics and categories."""
    service = NewsAggregationService(db)
    return await service.get_trending_topics(hours=hours, limit=limit)


@router.get("/sentiment")
async def get_sentiment_overview(
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get sentiment overview across all recent news."""
    service = NewsAggregationService(db)
    return await service.get_sentiment_overview(hours=hours)


@router.get("/sources")
async def get_news_sources(db: AsyncSession = Depends(get_db)):
    """Get list of news sources with article counts."""
    service = NewsAggregationService(db)
    return await service.get_sources()


@router.post("/articles")
async def add_article(request: AddArticleRequest, db: AsyncSession = Depends(get_db)):
    """Add a news article to the feed."""
    service = NewsAggregationService(db)
    result = await service.add_article(
        title=request.title,
        source=request.source,
        url=request.url,
        summary=request.summary,
        content_snippet=request.content_snippet,
        author=request.author,
        category=request.category,
        sentiment_score=request.sentiment_score,
        sentiment_label=request.sentiment_label,
        image_url=request.image_url,
        published_at=request.published_at,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to add article")
    return result


@router.post("/link")
async def link_article_to_market(request: LinkArticleRequest, db: AsyncSession = Depends(get_db)):
    """Link a news article to a market."""
    service = NewsAggregationService(db)
    success = await service.link_article_to_market(
        article_id=request.article_id,
        market_id=request.market_id,
        relevance_score=request.relevance_score,
        impact_direction=request.impact_direction,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to link article")
    return {"status": "linked"}


@router.post("/auto-link")
async def auto_link_articles(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Automatically link unlinked articles to relevant markets."""
    service = NewsAggregationService(db)
    count = await service.auto_link_articles(limit=limit)
    return {"status": "completed", "articles_linked": count}

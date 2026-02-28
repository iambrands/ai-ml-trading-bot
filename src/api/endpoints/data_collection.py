"""Data Collection Pipeline API endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.data_collection_service import DataCollectionService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/data-collection", tags=["data-collection"])


@router.post("/collect-all")
async def collect_all_data(
    background_tasks: BackgroundTasks,
    market_limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Run full data collection cycle (prices, order books, news) as background task."""
    service = DataCollectionService(db)

    async def _run():
        return await service.collect_all(market_limit=market_limit)

    background_tasks.add_task(_run)
    return {"status": "collection_started", "market_limit": market_limit}


@router.post("/collect-prices")
async def collect_prices(
    market_limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Collect price snapshots for active markets."""
    service = DataCollectionService(db)
    count = await service.collect_prices(market_limit=market_limit)
    return {"status": "completed", "prices_collected": count}


@router.post("/collect-orderbooks")
async def collect_orderbooks(
    market_limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Collect order book snapshots for top markets."""
    service = DataCollectionService(db)
    count = await service.collect_orderbooks(market_limit=market_limit)
    return {"status": "completed", "orderbooks_collected": count}


@router.post("/collect-news")
async def collect_news(
    market_limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Collect news articles relevant to active markets."""
    service = DataCollectionService(db)
    count = await service.collect_news_for_markets(market_limit=market_limit)
    return {"status": "completed", "news_collected": count}

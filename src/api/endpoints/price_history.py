"""Price History & Technical Analysis API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.price_history_service import PriceHistoryService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/price-history", tags=["price-history"])


class RecordPriceRequest(BaseModel):
    market_id: str
    yes_price: float
    no_price: float
    volume: float = 0
    liquidity: float = 0
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    open_interest: Optional[float] = None
    interval: str = "1h"


@router.get("/{market_id}")
async def get_price_history(
    market_id: str,
    hours: int = Query(default=168, ge=1, le=8760),
    interval: str = Query(default="1h"),
    limit: int = Query(default=500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    """Get price history for a market."""
    service = PriceHistoryService(db)
    return await service.get_price_history(market_id, hours=hours, interval=interval, limit=limit)


@router.get("/{market_id}/indicators")
async def get_technical_indicators(
    market_id: str,
    hours: int = Query(default=168, ge=1, le=8760),
    db: AsyncSession = Depends(get_db),
):
    """Compute technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, VWAP) for a market."""
    service = PriceHistoryService(db)
    return await service.compute_indicators(market_id, hours=hours)


@router.post("/record")
async def record_price(request: RecordPriceRequest, db: AsyncSession = Depends(get_db)):
    """Record a price data point."""
    service = PriceHistoryService(db)
    result = await service.record_price(
        market_id=request.market_id,
        yes_price=request.yes_price,
        no_price=request.no_price,
        volume=request.volume,
        liquidity=request.liquidity,
        bid_price=request.bid_price,
        ask_price=request.ask_price,
        open_interest=request.open_interest,
        interval=request.interval,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to record price")
    return result

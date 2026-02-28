"""Live Order Book Depth Analysis API endpoints."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.orderbook_service import OrderBookService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/orderbook", tags=["orderbook"])


class OrderBookSnapshotRequest(BaseModel):
    market_id: str
    bids: List[Dict]
    asks: List[Dict]


@router.get("/{market_id}")
async def get_latest_orderbook(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get the latest order book snapshot for a market."""
    service = OrderBookService(db)
    result = await service.get_latest_snapshot(market_id)
    if not result:
        return {"market_id": market_id, "message": "No order book data available"}
    return result


@router.get("/{market_id}/depth")
async def get_depth_chart(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get order book depth chart data for visualization."""
    service = OrderBookService(db)
    result = await service.get_depth_chart_data(market_id)
    if not result:
        return {"market_id": market_id, "message": "No order book data available"}
    return result


@router.get("/{market_id}/spread-history")
async def get_spread_history(
    market_id: str,
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get historical spread data for a market."""
    service = OrderBookService(db)
    return await service.get_spread_history(market_id, hours=hours)


@router.get("/{market_id}/microstructure")
async def analyze_microstructure(market_id: str, db: AsyncSession = Depends(get_db)):
    """Analyze market microstructure from order book data."""
    service = OrderBookService(db)
    return await service.analyze_market_microstructure(market_id)


@router.post("/snapshot")
async def save_orderbook_snapshot(request: OrderBookSnapshotRequest, db: AsyncSession = Depends(get_db)):
    """Save an order book snapshot."""
    service = OrderBookService(db)
    result = await service.save_snapshot(
        market_id=request.market_id,
        bids=request.bids,
        asks=request.asks,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to save snapshot")
    return result

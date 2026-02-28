"""Social Sentiment Momentum API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db
from ...services.sentiment_momentum_service import SentimentMomentumService
router = APIRouter(prefix="/sentiment-momentum", tags=["sentiment-momentum"])

@router.get("/mood")
async def get_market_mood(db: AsyncSession = Depends(get_db)):
    """Get overall market mood from sentiment across all markets."""
    return await SentimentMomentumService(db).get_market_mood()

@router.get("/divergences")
async def get_divergences(signal_type: Optional[str] = None, limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Get markets with sentiment-price divergences (leading indicators)."""
    return await SentimentMomentumService(db).get_divergences(signal_type=signal_type, limit=limit)

@router.get("/{market_id}")
async def get_momentum(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get latest sentiment momentum for a market."""
    result = await SentimentMomentumService(db).get_momentum(market_id)
    return result or {"market_id": market_id, "message": "No momentum data. Measure with POST."}

@router.get("/{market_id}/history")
async def get_momentum_history(market_id: str, hours: int = Query(default=48, ge=1, le=720), db: AsyncSession = Depends(get_db)):
    """Get sentiment momentum history for a market."""
    return await SentimentMomentumService(db).get_momentum_history(market_id, hours=hours)

@router.post("/{market_id}/measure")
async def measure_momentum(market_id: str, db: AsyncSession = Depends(get_db)):
    """Measure current sentiment momentum and detect divergences."""
    result = await SentimentMomentumService(db).measure_momentum(market_id)
    return result or {"market_id": market_id, "message": "Insufficient data for measurement"}

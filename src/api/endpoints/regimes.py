"""Market Regime Detection API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db
from ...services.regime_detection_service import RegimeDetectionService
router = APIRouter(prefix="/regimes", tags=["regime-detection"])

@router.get("/distribution")
async def get_regime_distribution(db: AsyncSession = Depends(get_db)):
    """Get distribution of market regimes across all analyzed markets."""
    return await RegimeDetectionService(db).get_regime_distribution()

@router.get("/{market_id}")
async def get_regime(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get latest detected regime for a market."""
    result = await RegimeDetectionService(db).get_regime(market_id)
    return result or {"market_id": market_id, "message": "No regime detected. Run detection with POST."}

@router.get("/{market_id}/history")
async def get_regime_history(market_id: str, limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Get regime change history for a market."""
    return await RegimeDetectionService(db).get_regime_history(market_id, limit=limit)

@router.post("/{market_id}/detect")
async def detect_regime(market_id: str, lookback_hours: int = Query(default=48, ge=6, le=720), db: AsyncSession = Depends(get_db)):
    """Detect current market regime (trending/mean-reverting/volatile/choppy) and recommend strategy."""
    result = await RegimeDetectionService(db).detect_regime(market_id, lookback_hours=lookback_hours)
    return result or {"market_id": market_id, "message": "Insufficient price data for regime detection"}

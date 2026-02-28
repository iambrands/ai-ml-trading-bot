"""Resolution Probability Decay Curves API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db
from ...services.probability_decay_service import ProbabilityDecayService
router = APIRouter(prefix="/decay-curves", tags=["probability-decay"])

@router.get("/converging")
async def get_converging_markets(min_decay_rate: float = Query(default=0.01, ge=0), limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Find markets rapidly converging toward resolution."""
    return await ProbabilityDecayService(db).get_converging_markets(min_decay_rate=min_decay_rate, limit=limit)

@router.get("/{market_id}")
async def get_decay_curve(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get the predicted probability path with confidence bands for a market."""
    result = await ProbabilityDecayService(db).get_decay_curve(market_id)
    return result or {"market_id": market_id, "message": "No decay curve available. Generate one with POST."}

@router.post("/{market_id}/generate")
async def generate_decay_curve(market_id: str, db: AsyncSession = Depends(get_db)):
    """Generate probability decay curve showing predicted path to resolution."""
    result = await ProbabilityDecayService(db).generate_decay_curve(market_id)
    if not result:
        raise HTTPException(status_code=400, detail="Insufficient data for curve generation")
    return result

"""Portfolio Hedging Engine API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db
from ...services.hedging_service import HedgingService
router = APIRouter(prefix="/hedging", tags=["hedging"])

@router.get("/suggestions")
async def get_hedge_suggestions(market_id: Optional[str] = None, executed: Optional[bool] = None, limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Get hedge suggestions for open positions."""
    return await HedgingService(db).get_suggestions(market_id=market_id, executed=executed, limit=limit)

@router.post("/suggest")
async def suggest_hedges(min_effectiveness: float = Query(default=0.3, ge=0, le=1), db: AsyncSession = Depends(get_db)):
    """Analyze portfolio and generate new hedge suggestions."""
    return await HedgingService(db).suggest_hedges(min_effectiveness=min_effectiveness)

@router.get("/portfolio-risk")
async def analyze_portfolio_risk(db: AsyncSession = Depends(get_db)):
    """Analyze current portfolio risk exposure with recommendations."""
    return await HedgingService(db).analyze_portfolio_risk()

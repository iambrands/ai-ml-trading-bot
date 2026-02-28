"""Cross-Platform Odds Comparison API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.cross_platform_service import CrossPlatformService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/cross-platform", tags=["cross-platform"])


class CompareRequest(BaseModel):
    polymarket_id: str
    market_question: str
    polymarket_yes: float
    polymarket_no: float
    polymarket_volume: Optional[float] = None


@router.get("/comparisons")
async def get_comparisons(
    limit: int = Query(default=50, ge=1, le=200),
    arbitrage_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Get recent odds comparisons across platforms."""
    service = CrossPlatformService(db)
    return await service.get_comparisons(limit=limit, arbitrage_only=arbitrage_only)


@router.get("/arbitrage")
async def get_arbitrage_opportunities(
    min_profit_pct: float = Query(default=0.5, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get cross-platform arbitrage opportunities."""
    service = CrossPlatformService(db)
    return await service.get_arbitrage_opportunities(min_profit_pct=min_profit_pct)


@router.get("/spread-analysis")
async def get_spread_analysis(db: AsyncSession = Depends(get_db)):
    """Get spread analysis across platforms."""
    service = CrossPlatformService(db)
    return await service.get_spread_analysis()


@router.post("/compare")
async def compare_odds(request: CompareRequest, db: AsyncSession = Depends(get_db)):
    """Compare odds for a market across all platforms."""
    service = CrossPlatformService(db)
    result = await service.compare_odds(
        polymarket_id=request.polymarket_id,
        market_question=request.market_question,
        polymarket_yes=request.polymarket_yes,
        polymarket_no=request.polymarket_no,
        polymarket_volume=request.polymarket_volume,
    )
    return result or {"message": "Failed to compare odds"}

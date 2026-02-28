"""AI Market Summaries API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.ai_summary_service import AIMarketSummaryService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ai-summaries", tags=["ai-summaries"])


@router.get("")
async def get_latest_summaries(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get latest AI market summaries."""
    service = AIMarketSummaryService(db)
    return await service.get_latest_summaries(limit=limit)


@router.get("/by-recommendation/{recommendation}")
async def get_summaries_by_recommendation(
    recommendation: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get summaries filtered by recommendation (BUY_YES, BUY_NO, HOLD, AVOID)."""
    service = AIMarketSummaryService(db)
    return await service.get_summaries_by_recommendation(recommendation, limit=limit)


@router.get("/{market_id}")
async def get_market_summary(market_id: str, db: AsyncSession = Depends(get_db)):
    """Get the latest AI summary for a specific market."""
    service = AIMarketSummaryService(db)
    result = await service.get_summary(market_id)
    if not result:
        return {"market_id": market_id, "message": "No summary available. Generate one with POST."}
    return result


@router.post("/{market_id}/generate")
async def generate_market_summary(market_id: str, db: AsyncSession = Depends(get_db)):
    """Generate a new AI analysis summary for a market."""
    service = AIMarketSummaryService(db)
    result = await service.generate_summary(market_id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to generate summary - market data may be unavailable")
    return result

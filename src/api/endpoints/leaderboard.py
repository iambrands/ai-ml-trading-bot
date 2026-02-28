"""Leaderboard & Rankings API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.leaderboard_service import LeaderboardService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("")
async def get_leaderboard(
    period: str = Query(default="ALL_TIME", regex="^(DAILY|WEEKLY|MONTHLY|ALL_TIME)$"),
    sort_by: str = Query(default="profit"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get the trader leaderboard rankings."""
    service = LeaderboardService(db)
    return await service.get_leaderboard(period=period, sort_by=sort_by, limit=limit, offset=offset)


@router.post("/calculate")
async def calculate_rankings(
    period: str = Query(default="ALL_TIME", regex="^(DAILY|WEEKLY|MONTHLY|ALL_TIME)$"),
    db: AsyncSession = Depends(get_db),
):
    """Calculate and store fresh rankings."""
    service = LeaderboardService(db)
    entries = await service.calculate_rankings(period=period)
    return {"status": "calculated", "entries": len(entries), "period": period}


@router.get("/profile/{wallet_address}")
async def get_trader_profile(wallet_address: str, db: AsyncSession = Depends(get_db)):
    """Get detailed profile for a specific trader."""
    service = LeaderboardService(db)
    result = await service.get_trader_profile(wallet_address)
    if not result:
        raise HTTPException(status_code=404, detail="Trader not found")
    return result


@router.get("/search")
async def search_traders(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search traders by nickname or wallet address."""
    service = LeaderboardService(db)
    return await service.search_traders(query=q, limit=limit)

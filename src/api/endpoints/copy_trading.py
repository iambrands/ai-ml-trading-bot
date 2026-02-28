"""Copy Trading API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.copy_trading_service import CopyTradingService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/copy-trading", tags=["copy-trading"])


class FollowRequest(BaseModel):
    wallet_address: str
    nickname: Optional[str] = None
    auto_copy: bool = False
    copy_percentage: float = Field(default=100.0, ge=1, le=100)
    max_copy_size: float = Field(default=1000.0, ge=10)
    min_trade_size: float = Field(default=10.0, ge=1)


class CopySettingsUpdate(BaseModel):
    auto_copy: Optional[bool] = None
    copy_percentage: Optional[float] = Field(default=None, ge=1, le=100)
    max_copy_size: Optional[float] = Field(default=None, ge=10)


class CopyTradeRequest(BaseModel):
    profile_id: int
    market_id: str
    side: str
    source_size: float
    entry_price: float
    market_question: Optional[str] = None


@router.get("/profiles")
async def get_followed_profiles(
    only_active: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
):
    """Get all followed profiles."""
    service = CopyTradingService(db)
    return await service.get_followed_profiles(only_active=only_active)


@router.post("/follow")
async def follow_wallet(request: FollowRequest, db: AsyncSession = Depends(get_db)):
    """Start following a wallet for copy trading."""
    service = CopyTradingService(db)
    result = await service.follow_wallet(
        wallet_address=request.wallet_address,
        nickname=request.nickname,
        auto_copy=request.auto_copy,
        copy_percentage=request.copy_percentage,
        max_copy_size=request.max_copy_size,
        min_trade_size=request.min_trade_size,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to follow wallet")
    return result


@router.post("/unfollow/{wallet_address}")
async def unfollow_wallet(wallet_address: str, db: AsyncSession = Depends(get_db)):
    """Stop following a wallet."""
    service = CopyTradingService(db)
    success = await service.unfollow_wallet(wallet_address)
    if not success:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {"status": "unfollowed", "wallet_address": wallet_address}


@router.put("/settings/{wallet_address}")
async def update_copy_settings(
    wallet_address: str,
    request: CopySettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update copy trading settings for a followed wallet."""
    service = CopyTradingService(db)
    result = await service.update_copy_settings(
        wallet_address=wallet_address,
        auto_copy=request.auto_copy,
        copy_percentage=request.copy_percentage,
        max_copy_size=request.max_copy_size,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.post("/execute")
async def execute_copy_trade(request: CopyTradeRequest, db: AsyncSession = Depends(get_db)):
    """Execute a copy trade."""
    service = CopyTradingService(db)
    result = await service.execute_copy_trade(
        profile_id=request.profile_id,
        market_id=request.market_id,
        side=request.side,
        source_size=request.source_size,
        entry_price=request.entry_price,
        market_question=request.market_question,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Copy trade not executed")
    return result


@router.get("/trades")
async def get_copy_trades(
    wallet_address: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get copy trade history."""
    service = CopyTradingService(db)
    return await service.get_copy_trades(wallet_address=wallet_address, status=status, limit=limit)


@router.get("/stats")
async def get_copy_trading_stats(db: AsyncSession = Depends(get_db)):
    """Get copy trading statistics."""
    service = CopyTradingService(db)
    return await service.get_copy_trading_stats()


@router.get("/discover")
async def discover_top_traders(
    min_profit: float = Query(default=5000, ge=0),
    min_trades: int = Query(default=50, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Discover top-performing traders to follow."""
    service = CopyTradingService(db)
    return await service.discover_top_traders(min_profit=min_profit, min_trades=min_trades, limit=limit)

"""API endpoints for paper trading."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...database.models import Trade, PortfolioSnapshot, Signal
from ...services.paper_trading_service import PaperTradingService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/paper-trading", tags=["paper-trading"])


class PaperTradeCreate(BaseModel):
    """Paper trade creation model."""
    signal_id: int
    entry_price: float
    size: float


class PaperTradeResponse(BaseModel):
    """Paper trade response model."""
    id: int
    signal_id: Optional[int]
    market_id: str
    side: str
    entry_price: float
    size: float
    exit_price: Optional[float]
    pnl: Optional[float]
    status: str
    paper_trading: bool
    entry_time: datetime
    exit_time: Optional[datetime]

    class Config:
        from_attributes = True


class PaperPortfolioResponse(BaseModel):
    """Paper portfolio response model."""
    id: int
    snapshot_time: datetime
    total_value: float
    cash: float
    positions_value: float
    total_exposure: float
    daily_pnl: Optional[float]
    unrealized_pnl: Optional[float]
    realized_pnl: Optional[float]
    paper_trading: bool

    class Config:
        from_attributes = True


@router.post("/trades", response_model=PaperTradeResponse)
async def create_paper_trade(
    trade: PaperTradeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a paper trade."""
    try:
        # Get signal
        result = await db.execute(select(Signal).where(Signal.id == trade.signal_id))
        signal = result.scalar_one_or_none()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        # Create paper trade
        service = PaperTradingService(db)
        paper_trade = await service.create_paper_trade(signal, trade.entry_price, trade.size)
        
        if not paper_trade:
            raise HTTPException(status_code=400, detail="Failed to create paper trade (insufficient capital or other error)")
        
        return PaperTradeResponse.model_validate(paper_trade)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create paper trade", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create paper trade: {str(e)}")


@router.get("/trades", response_model=List[PaperTradeResponse])
async def get_paper_trades(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get paper trades."""
    try:
        query = select(Trade).where(Trade.paper_trading == True)
        
        if status:
            query = query.where(Trade.status == status.upper())
        
        query = query.order_by(Trade.entry_time.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        trades = result.scalars().all()
        return [PaperTradeResponse.model_validate(t) for t in trades]
    except Exception as e:
        logger.error("Failed to get paper trades", error=str(e))
        return []


@router.put("/trades/{trade_id}/close")
async def close_paper_trade(
    trade_id: int,
    exit_price: float = Query(..., description="Exit price for the trade"),
    db: AsyncSession = Depends(get_db),
):
    """Close a paper trade."""
    try:
        result = await db.execute(select(Trade).where(Trade.id == trade_id))
        trade = result.scalar_one_or_none()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        if not trade.paper_trading:
            raise HTTPException(status_code=400, detail="Trade is not a paper trade")
        
        service = PaperTradingService(db)
        success = await service.close_paper_trade(trade, exit_price)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to close paper trade")
        
        await db.refresh(trade)
        return PaperTradeResponse.model_validate(trade)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to close paper trade", trade_id=trade_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to close paper trade: {str(e)}")


@router.get("/portfolio", response_model=PaperPortfolioResponse)
async def get_paper_portfolio(db: AsyncSession = Depends(get_db)):
    """Get paper trading portfolio."""
    try:
        service = PaperTradingService(db)
        portfolio = await service.get_paper_portfolio()
        
        if not portfolio:
            # Initialize if doesn't exist
            portfolio = await service._initialize_paper_portfolio()
        
        return PaperPortfolioResponse.model_validate(portfolio)
    except Exception as e:
        logger.error("Failed to get paper portfolio", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get paper portfolio: {str(e)}")


@router.get("/portfolio/snapshots", response_model=List[PaperPortfolioResponse])
async def get_paper_portfolio_snapshots(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get paper trading portfolio snapshots."""
    try:
        query = select(PortfolioSnapshot).where(
            PortfolioSnapshot.paper_trading == True
        ).order_by(
            PortfolioSnapshot.snapshot_time.desc()
        ).limit(limit).offset(offset)
        
        result = await db.execute(query)
        snapshots = result.scalars().all()
        return [PaperPortfolioResponse.model_validate(s) for s in snapshots]
    except Exception as e:
        logger.error("Failed to get paper portfolio snapshots", error=str(e))
        return []


"""Multi-Strategy Engine API endpoints."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.strategy_engine import StrategyEngine
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/strategies", tags=["strategies"])


class StrategyUpdate(BaseModel):
    parameters: Optional[Dict] = None
    is_active: Optional[bool] = None


@router.get("")
async def get_strategies(db: AsyncSession = Depends(get_db)):
    """Get all trading strategies with performance metrics."""
    engine = StrategyEngine(db)
    return await engine.get_all_strategies()


@router.get("/performance")
async def get_strategy_performance(db: AsyncSession = Depends(get_db)):
    """Get combined performance across all strategies."""
    engine = StrategyEngine(db)
    return await engine.get_strategy_performance()


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single strategy by ID."""
    engine = StrategyEngine(db)
    result = await engine.get_strategy(strategy_id)
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return result


@router.post("/initialize")
async def initialize_strategies(db: AsyncSession = Depends(get_db)):
    """Initialize default trading strategies."""
    engine = StrategyEngine(db)
    return await engine.initialize_strategies()


@router.put("/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: int, is_active: bool = Query(...), db: AsyncSession = Depends(get_db)):
    """Enable or disable a strategy."""
    engine = StrategyEngine(db)
    result = await engine.toggle_strategy(strategy_id, is_active)
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return result


@router.put("/{strategy_id}/params")
async def update_strategy_params(
    strategy_id: int,
    update: StrategyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update strategy parameters."""
    engine = StrategyEngine(db)
    if update.parameters:
        result = await engine.update_strategy_params(strategy_id, update.parameters)
    elif update.is_active is not None:
        result = await engine.toggle_strategy(strategy_id, update.is_active)
    else:
        raise HTTPException(status_code=400, detail="No update provided")
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return result


@router.post("/{strategy_id}/run/trend-following")
async def run_trend_following(
    strategy_id: int,
    market_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Run trend following analysis on a market."""
    engine = StrategyEngine(db)
    from ...services.price_history_service import PriceHistoryService
    ph = PriceHistoryService(db)
    history = await ph.get_price_history(market_id, hours=48)
    prices = [h["yes_price"] for h in history]
    if len(prices) < 6:
        return {"market_id": market_id, "message": "Insufficient price data", "signal": None}
    result = await engine.run_trend_following(market_id, prices)
    return result or {"market_id": market_id, "signal": None, "message": "No signal generated"}


@router.post("/{strategy_id}/run/mean-reversion")
async def run_mean_reversion(
    strategy_id: int,
    market_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Run mean reversion analysis on a market."""
    engine = StrategyEngine(db)
    from ...services.price_history_service import PriceHistoryService
    ph = PriceHistoryService(db)
    history = await ph.get_price_history(market_id, hours=96)
    prices = [h["yes_price"] for h in history]
    if len(prices) < 10:
        return {"market_id": market_id, "message": "Insufficient price data", "signal": None}
    result = await engine.run_mean_reversion(market_id, prices)
    return result or {"market_id": market_id, "signal": None, "message": "No signal generated"}


@router.post("/{strategy_id}/run/momentum")
async def run_momentum(
    strategy_id: int,
    market_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Run momentum analysis on a market."""
    engine = StrategyEngine(db)
    from ...services.price_history_service import PriceHistoryService
    ph = PriceHistoryService(db)
    history = await ph.get_price_history(market_id, hours=24)
    prices = [h["yes_price"] for h in history]
    volumes = [h.get("volume", 0) for h in history]
    if len(prices) < 3:
        return {"market_id": market_id, "message": "Insufficient price data", "signal": None}
    result = await engine.run_momentum(market_id, prices, volumes)
    return result or {"market_id": market_id, "signal": None, "message": "No signal generated"}

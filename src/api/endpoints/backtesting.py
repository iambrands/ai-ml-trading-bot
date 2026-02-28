"""Advanced Backtesting Engine API endpoints."""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.backtesting_service import BacktestingService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/backtesting", tags=["backtesting"])


class RunBacktestRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    strategy_name: str
    strategy_params: Dict = Field(default_factory=dict)
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(default=10000.0, ge=100)


class CompareRequest(BaseModel):
    backtest_ids: List[int]


@router.get("/runs")
async def get_backtest_runs(
    strategy_name: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get backtest run history."""
    service = BacktestingService(db)
    return await service.get_backtest_runs(strategy_name=strategy_name, limit=limit)


@router.get("/runs/{backtest_id}")
async def get_backtest_detail(backtest_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed results for a specific backtest run."""
    service = BacktestingService(db)
    result = await service.get_backtest_detail(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return result


@router.post("/run")
async def run_backtest(request: RunBacktestRequest, db: AsyncSession = Depends(get_db)):
    """Run a new backtest."""
    if request.start_date >= request.end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    service = BacktestingService(db)
    result = await service.run_backtest(
        name=request.name,
        strategy_name=request.strategy_name,
        strategy_params=request.strategy_params,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Backtest failed")
    return result


@router.post("/compare")
async def compare_backtests(request: CompareRequest, db: AsyncSession = Depends(get_db)):
    """Compare multiple backtest runs side by side."""
    if len(request.backtest_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 backtests to compare")
    service = BacktestingService(db)
    return await service.compare_backtests(request.backtest_ids)


@router.delete("/runs/{backtest_id}")
async def delete_backtest(backtest_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a backtest run and its trades."""
    service = BacktestingService(db)
    success = await service.delete_backtest(backtest_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return {"status": "deleted", "backtest_id": backtest_id}

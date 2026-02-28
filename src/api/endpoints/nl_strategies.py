"""Natural Language Strategy Builder API endpoints."""
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db
from ...services.nl_strategy_service import NLStrategyService
router = APIRouter(prefix="/nl-strategies", tags=["nl-strategies"])

class CreateNLStrategy(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10, description="Describe your strategy in plain English")

class EvaluateMarket(BaseModel):
    market_data: Dict

@router.get("")
async def get_strategies(user_id: str = "default", active_only: bool = False, db: AsyncSession = Depends(get_db)):
    """Get all natural language strategies."""
    return await NLStrategyService(db).get_strategies(user_id=user_id, active_only=active_only)

@router.post("")
async def create_strategy(request: CreateNLStrategy, db: AsyncSession = Depends(get_db)):
    """Create a strategy from a plain English description. Example: 'Buy YES when price drops below 30 cents and RSI is oversold, sell at 60 cents with a 5% trailing stop'"""
    result = await NLStrategyService(db).create_strategy(name=request.name, description=request.description)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create strategy")
    return result

@router.get("/{strategy_id}")
async def get_strategy(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific NL strategy with its parsed rules."""
    result = await NLStrategyService(db).get_strategy(strategy_id)
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return result

@router.put("/{strategy_id}/activate")
async def activate(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """Activate a NL strategy for live signal generation."""
    result = await NLStrategyService(db).activate_strategy(strategy_id)
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return result

@router.put("/{strategy_id}/deactivate")
async def deactivate(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """Deactivate a NL strategy."""
    result = await NLStrategyService(db).deactivate_strategy(strategy_id)
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return result

@router.post("/{strategy_id}/evaluate")
async def evaluate_market(strategy_id: int, request: EvaluateMarket, db: AsyncSession = Depends(get_db)):
    """Evaluate whether a market matches the strategy's rules."""
    return await NLStrategyService(db).evaluate_market(strategy_id, request.market_data)

@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a NL strategy."""
    if not await NLStrategyService(db).delete_strategy(strategy_id):
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"status": "deleted"}

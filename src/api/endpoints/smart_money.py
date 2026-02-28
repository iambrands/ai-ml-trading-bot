"""Smart Money Conviction Scoring API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...database import get_db
from ...services.smart_money_service import SmartMoneyService
router = APIRouter(prefix="/smart-money", tags=["smart-money"])

@router.get("/top")
async def get_top_smart_money(grade: Optional[str] = None, limit: int = Query(default=25, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Get top-rated smart money wallets with conviction scores."""
    return await SmartMoneyService(db).get_top_smart_money(grade=grade, limit=limit)

@router.post("/score/{wallet_address}")
async def score_wallet(wallet_address: str, db: AsyncSession = Depends(get_db)):
    """Compute 7-layer conviction score for a wallet (S/A/B/C/D grading)."""
    result = await SmartMoneyService(db).score_wallet(wallet_address)
    return result or {"wallet_address": wallet_address, "message": "Insufficient trade data"}

@router.get("/grade-trade")
async def grade_trade(wallet_address: str = Query(...), market_id: str = Query(...), trade_value: float = Query(...), side: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Grade a single trade from A to D based on wallet conviction."""
    return await SmartMoneyService(db).grade_trade(wallet_address, market_id, trade_value, side)

@router.get("/flow")
async def get_smart_money_flow(market_id: Optional[str] = None, hours: int = Query(default=24, ge=1, le=168), db: AsyncSession = Depends(get_db)):
    """Track aggregate smart money buy/sell flow direction."""
    return await SmartMoneyService(db).get_smart_money_flow(market_id=market_id, hours=hours)

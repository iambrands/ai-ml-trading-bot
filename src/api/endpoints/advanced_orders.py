"""Advanced Order Management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.advanced_orders_service import AdvancedOrdersService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/orders", tags=["advanced-orders"])


class TrailingStopRequest(BaseModel):
    trade_id: int
    market_id: str
    side: str
    size: float
    trail_pct: float = Field(default=0.05, ge=0.01, le=0.50)
    trail_amount: Optional[float] = None


class TakeProfitRequest(BaseModel):
    trade_id: int
    market_id: str
    side: str
    size: float
    take_profit_price: float = Field(ge=0.01, le=0.99)


class StopLossRequest(BaseModel):
    trade_id: int
    market_id: str
    side: str
    size: float
    stop_loss_price: float = Field(ge=0.01, le=0.99)


class BracketOrderRequest(BaseModel):
    trade_id: int
    market_id: str
    side: str
    size: float
    take_profit_price: float = Field(ge=0.01, le=0.99)
    stop_loss_price: float = Field(ge=0.01, le=0.99)


class OCORequest(BaseModel):
    market_id: str
    side: str
    size: float
    take_profit_price: float = Field(ge=0.01, le=0.99)
    stop_loss_price: float = Field(ge=0.01, le=0.99)


@router.get("")
async def get_orders(
    market_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get all advanced orders."""
    service = AdvancedOrdersService(db)
    return await service.get_all_orders(market_id=market_id, status=status, limit=limit)


@router.get("/active")
async def get_active_orders(
    market_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get all active advanced orders."""
    service = AdvancedOrdersService(db)
    return await service.get_active_orders(market_id=market_id, limit=limit)


@router.post("/trailing-stop")
async def create_trailing_stop(request: TrailingStopRequest, db: AsyncSession = Depends(get_db)):
    """Create a trailing stop-loss order."""
    service = AdvancedOrdersService(db)
    result = await service.create_trailing_stop(
        trade_id=request.trade_id,
        market_id=request.market_id,
        side=request.side,
        size=request.size,
        trail_pct=request.trail_pct,
        trail_amount=request.trail_amount,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create trailing stop")
    return result


@router.post("/take-profit")
async def create_take_profit(request: TakeProfitRequest, db: AsyncSession = Depends(get_db)):
    """Create a take-profit order."""
    service = AdvancedOrdersService(db)
    result = await service.create_take_profit(
        trade_id=request.trade_id,
        market_id=request.market_id,
        side=request.side,
        size=request.size,
        take_profit_price=request.take_profit_price,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create take profit")
    return result


@router.post("/stop-loss")
async def create_stop_loss(request: StopLossRequest, db: AsyncSession = Depends(get_db)):
    """Create a stop-loss order."""
    service = AdvancedOrdersService(db)
    result = await service.create_stop_loss(
        trade_id=request.trade_id,
        market_id=request.market_id,
        side=request.side,
        size=request.size,
        stop_loss_price=request.stop_loss_price,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create stop loss")
    return result


@router.post("/bracket")
async def create_bracket_order(request: BracketOrderRequest, db: AsyncSession = Depends(get_db)):
    """Create a bracket order (take-profit + stop-loss)."""
    service = AdvancedOrdersService(db)
    result = await service.create_bracket_order(
        trade_id=request.trade_id,
        market_id=request.market_id,
        side=request.side,
        size=request.size,
        take_profit_price=request.take_profit_price,
        stop_loss_price=request.stop_loss_price,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create bracket order")
    return result


@router.post("/oco")
async def create_oco_order(request: OCORequest, db: AsyncSession = Depends(get_db)):
    """Create an OCO (One-Cancels-Other) order."""
    service = AdvancedOrdersService(db)
    result = await service.create_oco_order(
        market_id=request.market_id,
        side=request.side,
        size=request.size,
        take_profit_price=request.take_profit_price,
        stop_loss_price=request.stop_loss_price,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create OCO order")
    return result


@router.post("/check/{market_id}")
async def check_orders(
    market_id: str,
    current_price: float = Query(..., ge=0.01, le=0.99),
    db: AsyncSession = Depends(get_db),
):
    """Check and trigger orders for a market at current price."""
    service = AdvancedOrdersService(db)
    return await service.check_and_trigger_orders(market_id, current_price)


@router.delete("/{order_id}")
async def cancel_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel an active order."""
    service = AdvancedOrdersService(db)
    success = await service.cancel_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found or not active")
    return {"status": "cancelled", "order_id": order_id}

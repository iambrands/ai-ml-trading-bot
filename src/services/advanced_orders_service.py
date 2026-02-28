"""Advanced Order Management - Trailing stops, take-profit, OCO, bracket orders."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import desc, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import AdvancedOrder, Trade
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AdvancedOrdersService:
    """Service for managing advanced order types."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_trailing_stop(
        self,
        trade_id: int,
        market_id: str,
        side: str,
        size: float,
        trail_pct: float = 0.05,
        trail_amount: Optional[float] = None,
    ) -> Optional[Dict]:
        """Create a trailing stop-loss order."""
        try:
            order = AdvancedOrder(
                trade_id=trade_id,
                market_id=market_id,
                order_type="TRAILING_STOP",
                side=side,
                trail_pct=trail_pct,
                trail_amount=trail_amount,
                size=size,
                status="ACTIVE",
            )
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            logger.info("Created trailing stop", market=market_id, trail_pct=trail_pct)
            return self._order_to_dict(order)
        except Exception as e:
            logger.error("Failed to create trailing stop", error=str(e))
            await self.db.rollback()
            return None

    async def create_take_profit(
        self,
        trade_id: int,
        market_id: str,
        side: str,
        size: float,
        take_profit_price: float,
    ) -> Optional[Dict]:
        """Create a take-profit order."""
        try:
            order = AdvancedOrder(
                trade_id=trade_id,
                market_id=market_id,
                order_type="TAKE_PROFIT",
                side=side,
                take_profit_price=take_profit_price,
                size=size,
                status="ACTIVE",
            )
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            return self._order_to_dict(order)
        except Exception as e:
            logger.error("Failed to create take profit", error=str(e))
            await self.db.rollback()
            return None

    async def create_stop_loss(
        self,
        trade_id: int,
        market_id: str,
        side: str,
        size: float,
        stop_loss_price: float,
    ) -> Optional[Dict]:
        """Create a stop-loss order."""
        try:
            order = AdvancedOrder(
                trade_id=trade_id,
                market_id=market_id,
                order_type="STOP_LOSS",
                side=side,
                stop_loss_price=stop_loss_price,
                size=size,
                status="ACTIVE",
            )
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            return self._order_to_dict(order)
        except Exception as e:
            logger.error("Failed to create stop loss", error=str(e))
            await self.db.rollback()
            return None

    async def create_bracket_order(
        self,
        trade_id: int,
        market_id: str,
        side: str,
        size: float,
        take_profit_price: float,
        stop_loss_price: float,
    ) -> Optional[Dict]:
        """Create a bracket order (combined take-profit + stop-loss)."""
        try:
            order = AdvancedOrder(
                trade_id=trade_id,
                market_id=market_id,
                order_type="BRACKET",
                side=side,
                take_profit_price=take_profit_price,
                stop_loss_price=stop_loss_price,
                size=size,
                status="ACTIVE",
            )
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            logger.info("Created bracket order", market=market_id, tp=take_profit_price, sl=stop_loss_price)
            return self._order_to_dict(order)
        except Exception as e:
            logger.error("Failed to create bracket order", error=str(e))
            await self.db.rollback()
            return None

    async def create_oco_order(
        self,
        market_id: str,
        side: str,
        size: float,
        take_profit_price: float,
        stop_loss_price: float,
    ) -> Optional[Dict]:
        """Create an OCO (One-Cancels-Other) order."""
        try:
            order = AdvancedOrder(
                market_id=market_id,
                order_type="OCO",
                side=side,
                take_profit_price=take_profit_price,
                stop_loss_price=stop_loss_price,
                size=size,
                status="ACTIVE",
            )
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            return self._order_to_dict(order)
        except Exception as e:
            logger.error("Failed to create OCO order", error=str(e))
            await self.db.rollback()
            return None

    async def check_and_trigger_orders(self, market_id: str, current_price: float) -> List[Dict]:
        """Check active orders against current price and trigger if conditions met."""
        triggered = []
        try:
            result = await self.db.execute(
                select(AdvancedOrder).where(
                    AdvancedOrder.market_id == market_id,
                    AdvancedOrder.status == "ACTIVE",
                )
            )
            orders = result.scalars().all()

            for order in orders:
                should_trigger = False

                if order.order_type == "TRAILING_STOP":
                    should_trigger = self._check_trailing_stop(order, current_price)
                elif order.order_type == "TAKE_PROFIT":
                    if order.side == "YES" and current_price >= float(order.take_profit_price):
                        should_trigger = True
                    elif order.side == "NO" and current_price <= float(order.take_profit_price):
                        should_trigger = True
                elif order.order_type == "STOP_LOSS":
                    if order.side == "YES" and current_price <= float(order.stop_loss_price):
                        should_trigger = True
                    elif order.side == "NO" and current_price >= float(order.stop_loss_price):
                        should_trigger = True
                elif order.order_type in ("BRACKET", "OCO"):
                    if order.side == "YES":
                        if order.take_profit_price and current_price >= float(order.take_profit_price):
                            should_trigger = True
                        elif order.stop_loss_price and current_price <= float(order.stop_loss_price):
                            should_trigger = True
                    else:
                        if order.take_profit_price and current_price <= float(order.take_profit_price):
                            should_trigger = True
                        elif order.stop_loss_price and current_price >= float(order.stop_loss_price):
                            should_trigger = True

                if should_trigger:
                    order.status = "TRIGGERED"
                    order.triggered_at = datetime.now(timezone.utc)
                    triggered.append(self._order_to_dict(order))
                    logger.info("Order triggered", order_id=order.id, type=order.order_type, price=current_price)
                else:
                    self._update_tracking_prices(order, current_price)

            if triggered:
                await self.db.commit()

            return triggered
        except Exception as e:
            logger.error("Failed to check orders", market=market_id, error=str(e))
            await self.db.rollback()
            return []

    def _check_trailing_stop(self, order: AdvancedOrder, current_price: float) -> bool:
        """Check if trailing stop should trigger."""
        if order.side == "YES":
            if order.highest_price is None or current_price > float(order.highest_price):
                order.highest_price = current_price
            highest = float(order.highest_price)
            if order.trail_pct:
                trigger_price = highest * (1 - float(order.trail_pct))
            elif order.trail_amount:
                trigger_price = highest - float(order.trail_amount)
            else:
                return False
            return current_price <= trigger_price
        else:
            if order.lowest_price is None or current_price < float(order.lowest_price):
                order.lowest_price = current_price
            lowest = float(order.lowest_price)
            if order.trail_pct:
                trigger_price = lowest * (1 + float(order.trail_pct))
            elif order.trail_amount:
                trigger_price = lowest + float(order.trail_amount)
            else:
                return False
            return current_price >= trigger_price

    def _update_tracking_prices(self, order: AdvancedOrder, current_price: float):
        """Update highest/lowest tracking prices for trailing stops."""
        if order.order_type == "TRAILING_STOP":
            if order.side == "YES":
                if order.highest_price is None or current_price > float(order.highest_price or 0):
                    order.highest_price = current_price
            else:
                if order.lowest_price is None or current_price < float(order.lowest_price or 999):
                    order.lowest_price = current_price

    async def get_active_orders(self, market_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get all active advanced orders."""
        try:
            query = select(AdvancedOrder).where(AdvancedOrder.status == "ACTIVE")
            if market_id:
                query = query.where(AdvancedOrder.market_id == market_id)
            query = query.order_by(desc(AdvancedOrder.created_at)).limit(limit)

            result = await self.db.execute(query)
            orders = result.scalars().all()
            return [self._order_to_dict(o) for o in orders]
        except Exception as e:
            logger.error("Failed to get active orders", error=str(e))
            return []

    async def get_all_orders(self, market_id: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get all advanced orders with optional filters."""
        try:
            query = select(AdvancedOrder)
            if market_id:
                query = query.where(AdvancedOrder.market_id == market_id)
            if status:
                query = query.where(AdvancedOrder.status == status.upper())
            query = query.order_by(desc(AdvancedOrder.created_at)).limit(limit)

            result = await self.db.execute(query)
            orders = result.scalars().all()
            return [self._order_to_dict(o) for o in orders]
        except Exception as e:
            logger.error("Failed to get orders", error=str(e))
            return []

    async def cancel_order(self, order_id: int) -> bool:
        """Cancel an active order."""
        try:
            result = await self.db.execute(
                update(AdvancedOrder)
                .where(AdvancedOrder.id == order_id, AdvancedOrder.status == "ACTIVE")
                .values(status="CANCELLED")
            )
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error("Failed to cancel order", order_id=order_id, error=str(e))
            await self.db.rollback()
            return False

    def _order_to_dict(self, order: AdvancedOrder) -> Dict:
        return {
            "id": order.id,
            "trade_id": order.trade_id,
            "market_id": order.market_id,
            "order_type": order.order_type,
            "side": order.side,
            "trigger_price": float(order.trigger_price) if order.trigger_price else None,
            "trail_amount": float(order.trail_amount) if order.trail_amount else None,
            "trail_pct": float(order.trail_pct) if order.trail_pct else None,
            "take_profit_price": float(order.take_profit_price) if order.take_profit_price else None,
            "stop_loss_price": float(order.stop_loss_price) if order.stop_loss_price else None,
            "highest_price": float(order.highest_price) if order.highest_price else None,
            "lowest_price": float(order.lowest_price) if order.lowest_price else None,
            "size": float(order.size),
            "status": order.status,
            "triggered_at": order.triggered_at.isoformat() if order.triggered_at else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }

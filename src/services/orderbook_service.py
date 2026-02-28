"""Live Order Book Depth Analysis Service."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import OrderBookSnapshot
from ..utils.logging import get_logger

logger = get_logger(__name__)


class OrderBookService:
    """Service for order book depth analysis and market microstructure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_snapshot(
        self,
        market_id: str,
        bids: List[Dict],
        asks: List[Dict],
    ) -> Optional[Dict]:
        """Save an order book snapshot with computed metrics."""
        try:
            best_bid = bids[0]["price"] if bids else None
            best_ask = asks[0]["price"] if asks else None
            mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else None
            spread = best_ask - best_bid if best_bid and best_ask else None
            spread_pct = (spread / mid_price * 100) if spread and mid_price else None

            bid_depth_10 = sum(b.get("size", 0) for b in bids if b.get("price", 0) >= (best_bid or 0) * 0.9) if bids else 0
            ask_depth_10 = sum(a.get("size", 0) for a in asks if a.get("price", 0) <= (best_ask or 999) * 1.1) if asks else 0

            total_bid = sum(b.get("size", 0) * b.get("price", 0) for b in bids)
            total_ask = sum(a.get("size", 0) * a.get("price", 0) for a in asks)
            imbalance = (total_bid - total_ask) / (total_bid + total_ask) if (total_bid + total_ask) > 0 else 0

            snapshot = OrderBookSnapshot(
                market_id=market_id,
                bids=bids,
                asks=asks,
                best_bid=best_bid,
                best_ask=best_ask,
                mid_price=mid_price,
                spread=spread,
                spread_pct=spread_pct,
                bid_depth_10pct=bid_depth_10,
                ask_depth_10pct=ask_depth_10,
                imbalance_ratio=imbalance,
                total_bid_volume=total_bid,
                total_ask_volume=total_ask,
                snapshot_time=datetime.now(timezone.utc),
            )
            self.db.add(snapshot)
            await self.db.commit()
            await self.db.refresh(snapshot)
            return self._snapshot_to_dict(snapshot)
        except Exception as e:
            logger.error("Failed to save orderbook snapshot", error=str(e))
            await self.db.rollback()
            return None

    async def get_latest_snapshot(self, market_id: str) -> Optional[Dict]:
        """Get the latest order book snapshot for a market."""
        try:
            result = await self.db.execute(
                select(OrderBookSnapshot)
                .where(OrderBookSnapshot.market_id == market_id)
                .order_by(desc(OrderBookSnapshot.snapshot_time))
                .limit(1)
            )
            snapshot = result.scalar_one_or_none()
            return self._snapshot_to_dict(snapshot) if snapshot else None
        except Exception as e:
            logger.error("Failed to get orderbook snapshot", error=str(e))
            return None

    async def get_depth_chart_data(self, market_id: str) -> Optional[Dict]:
        """Get order book data formatted for depth chart visualization."""
        try:
            result = await self.db.execute(
                select(OrderBookSnapshot)
                .where(OrderBookSnapshot.market_id == market_id)
                .order_by(desc(OrderBookSnapshot.snapshot_time))
                .limit(1)
            )
            snapshot = result.scalar_one_or_none()
            if not snapshot:
                return None

            bids = sorted(snapshot.bids or [], key=lambda x: x.get("price", 0), reverse=True)
            asks = sorted(snapshot.asks or [], key=lambda x: x.get("price", 0))

            cum_bid_volume = 0
            bid_depth = []
            for b in bids:
                cum_bid_volume += b.get("size", 0)
                bid_depth.append({"price": b.get("price"), "cumulative_volume": cum_bid_volume})

            cum_ask_volume = 0
            ask_depth = []
            for a in asks:
                cum_ask_volume += a.get("size", 0)
                ask_depth.append({"price": a.get("price"), "cumulative_volume": cum_ask_volume})

            return {
                "market_id": market_id,
                "bid_depth": bid_depth,
                "ask_depth": ask_depth,
                "best_bid": float(snapshot.best_bid) if snapshot.best_bid else None,
                "best_ask": float(snapshot.best_ask) if snapshot.best_ask else None,
                "mid_price": float(snapshot.mid_price) if snapshot.mid_price else None,
                "spread": float(snapshot.spread) if snapshot.spread else None,
                "spread_pct": float(snapshot.spread_pct) if snapshot.spread_pct else None,
                "imbalance_ratio": float(snapshot.imbalance_ratio) if snapshot.imbalance_ratio else None,
                "timestamp": snapshot.snapshot_time.isoformat() if snapshot.snapshot_time else None,
            }
        except Exception as e:
            logger.error("Failed to get depth chart data", error=str(e))
            return None

    async def get_spread_history(self, market_id: str, hours: int = 24) -> List[Dict]:
        """Get historical spread data for a market."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(
                    OrderBookSnapshot.snapshot_time,
                    OrderBookSnapshot.spread,
                    OrderBookSnapshot.spread_pct,
                    OrderBookSnapshot.mid_price,
                    OrderBookSnapshot.imbalance_ratio,
                )
                .where(
                    OrderBookSnapshot.market_id == market_id,
                    OrderBookSnapshot.snapshot_time >= cutoff,
                )
                .order_by(OrderBookSnapshot.snapshot_time)
            )
            rows = result.all()
            return [
                {
                    "timestamp": row[0].isoformat(),
                    "spread": float(row[1]) if row[1] else None,
                    "spread_pct": float(row[2]) if row[2] else None,
                    "mid_price": float(row[3]) if row[3] else None,
                    "imbalance_ratio": float(row[4]) if row[4] else None,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get spread history", error=str(e))
            return []

    async def analyze_market_microstructure(self, market_id: str) -> Dict:
        """Analyze market microstructure from order book data."""
        try:
            result = await self.db.execute(
                select(OrderBookSnapshot)
                .where(OrderBookSnapshot.market_id == market_id)
                .order_by(desc(OrderBookSnapshot.snapshot_time))
                .limit(50)
            )
            snapshots = result.scalars().all()

            if not snapshots:
                return {"market_id": market_id, "message": "No order book data available"}

            spreads = [float(s.spread) for s in snapshots if s.spread]
            imbalances = [float(s.imbalance_ratio) for s in snapshots if s.imbalance_ratio]
            mid_prices = [float(s.mid_price) for s in snapshots if s.mid_price]

            avg_spread = sum(spreads) / len(spreads) if spreads else 0
            avg_imbalance = sum(imbalances) / len(imbalances) if imbalances else 0

            volatility = 0
            if len(mid_prices) >= 2:
                returns = [(mid_prices[i] - mid_prices[i-1]) / mid_prices[i-1] for i in range(1, len(mid_prices)) if mid_prices[i-1] != 0]
                if returns:
                    mean_ret = sum(returns) / len(returns)
                    volatility = (sum((r - mean_ret) ** 2 for r in returns) / len(returns)) ** 0.5

            liquidity_score = min(100, int((1 - min(avg_spread, 0.1) / 0.1) * 100)) if avg_spread else 50

            return {
                "market_id": market_id,
                "data_points": len(snapshots),
                "avg_spread": round(avg_spread, 6),
                "avg_imbalance": round(avg_imbalance, 4),
                "price_volatility": round(volatility, 6),
                "liquidity_score": liquidity_score,
                "liquidity_grade": "A" if liquidity_score >= 80 else "B" if liquidity_score >= 60 else "C" if liquidity_score >= 40 else "D",
                "bid_pressure": "STRONG" if avg_imbalance > 0.2 else "WEAK" if avg_imbalance < -0.2 else "NEUTRAL",
                "latest_snapshot": self._snapshot_to_dict(snapshots[0]) if snapshots else None,
            }
        except Exception as e:
            logger.error("Failed to analyze microstructure", error=str(e))
            return {"market_id": market_id, "error": str(e)}

    def _snapshot_to_dict(self, snapshot: OrderBookSnapshot) -> Dict:
        return {
            "id": snapshot.id,
            "market_id": snapshot.market_id,
            "best_bid": float(snapshot.best_bid) if snapshot.best_bid else None,
            "best_ask": float(snapshot.best_ask) if snapshot.best_ask else None,
            "mid_price": float(snapshot.mid_price) if snapshot.mid_price else None,
            "spread": float(snapshot.spread) if snapshot.spread else None,
            "spread_pct": float(snapshot.spread_pct) if snapshot.spread_pct else None,
            "bid_depth_10pct": float(snapshot.bid_depth_10pct) if snapshot.bid_depth_10pct else None,
            "ask_depth_10pct": float(snapshot.ask_depth_10pct) if snapshot.ask_depth_10pct else None,
            "imbalance_ratio": float(snapshot.imbalance_ratio) if snapshot.imbalance_ratio else None,
            "total_bid_volume": float(snapshot.total_bid_volume) if snapshot.total_bid_volume else None,
            "total_ask_volume": float(snapshot.total_ask_volume) if snapshot.total_ask_volume else None,
            "bid_levels": len(snapshot.bids) if snapshot.bids else 0,
            "ask_levels": len(snapshot.asks) if snapshot.asks else 0,
            "timestamp": snapshot.snapshot_time.isoformat() if snapshot.snapshot_time else None,
        }

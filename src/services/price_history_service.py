"""Price History & Technical Analysis Service."""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import PriceHistory, TechnicalIndicator
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PriceHistoryService:
    """Service for price history tracking and technical analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_price(
        self,
        market_id: str,
        yes_price: float,
        no_price: float,
        volume: float = 0,
        liquidity: float = 0,
        bid_price: Optional[float] = None,
        ask_price: Optional[float] = None,
        open_interest: Optional[float] = None,
        interval: str = "1h",
    ) -> Optional[Dict]:
        """Record a price data point."""
        try:
            now = datetime.now(timezone.utc)
            spread = (ask_price - bid_price) if bid_price and ask_price else None

            price = PriceHistory(
                market_id=market_id,
                yes_price=yes_price,
                no_price=no_price,
                volume=volume,
                liquidity=liquidity,
                bid_price=bid_price,
                ask_price=ask_price,
                spread=spread,
                open_interest=open_interest,
                interval=interval,
                timestamp=now,
            )
            self.db.add(price)
            await self.db.commit()
            return self._price_to_dict(price)
        except Exception as e:
            logger.error("Failed to record price", market=market_id, error=str(e))
            await self.db.rollback()
            return None

    async def get_price_history(
        self,
        market_id: str,
        hours: int = 168,
        interval: str = "1h",
        limit: int = 500,
    ) -> List[Dict]:
        """Get price history for a market."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(PriceHistory)
                .where(
                    PriceHistory.market_id == market_id,
                    PriceHistory.interval == interval,
                    PriceHistory.timestamp >= cutoff,
                )
                .order_by(PriceHistory.timestamp)
                .limit(limit)
            )
            prices = result.scalars().all()
            return [self._price_to_dict(p) for p in prices]
        except Exception as e:
            logger.error("Failed to get price history", market=market_id, error=str(e))
            return []

    async def compute_indicators(self, market_id: str, hours: int = 168) -> Dict:
        """Compute all technical indicators for a market."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(PriceHistory)
                .where(
                    PriceHistory.market_id == market_id,
                    PriceHistory.timestamp >= cutoff,
                )
                .order_by(PriceHistory.timestamp)
            )
            prices = result.scalars().all()

            if len(prices) < 3:
                return {"market_id": market_id, "indicators": {}, "message": "Insufficient data"}

            yes_prices = [float(p.yes_price) for p in prices]
            volumes = [float(p.volume) for p in prices]
            timestamps = [p.timestamp.isoformat() for p in prices]

            indicators = {}

            for period in [7, 14, 20, 50]:
                sma = self._sma(yes_prices, period)
                if sma is not None:
                    indicators[f"sma_{period}"] = round(sma, 6)

            for period in [12, 26]:
                ema = self._ema(yes_prices, period)
                if ema is not None:
                    indicators[f"ema_{period}"] = round(ema, 6)

            rsi = self._rsi(yes_prices)
            if rsi is not None:
                indicators["rsi_14"] = round(rsi, 2)

            macd_data = self._macd(yes_prices)
            if macd_data:
                indicators["macd"] = {k: round(v, 6) for k, v in macd_data.items()}

            bb = self._bollinger_bands(yes_prices)
            if bb:
                indicators["bollinger"] = {k: round(v, 6) for k, v in bb.items()}

            vwap = self._vwap(yes_prices, volumes)
            if vwap is not None:
                indicators["vwap"] = round(vwap, 6)

            indicators["current_price"] = yes_prices[-1]
            indicators["price_change_24h"] = round(
                (yes_prices[-1] - yes_prices[-min(24, len(yes_prices))]) / yes_prices[-min(24, len(yes_prices))] * 100, 2
            ) if len(yes_prices) >= 2 else 0

            signal = self._generate_technical_signal(indicators)

            return {
                "market_id": market_id,
                "indicators": indicators,
                "signal": signal,
                "data_points": len(prices),
                "timespan_hours": hours,
            }
        except Exception as e:
            logger.error("Failed to compute indicators", market=market_id, error=str(e))
            return {"market_id": market_id, "indicators": {}, "error": str(e)}

    def _sma(self, prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    def _ema(self, prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return ema

    def _rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        if len(prices) < period + 1:
            return None
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        recent = deltas[-period:]
        gains = [d if d > 0 else 0 for d in recent]
        losses = [-d if d < 0 else 0 for d in recent]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _macd(self, prices: List[float]) -> Optional[Dict]:
        if len(prices) < 26:
            return None
        ema_12 = self._ema(prices, 12)
        ema_26 = self._ema(prices, 26)
        if ema_12 is None or ema_26 is None:
            return None
        macd_line = ema_12 - ema_26
        signal_line = self._ema(prices[-9:], 9) if len(prices) >= 9 else macd_line
        histogram = macd_line - (signal_line or 0)
        return {"macd_line": macd_line, "signal_line": signal_line or 0, "histogram": histogram}

    def _bollinger_bands(self, prices: List[float], period: int = 20, num_std: float = 2.0) -> Optional[Dict]:
        if len(prices) < period:
            return None
        recent = prices[-period:]
        middle = sum(recent) / period
        variance = sum((p - middle) ** 2 for p in recent) / period
        std = math.sqrt(variance)
        return {
            "upper": middle + num_std * std,
            "middle": middle,
            "lower": middle - num_std * std,
            "bandwidth": (2 * num_std * std) / middle if middle != 0 else 0,
        }

    def _vwap(self, prices: List[float], volumes: List[float]) -> Optional[float]:
        if not prices or not volumes or len(prices) != len(volumes):
            return None
        total_volume = sum(volumes)
        if total_volume == 0:
            return None
        return sum(p * v for p, v in zip(prices, volumes)) / total_volume

    def _generate_technical_signal(self, indicators: Dict) -> Dict:
        """Generate trading signal from technical indicators."""
        signals = {"bullish": 0, "bearish": 0, "neutral": 0}

        rsi = indicators.get("rsi_14")
        if rsi is not None:
            if rsi < 30:
                signals["bullish"] += 2
            elif rsi > 70:
                signals["bearish"] += 2
            else:
                signals["neutral"] += 1

        macd = indicators.get("macd")
        if macd:
            if macd.get("histogram", 0) > 0:
                signals["bullish"] += 1
            elif macd.get("histogram", 0) < 0:
                signals["bearish"] += 1

        bb = indicators.get("bollinger")
        current = indicators.get("current_price", 0)
        if bb and current:
            if current < bb.get("lower", 0):
                signals["bullish"] += 2
            elif current > bb.get("upper", 999):
                signals["bearish"] += 2
            else:
                signals["neutral"] += 1

        sma_20 = indicators.get("sma_20")
        if sma_20 and current:
            if current > sma_20:
                signals["bullish"] += 1
            else:
                signals["bearish"] += 1

        total = sum(signals.values())
        if total == 0:
            return {"direction": "NEUTRAL", "strength": 0, "breakdown": signals}

        if signals["bullish"] > signals["bearish"]:
            direction = "BULLISH"
            strength = signals["bullish"] / total
        elif signals["bearish"] > signals["bullish"]:
            direction = "BEARISH"
            strength = signals["bearish"] / total
        else:
            direction = "NEUTRAL"
            strength = 0.5

        return {
            "direction": direction,
            "strength": round(strength, 2),
            "breakdown": signals,
        }

    def _price_to_dict(self, price: PriceHistory) -> Dict:
        return {
            "market_id": price.market_id,
            "yes_price": float(price.yes_price),
            "no_price": float(price.no_price),
            "volume": float(price.volume),
            "liquidity": float(price.liquidity),
            "bid_price": float(price.bid_price) if price.bid_price else None,
            "ask_price": float(price.ask_price) if price.ask_price else None,
            "spread": float(price.spread) if price.spread else None,
            "open_interest": float(price.open_interest) if price.open_interest else None,
            "interval": price.interval,
            "timestamp": price.timestamp.isoformat() if price.timestamp else None,
        }

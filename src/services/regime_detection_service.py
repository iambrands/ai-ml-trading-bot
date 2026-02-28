"""Market Regime Detection - Automatically identify market states and adapt strategies.

Detects whether a market is trending, mean-reverting, volatile, or choppy,
and recommends which strategy to use. Enables the platform to automatically
switch between strategies based on detected regime.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import MarketRegime, PriceHistory
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RegimeDetectionService:
    """Detects market regimes for adaptive strategy selection."""

    REGIME_STRATEGIES = {
        "TRENDING_UP": "TREND_FOLLOWING",
        "TRENDING_DOWN": "TREND_FOLLOWING",
        "MEAN_REVERTING": "MEAN_REVERSION",
        "HIGH_VOLATILITY": "MOMENTUM",
        "LOW_VOLATILITY": "ARBITRAGE",
        "CHOPPY": "ML_ENSEMBLE",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_regime(self, market_id: str, lookback_hours: int = 48) -> Optional[Dict]:
        """Detect the current market regime for a given market."""
        try:
            prices = await self._get_prices(market_id, lookback_hours)
            if len(prices) < 10:
                return None

            volatility = self._compute_volatility(prices)
            trend = self._compute_trend(prices)
            mean_rev = self._compute_mean_reversion_speed(prices)
            hurst = self._compute_hurst_exponent(prices)

            regime, confidence = self._classify_regime(volatility, trend, mean_rev, hurst)
            recommended = self.REGIME_STRATEGIES.get(regime, "ML_ENSEMBLE")

            record = MarketRegime(
                market_id=market_id,
                regime_type=regime,
                confidence=round(confidence, 4),
                volatility=round(volatility, 6),
                trend_strength=round(trend, 6),
                mean_reversion_speed=round(mean_rev, 6),
                recommended_strategy=recommended,
                lookback_hours=lookback_hours,
                features={"hurst": round(hurst, 4), "data_points": len(prices), "price_range": [min(prices), max(prices)]},
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)

            return self._regime_to_dict(record)
        except Exception as e:
            logger.error("Failed to detect regime", market=market_id, error=str(e))
            await self.db.rollback()
            return None

    async def get_regime(self, market_id: str) -> Optional[Dict]:
        """Get the latest detected regime for a market."""
        try:
            result = await self.db.execute(
                select(MarketRegime)
                .where(MarketRegime.market_id == market_id)
                .order_by(desc(MarketRegime.detected_at))
                .limit(1)
            )
            regime = result.scalar_one_or_none()
            return self._regime_to_dict(regime) if regime else None
        except Exception as e:
            logger.error("Failed to get regime", error=str(e))
            return None

    async def get_regime_history(self, market_id: str, limit: int = 20) -> List[Dict]:
        """Get regime history for a market."""
        try:
            result = await self.db.execute(
                select(MarketRegime)
                .where(MarketRegime.market_id == market_id)
                .order_by(desc(MarketRegime.detected_at))
                .limit(limit)
            )
            regimes = result.scalars().all()
            return [self._regime_to_dict(r) for r in regimes]
        except Exception as e:
            logger.error("Failed to get regime history", error=str(e))
            return []

    async def get_regime_distribution(self) -> Dict:
        """Get distribution of regimes across all markets."""
        try:
            result = await self.db.execute(
                select(MarketRegime).order_by(desc(MarketRegime.detected_at)).limit(500)
            )
            regimes = result.scalars().all()
            seen = set()
            latest = []
            for r in regimes:
                if r.market_id not in seen:
                    seen.add(r.market_id)
                    latest.append(r)

            distribution = {}
            for r in latest:
                rt = r.regime_type
                distribution[rt] = distribution.get(rt, 0) + 1

            return {
                "total_markets_analyzed": len(latest),
                "distribution": distribution,
                "recommended_strategies": {rt: self.REGIME_STRATEGIES.get(rt, "ML_ENSEMBLE") for rt in distribution},
            }
        except Exception as e:
            logger.error("Failed to get regime distribution", error=str(e))
            return {"total_markets_analyzed": 0, "distribution": {}}

    def _compute_volatility(self, prices: List[float]) -> float:
        if len(prices) < 2:
            return 0
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices)) if prices[i-1] != 0]
        if not returns:
            return 0
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance)

    def _compute_trend(self, prices: List[float]) -> float:
        n = len(prices)
        if n < 3:
            return 0
        x_mean = (n - 1) / 2
        y_mean = sum(prices) / n
        numerator = sum((i - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        return slope / y_mean if y_mean != 0 else 0

    def _compute_mean_reversion_speed(self, prices: List[float]) -> float:
        if len(prices) < 5:
            return 0
        mean = sum(prices) / len(prices)
        deviations = [p - mean for p in prices]
        reversions = 0
        for i in range(1, len(deviations)):
            if (deviations[i-1] > 0 and deviations[i] < deviations[i-1]) or \
               (deviations[i-1] < 0 and deviations[i] > deviations[i-1]):
                reversions += 1
        return reversions / (len(deviations) - 1)

    def _compute_hurst_exponent(self, prices: List[float]) -> float:
        """Hurst exponent: H>0.5 = trending, H<0.5 = mean reverting, H=0.5 = random."""
        n = len(prices)
        if n < 20:
            return 0.5

        returns = [prices[i] - prices[i-1] for i in range(1, n)]
        mean_r = sum(returns) / len(returns)
        cumulative = []
        running = 0
        for r in returns:
            running += (r - mean_r)
            cumulative.append(running)

        range_rs = max(cumulative) - min(cumulative)
        std = math.sqrt(sum((r - mean_r) ** 2 for r in returns) / len(returns))

        if std == 0 or range_rs == 0:
            return 0.5

        rs = range_rs / std
        hurst = math.log(rs) / math.log(n) if n > 1 else 0.5
        return max(0, min(1, hurst))

    def _classify_regime(self, volatility: float, trend: float, mean_rev: float, hurst: float) -> tuple:
        scores = {
            "TRENDING_UP": 0,
            "TRENDING_DOWN": 0,
            "MEAN_REVERTING": 0,
            "HIGH_VOLATILITY": 0,
            "LOW_VOLATILITY": 0,
            "CHOPPY": 0,
        }

        if trend > 0.002:
            scores["TRENDING_UP"] += 3
        elif trend < -0.002:
            scores["TRENDING_DOWN"] += 3

        if hurst > 0.6:
            if trend > 0:
                scores["TRENDING_UP"] += 2
            else:
                scores["TRENDING_DOWN"] += 2
        elif hurst < 0.4:
            scores["MEAN_REVERTING"] += 3

        if mean_rev > 0.6:
            scores["MEAN_REVERTING"] += 2

        if volatility > 0.05:
            scores["HIGH_VOLATILITY"] += 2
        elif volatility < 0.01:
            scores["LOW_VOLATILITY"] += 2

        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        regime = top[0][0]
        max_score = top[0][1]
        total = sum(s for _, s in scores.items()) or 1
        confidence = max_score / total

        if max_score <= 1:
            regime = "CHOPPY"
            confidence = 0.3

        return regime, min(1.0, confidence)

    async def _get_prices(self, market_id: str, lookback_hours: int) -> List[float]:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
            result = await self.db.execute(
                select(PriceHistory.yes_price)
                .where(PriceHistory.market_id == market_id, PriceHistory.timestamp >= cutoff)
                .order_by(PriceHistory.timestamp)
            )
            return [float(row[0]) for row in result.all()]
        except Exception:
            return []

    def _regime_to_dict(self, regime: MarketRegime) -> Dict:
        return {
            "id": regime.id, "market_id": regime.market_id,
            "regime_type": regime.regime_type, "confidence": float(regime.confidence),
            "volatility": float(regime.volatility) if regime.volatility else None,
            "trend_strength": float(regime.trend_strength) if regime.trend_strength else None,
            "mean_reversion_speed": float(regime.mean_reversion_speed) if regime.mean_reversion_speed else None,
            "recommended_strategy": regime.recommended_strategy,
            "lookback_hours": regime.lookback_hours,
            "features": regime.features,
            "detected_at": regime.detected_at.isoformat() if regime.detected_at else None,
        }

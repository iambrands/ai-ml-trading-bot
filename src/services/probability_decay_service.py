"""Resolution Probability Decay Curves - Model how prices converge as resolution approaches.

Prediction markets exhibit characteristic probability decay patterns as events
approach resolution. This models that behavior using GBM and empirical curves
to predict future price paths with confidence bands.
"""

import math
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ProbabilityDecayCurve, Market, PriceHistory
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ProbabilityDecayService:
    """Models probability convergence as markets approach resolution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_decay_curve(self, market_id: str) -> Optional[Dict]:
        """Generate a probability decay/convergence curve for a market."""
        try:
            market_result = await self.db.execute(
                select(Market).where(Market.market_id == market_id)
            )
            market = market_result.scalar_one_or_none()

            prices = await self._get_price_series(market_id)
            if not prices:
                return None

            current_price = prices[-1]
            resolution_date = market.resolution_date if market else None
            hours_to_resolution = None
            if resolution_date:
                now = datetime.now(timezone.utc)
                res_aware = resolution_date.replace(tzinfo=timezone.utc) if resolution_date.tzinfo is None else resolution_date
                hours_to_resolution = max(0, (res_aware - now).total_seconds() / 3600)

            predicted_path = self._generate_gbm_path(current_price, hours_to_resolution, len(prices))
            upper_band, lower_band = self._generate_confidence_bands(predicted_path, prices)
            decay_rate = self._estimate_decay_rate(prices, hours_to_resolution)
            expected_final = self._estimate_final_price(current_price, decay_rate, hours_to_resolution)

            record = ProbabilityDecayCurve(
                market_id=market_id,
                market_question=market.question if market else None,
                resolution_date=resolution_date,
                hours_to_resolution=hours_to_resolution,
                current_price=current_price,
                predicted_path=predicted_path,
                confidence_band_upper=upper_band,
                confidence_band_lower=lower_band,
                decay_rate=decay_rate,
                expected_final_price=expected_final,
                model_type="gbm",
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            return self._curve_to_dict(record)
        except Exception as e:
            logger.error("Failed to generate decay curve", market=market_id, error=str(e))
            await self.db.rollback()
            return None

    async def get_decay_curve(self, market_id: str) -> Optional[Dict]:
        """Get the latest decay curve for a market."""
        try:
            result = await self.db.execute(
                select(ProbabilityDecayCurve)
                .where(ProbabilityDecayCurve.market_id == market_id)
                .order_by(desc(ProbabilityDecayCurve.calculated_at))
                .limit(1)
            )
            curve = result.scalar_one_or_none()
            return self._curve_to_dict(curve) if curve else None
        except Exception as e:
            logger.error("Failed to get decay curve", error=str(e))
            return None

    async def get_converging_markets(self, min_decay_rate: float = 0.01, limit: int = 20) -> List[Dict]:
        """Find markets that are rapidly converging toward resolution."""
        try:
            result = await self.db.execute(
                select(ProbabilityDecayCurve)
                .where(ProbabilityDecayCurve.decay_rate >= min_decay_rate)
                .order_by(desc(ProbabilityDecayCurve.decay_rate))
                .limit(limit)
            )
            curves = result.scalars().all()
            return [self._curve_to_dict(c) for c in curves]
        except Exception as e:
            logger.error("Failed to get converging markets", error=str(e))
            return []

    def _generate_gbm_path(self, current_price: float, hours_remaining: Optional[float], history_length: int) -> List[Dict]:
        """Generate predicted price path using Geometric Brownian Motion."""
        steps = min(50, int(hours_remaining or 168))
        if steps <= 0:
            return [{"hour": 0, "price": current_price}]

        mu = 0
        sigma = 0.02
        dt = 1.0
        path = [{"hour": 0, "price": round(current_price, 6)}]

        price = current_price
        for i in range(1, steps + 1):
            drift = (mu - 0.5 * sigma ** 2) * dt
            diffusion = sigma * math.sqrt(dt) * random.gauss(0, 1)
            price = price * math.exp(drift + diffusion)
            price = max(0.01, min(0.99, price))

            if hours_remaining:
                progress = i / steps
                price = price * (1 - progress) + (1.0 if current_price > 0.5 else 0.0) * progress * 0.3 + price * 0.7 * progress

            price = max(0.01, min(0.99, price))
            path.append({"hour": i, "price": round(price, 6)})

        return path

    def _generate_confidence_bands(self, path: List[Dict], historical: List[float]) -> tuple:
        """Generate upper and lower confidence bands."""
        vol = 0.03
        if len(historical) > 5:
            returns = [(historical[i] - historical[i-1]) / historical[i-1] for i in range(1, len(historical)) if historical[i-1] != 0]
            if returns:
                vol = math.sqrt(sum(r**2 for r in returns) / len(returns))

        upper = []
        lower = []
        for point in path:
            h = point["hour"]
            p = point["price"]
            band_width = vol * math.sqrt(max(h, 1)) * 0.5
            upper.append({"hour": h, "price": round(min(0.99, p + band_width), 6)})
            lower.append({"hour": h, "price": round(max(0.01, p - band_width), 6)})

        return upper, lower

    def _estimate_decay_rate(self, prices: List[float], hours_remaining: Optional[float]) -> float:
        """Estimate how fast the market is converging."""
        if len(prices) < 5:
            return 0

        recent = prices[-10:]
        dist_from_extreme = [min(p, 1 - p) for p in recent]

        if len(dist_from_extreme) < 2:
            return 0

        decay = (dist_from_extreme[0] - dist_from_extreme[-1]) / len(dist_from_extreme)
        return max(0, round(decay, 6))

    def _estimate_final_price(self, current: float, decay_rate: float, hours: Optional[float]) -> float:
        """Estimate the final price at resolution."""
        if current > 0.8:
            return min(0.99, current + decay_rate * (hours or 24))
        elif current < 0.2:
            return max(0.01, current - decay_rate * (hours or 24))
        return round(current, 6)

    async def _get_price_series(self, market_id: str) -> List[float]:
        try:
            result = await self.db.execute(
                select(PriceHistory.yes_price)
                .where(PriceHistory.market_id == market_id)
                .order_by(PriceHistory.timestamp)
                .limit(200)
            )
            return [float(row[0]) for row in result.all()]
        except Exception:
            return []

    def _curve_to_dict(self, curve: ProbabilityDecayCurve) -> Dict:
        return {
            "id": curve.id, "market_id": curve.market_id, "market_question": curve.market_question,
            "resolution_date": curve.resolution_date.isoformat() if curve.resolution_date else None,
            "hours_to_resolution": float(curve.hours_to_resolution) if curve.hours_to_resolution else None,
            "current_price": float(curve.current_price),
            "predicted_path": curve.predicted_path,
            "confidence_band_upper": curve.confidence_band_upper,
            "confidence_band_lower": curve.confidence_band_lower,
            "decay_rate": float(curve.decay_rate) if curve.decay_rate else None,
            "expected_final_price": float(curve.expected_final_price) if curve.expected_final_price else None,
            "model_type": curve.model_type,
            "calculated_at": curve.calculated_at.isoformat() if curve.calculated_at else None,
        }

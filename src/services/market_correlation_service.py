"""Market Correlation Analysis Service."""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import MarketCorrelation, PriceHistory, Market
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MarketCorrelationService:
    """Service for detecting and analyzing correlations between markets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_correlation(
        self,
        market_id_a: str,
        market_id_b: str,
        lookback_hours: int = 168,
        correlation_type: str = "price",
    ) -> Optional[Dict]:
        """Compute correlation between two markets."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

            prices_a = await self._get_price_series(market_id_a, cutoff)
            prices_b = await self._get_price_series(market_id_b, cutoff)

            aligned_a, aligned_b = self._align_series(prices_a, prices_b)

            if len(aligned_a) < 5:
                return None

            corr = self._pearson_correlation(aligned_a, aligned_b)
            p_value = self._approximate_p_value(corr, len(aligned_a))

            existing = await self.db.execute(
                select(MarketCorrelation).where(
                    MarketCorrelation.market_id_a == market_id_a,
                    MarketCorrelation.market_id_b == market_id_b,
                    MarketCorrelation.correlation_type == correlation_type,
                )
            )
            record = existing.scalar_one_or_none()

            if record:
                record.correlation = corr
                record.lookback_hours = lookback_hours
                record.sample_count = len(aligned_a)
                record.p_value = p_value
                record.calculated_at = datetime.now(timezone.utc)
            else:
                record = MarketCorrelation(
                    market_id_a=market_id_a,
                    market_id_b=market_id_b,
                    correlation=corr,
                    correlation_type=correlation_type,
                    lookback_hours=lookback_hours,
                    sample_count=len(aligned_a),
                    p_value=p_value,
                )
                self.db.add(record)

            await self.db.commit()

            return {
                "market_id_a": market_id_a,
                "market_id_b": market_id_b,
                "correlation": round(float(corr), 4),
                "correlation_type": correlation_type,
                "sample_count": len(aligned_a),
                "p_value": round(float(p_value), 6) if p_value else None,
                "strength": self._classify_correlation(float(corr)),
                "lookback_hours": lookback_hours,
            }
        except Exception as e:
            logger.error("Failed to compute correlation", error=str(e))
            await self.db.rollback()
            return None

    async def find_correlated_markets(
        self,
        market_id: str,
        min_correlation: float = 0.5,
        limit: int = 20,
    ) -> List[Dict]:
        """Find markets correlated with a given market."""
        try:
            result = await self.db.execute(
                select(MarketCorrelation)
                .where(
                    (
                        (MarketCorrelation.market_id_a == market_id)
                        | (MarketCorrelation.market_id_b == market_id)
                    ),
                    func.abs(MarketCorrelation.correlation) >= min_correlation,
                )
                .order_by(desc(func.abs(MarketCorrelation.correlation)))
                .limit(limit)
            )
            correlations = result.scalars().all()

            return [
                {
                    "market_id": c.market_id_b if c.market_id_a == market_id else c.market_id_a,
                    "correlation": round(float(c.correlation), 4),
                    "correlation_type": c.correlation_type,
                    "strength": self._classify_correlation(float(c.correlation)),
                    "sample_count": c.sample_count,
                }
                for c in correlations
            ]
        except Exception as e:
            logger.error("Failed to find correlated markets", error=str(e))
            return []

    async def get_correlation_matrix(self, market_ids: List[str]) -> Dict:
        """Get correlation matrix for a set of markets."""
        try:
            matrix = {}
            for i, id_a in enumerate(market_ids):
                matrix[id_a] = {}
                for j, id_b in enumerate(market_ids):
                    if i == j:
                        matrix[id_a][id_b] = 1.0
                        continue
                    result = await self.db.execute(
                        select(MarketCorrelation.correlation).where(
                            ((MarketCorrelation.market_id_a == id_a) & (MarketCorrelation.market_id_b == id_b))
                            | ((MarketCorrelation.market_id_a == id_b) & (MarketCorrelation.market_id_b == id_a))
                        )
                    )
                    corr = result.scalar()
                    matrix[id_a][id_b] = round(float(corr), 4) if corr else None

            return {"market_ids": market_ids, "matrix": matrix}
        except Exception as e:
            logger.error("Failed to get correlation matrix", error=str(e))
            return {"market_ids": market_ids, "matrix": {}}

    async def get_top_correlations(self, limit: int = 20) -> List[Dict]:
        """Get strongest correlations across all market pairs."""
        try:
            result = await self.db.execute(
                select(MarketCorrelation)
                .order_by(desc(func.abs(MarketCorrelation.correlation)))
                .limit(limit)
            )
            correlations = result.scalars().all()

            return [
                {
                    "market_id_a": c.market_id_a,
                    "market_id_b": c.market_id_b,
                    "correlation": round(float(c.correlation), 4),
                    "correlation_type": c.correlation_type,
                    "strength": self._classify_correlation(float(c.correlation)),
                    "sample_count": c.sample_count,
                    "category_a": c.category_a,
                    "category_b": c.category_b,
                }
                for c in correlations
            ]
        except Exception as e:
            logger.error("Failed to get top correlations", error=str(e))
            return []

    async def _get_price_series(self, market_id: str, cutoff: datetime) -> List[Tuple[datetime, float]]:
        result = await self.db.execute(
            select(PriceHistory.timestamp, PriceHistory.yes_price)
            .where(PriceHistory.market_id == market_id, PriceHistory.timestamp >= cutoff)
            .order_by(PriceHistory.timestamp)
        )
        return [(row[0], float(row[1])) for row in result.all()]

    def _align_series(
        self, series_a: List[Tuple], series_b: List[Tuple]
    ) -> Tuple[List[float], List[float]]:
        """Align two time series by matching timestamps (within 5 min tolerance)."""
        dict_b = {ts: val for ts, val in series_b}
        aligned_a, aligned_b = [], []

        for ts_a, val_a in series_a:
            best_match = None
            best_diff = timedelta(minutes=5)
            for ts_b, val_b in series_b:
                diff = abs(ts_a - ts_b) if ts_a > ts_b else abs(ts_b - ts_a)
                if diff < best_diff:
                    best_diff = diff
                    best_match = val_b
            if best_match is not None:
                aligned_a.append(val_a)
                aligned_b.append(best_match)

        return aligned_a, aligned_b

    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        n = len(x)
        if n < 2:
            return 0.0
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
        std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) / n)
        std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y) / n)
        if std_x == 0 or std_y == 0:
            return 0.0
        return cov / (std_x * std_y)

    def _approximate_p_value(self, r: float, n: int) -> Optional[float]:
        if n < 4 or abs(r) >= 1:
            return None
        t = r * math.sqrt((n - 2) / (1 - r ** 2))
        df = n - 2
        p = 2 * (1 - self._students_t_cdf(abs(t), df))
        return max(0, min(1, p))

    def _students_t_cdf(self, t: float, df: int) -> float:
        """Rough approximation of Student's t CDF."""
        x = df / (df + t ** 2)
        return 1 - 0.5 * x ** (df / 2)

    def _classify_correlation(self, corr: float) -> str:
        abs_corr = abs(corr)
        if abs_corr >= 0.8:
            return "VERY_STRONG"
        elif abs_corr >= 0.6:
            return "STRONG"
        elif abs_corr >= 0.4:
            return "MODERATE"
        elif abs_corr >= 0.2:
            return "WEAK"
        return "NEGLIGIBLE"

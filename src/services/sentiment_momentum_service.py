"""Social Sentiment Momentum - Track real-time sentiment shifts versus price.

Detects divergences between social sentiment and market price, which are
leading indicators of price movements. No competitor combines sentiment
momentum with divergence detection for prediction markets.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import SentimentMomentum, PriceHistory, NewsArticle
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SentimentMomentumService:
    """Tracks sentiment momentum and price-sentiment divergences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def measure_momentum(self, market_id: str) -> Optional[Dict]:
        """Measure current sentiment momentum for a market."""
        try:
            current_sentiment = await self._compute_current_sentiment(market_id)
            sentiment_1h_ago = await self._get_historical_sentiment(market_id, hours=1)
            sentiment_24h_ago = await self._get_historical_sentiment(market_id, hours=24)
            current_price = await self._get_current_price(market_id)
            price_1h_ago = await self._get_historical_price(market_id, hours=1)
            price_24h_ago = await self._get_historical_price(market_id, hours=24)

            sent_change_1h = current_sentiment - sentiment_1h_ago if sentiment_1h_ago else None
            sent_change_24h = current_sentiment - sentiment_24h_ago if sentiment_24h_ago else None
            price_change_1h = (current_price - price_1h_ago) if price_1h_ago and current_price else None
            price_change_24h = (current_price - price_24h_ago) if price_24h_ago and current_price else None

            divergence = self._detect_divergence(sent_change_1h, price_change_1h, sent_change_24h, price_change_24h)

            social_counts = await self._get_social_counts(market_id)

            record = SentimentMomentum(
                market_id=market_id,
                sentiment_score=current_sentiment,
                sentiment_change_1h=sent_change_1h,
                sentiment_change_24h=sent_change_24h,
                price_at_measurement=current_price,
                price_change_1h=price_change_1h,
                price_change_24h=price_change_24h,
                sentiment_price_divergence=self._compute_divergence_score(sent_change_24h, price_change_24h),
                twitter_mentions=social_counts.get("twitter", 0),
                reddit_mentions=social_counts.get("reddit", 0),
                news_mentions=social_counts.get("news", 0),
                social_volume_change=social_counts.get("volume_change"),
                divergence_signal=divergence,
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            return self._momentum_to_dict(record)
        except Exception as e:
            logger.error("Failed to measure momentum", market=market_id, error=str(e))
            await self.db.rollback()
            return None

    async def get_momentum(self, market_id: str) -> Optional[Dict]:
        """Get latest sentiment momentum for a market."""
        try:
            result = await self.db.execute(
                select(SentimentMomentum)
                .where(SentimentMomentum.market_id == market_id)
                .order_by(desc(SentimentMomentum.measured_at))
                .limit(1)
            )
            m = result.scalar_one_or_none()
            return self._momentum_to_dict(m) if m else None
        except Exception as e:
            logger.error("Failed to get momentum", error=str(e))
            return None

    async def get_divergences(self, signal_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get markets with sentiment-price divergences (leading indicators)."""
        try:
            query = select(SentimentMomentum).where(
                SentimentMomentum.divergence_signal.in_(["BULLISH_DIVERGENCE", "BEARISH_DIVERGENCE"])
            )
            if signal_type:
                query = select(SentimentMomentum).where(SentimentMomentum.divergence_signal == signal_type.upper())
            query = query.order_by(desc(SentimentMomentum.measured_at)).limit(limit)

            result = await self.db.execute(query)
            records = result.scalars().all()
            return [self._momentum_to_dict(r) for r in records]
        except Exception as e:
            logger.error("Failed to get divergences", error=str(e))
            return []

    async def get_momentum_history(self, market_id: str, hours: int = 48) -> List[Dict]:
        """Get sentiment momentum history for a market."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(SentimentMomentum)
                .where(SentimentMomentum.market_id == market_id, SentimentMomentum.measured_at >= cutoff)
                .order_by(SentimentMomentum.measured_at)
            )
            records = result.scalars().all()
            return [self._momentum_to_dict(r) for r in records]
        except Exception as e:
            logger.error("Failed to get momentum history", error=str(e))
            return []

    async def get_market_mood(self) -> Dict:
        """Get overall market mood from sentiment across all markets."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
            result = await self.db.execute(
                select(
                    func.avg(SentimentMomentum.sentiment_score),
                    func.count(SentimentMomentum.id),
                    func.count(SentimentMomentum.id).filter(SentimentMomentum.divergence_signal == "BULLISH_DIVERGENCE"),
                    func.count(SentimentMomentum.id).filter(SentimentMomentum.divergence_signal == "BEARISH_DIVERGENCE"),
                )
                .where(SentimentMomentum.measured_at >= cutoff)
            )
            row = result.one()
            avg_sentiment = float(row[0]) if row[0] else 0.5
            total = row[1] or 0
            bullish_div = row[2] or 0
            bearish_div = row[3] or 0

            mood = "BULLISH" if avg_sentiment > 0.6 else "BEARISH" if avg_sentiment < 0.4 else "NEUTRAL"
            if bullish_div > bearish_div * 2:
                mood = "CONTRARIAN_BULLISH"
            elif bearish_div > bullish_div * 2:
                mood = "CONTRARIAN_BEARISH"

            return {
                "overall_mood": mood,
                "avg_sentiment": round(avg_sentiment, 4),
                "markets_measured": total,
                "bullish_divergences": bullish_div,
                "bearish_divergences": bearish_div,
            }
        except Exception as e:
            logger.error("Failed to get market mood", error=str(e))
            return {"overall_mood": "UNKNOWN"}

    def _detect_divergence(self, sent_1h: Optional[float], price_1h: Optional[float], sent_24h: Optional[float], price_24h: Optional[float]) -> str:
        if sent_24h is not None and price_24h is not None:
            if sent_24h > 0.05 and price_24h < -0.02:
                return "BULLISH_DIVERGENCE"
            if sent_24h < -0.05 and price_24h > 0.02:
                return "BEARISH_DIVERGENCE"
            if sent_24h > 0.03 and price_24h > 0.02:
                return "CONFIRMING"
            if sent_24h < -0.03 and price_24h < -0.02:
                return "CONFIRMING"

        if sent_1h is not None and price_1h is not None:
            if sent_1h > 0.05 and price_1h < -0.01:
                return "BULLISH_DIVERGENCE"
            if sent_1h < -0.05 and price_1h > 0.01:
                return "BEARISH_DIVERGENCE"

        return "NEUTRAL"

    def _compute_divergence_score(self, sent_change: Optional[float], price_change: Optional[float]) -> Optional[float]:
        if sent_change is None or price_change is None:
            return None
        if sent_change == 0 and price_change == 0:
            return 0
        if (sent_change > 0 and price_change < 0) or (sent_change < 0 and price_change > 0):
            return round(abs(sent_change - price_change), 6)
        return round(-abs(sent_change + price_change) / 2, 6)

    async def _compute_current_sentiment(self, market_id: str) -> float:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
            from ..database.models import NewsMarketLink
            result = await self.db.execute(
                select(func.avg(NewsArticle.sentiment_score))
                .join(NewsMarketLink)
                .where(NewsMarketLink.market_id == market_id, NewsArticle.published_at >= cutoff)
            )
            score = result.scalar()
            return float(score) if score else 0.5
        except Exception:
            return 0.5

    async def _get_historical_sentiment(self, market_id: str, hours: int) -> Optional[float]:
        try:
            target = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(SentimentMomentum.sentiment_score)
                .where(SentimentMomentum.market_id == market_id, SentimentMomentum.measured_at <= target)
                .order_by(desc(SentimentMomentum.measured_at))
                .limit(1)
            )
            score = result.scalar()
            return float(score) if score else None
        except Exception:
            return None

    async def _get_current_price(self, market_id: str) -> Optional[float]:
        try:
            result = await self.db.execute(
                select(PriceHistory.yes_price)
                .where(PriceHistory.market_id == market_id)
                .order_by(desc(PriceHistory.timestamp))
                .limit(1)
            )
            price = result.scalar()
            return float(price) if price else None
        except Exception:
            return None

    async def _get_historical_price(self, market_id: str, hours: int) -> Optional[float]:
        try:
            target = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(PriceHistory.yes_price)
                .where(PriceHistory.market_id == market_id, PriceHistory.timestamp <= target)
                .order_by(desc(PriceHistory.timestamp))
                .limit(1)
            )
            price = result.scalar()
            return float(price) if price else None
        except Exception:
            return None

    async def _get_social_counts(self, market_id: str) -> Dict:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            from ..database.models import NewsMarketLink
            result = await self.db.execute(
                select(func.count(NewsArticle.id))
                .join(NewsMarketLink)
                .where(NewsMarketLink.market_id == market_id, NewsArticle.published_at >= cutoff)
            )
            news_count = result.scalar() or 0
            return {"twitter": 0, "reddit": 0, "news": news_count, "volume_change": None}
        except Exception:
            return {"twitter": 0, "reddit": 0, "news": 0}

    def _momentum_to_dict(self, m: SentimentMomentum) -> Dict:
        return {
            "id": m.id, "market_id": m.market_id,
            "sentiment_score": float(m.sentiment_score),
            "sentiment_change_1h": float(m.sentiment_change_1h) if m.sentiment_change_1h else None,
            "sentiment_change_24h": float(m.sentiment_change_24h) if m.sentiment_change_24h else None,
            "price_at_measurement": float(m.price_at_measurement) if m.price_at_measurement else None,
            "price_change_1h": float(m.price_change_1h) if m.price_change_1h else None,
            "price_change_24h": float(m.price_change_24h) if m.price_change_24h else None,
            "sentiment_price_divergence": float(m.sentiment_price_divergence) if m.sentiment_price_divergence else None,
            "social_mentions": {"twitter": m.twitter_mentions, "reddit": m.reddit_mentions, "news": m.news_mentions},
            "divergence_signal": m.divergence_signal,
            "measured_at": m.measured_at.isoformat() if m.measured_at else None,
        }

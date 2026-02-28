"""Multi-Model AI Consensus - Aggregate predictions from multiple AI/ML models.

Unlike platforms using a single model, this aggregates predictions from the
internal ML ensemble, technical analysis, sentiment analysis, smart money flow,
and (optionally) external LLMs to produce a consensus view with a disagreement
score that measures model agreement.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import AIConsensus, Prediction, Market
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AIConsensusService:
    """Aggregates predictions from multiple AI models for consensus view."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_consensus(self, market_id: str, market_price: Optional[float] = None) -> Optional[Dict]:
        """Generate multi-model consensus for a market."""
        try:
            model_predictions = {}

            ml_pred = await self._get_ml_prediction(market_id)
            if ml_pred:
                model_predictions["ml_ensemble"] = ml_pred

            ta_pred = await self._get_technical_prediction(market_id)
            if ta_pred:
                model_predictions["technical_analysis"] = ta_pred

            sentiment_pred = await self._get_sentiment_prediction(market_id)
            if sentiment_pred:
                model_predictions["sentiment_analysis"] = sentiment_pred

            flow_pred = await self._get_smart_money_prediction(market_id)
            if flow_pred:
                model_predictions["smart_money_flow"] = flow_pred

            if not model_predictions:
                return None

            probs = [p["probability"] for p in model_predictions.values()]
            confs = [p.get("confidence", 0.5) for p in model_predictions.values()]

            weights = [confs[i] for i in range(len(probs))]
            total_weight = sum(weights) or 1
            consensus_prob = sum(p * w for p, w in zip(probs, weights)) / total_weight
            consensus_conf = sum(confs) / len(confs)

            mean = sum(probs) / len(probs)
            variance = sum((p - mean) ** 2 for p in probs) / len(probs)
            disagreement = min(1.0, variance * 10)

            bullish = sum(1 for p in probs if p > 0.55)
            bearish = sum(1 for p in probs if p < 0.45)

            if bullish > bearish and consensus_prob > 0.55:
                strongest = "STRONG_YES"
            elif bearish > bullish and consensus_prob < 0.45:
                strongest = "STRONG_NO"
            elif bullish > bearish:
                strongest = "LEAN_YES"
            elif bearish > bullish:
                strongest = "LEAN_NO"
            else:
                strongest = "NEUTRAL"

            edge = consensus_prob - market_price if market_price else None

            market_result = await self.db.execute(
                select(Market.question).where(Market.market_id == market_id)
            )
            question = market_result.scalar()

            record = AIConsensus(
                market_id=market_id,
                market_question=question,
                model_predictions=model_predictions,
                consensus_probability=round(consensus_prob, 4),
                consensus_confidence=round(consensus_conf, 4),
                disagreement_score=round(disagreement, 4),
                strongest_signal=strongest,
                num_models=len(model_predictions),
                num_bullish=bullish,
                num_bearish=bearish,
                market_price=market_price,
                edge_vs_market=round(edge, 6) if edge else None,
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
            return self._consensus_to_dict(record)
        except Exception as e:
            logger.error("Failed to generate consensus", market=market_id, error=str(e))
            await self.db.rollback()
            return None

    async def get_consensus(self, market_id: str) -> Optional[Dict]:
        """Get latest consensus for a market."""
        try:
            result = await self.db.execute(
                select(AIConsensus)
                .where(AIConsensus.market_id == market_id)
                .order_by(desc(AIConsensus.calculated_at))
                .limit(1)
            )
            consensus = result.scalar_one_or_none()
            return self._consensus_to_dict(consensus) if consensus else None
        except Exception as e:
            logger.error("Failed to get consensus", error=str(e))
            return None

    async def get_high_conviction(self, min_confidence: float = 0.7, max_disagreement: float = 0.3, limit: int = 20) -> List[Dict]:
        """Get markets where models have high agreement."""
        try:
            result = await self.db.execute(
                select(AIConsensus)
                .where(
                    AIConsensus.consensus_confidence >= min_confidence,
                    AIConsensus.disagreement_score <= max_disagreement,
                )
                .order_by(desc(AIConsensus.consensus_confidence))
                .limit(limit)
            )
            records = result.scalars().all()
            return [self._consensus_to_dict(r) for r in records]
        except Exception as e:
            logger.error("Failed to get high conviction", error=str(e))
            return []

    async def get_most_disagreed(self, min_disagreement: float = 0.5, limit: int = 20) -> List[Dict]:
        """Get markets where models disagree most (contrarian opportunities)."""
        try:
            result = await self.db.execute(
                select(AIConsensus)
                .where(AIConsensus.disagreement_score >= min_disagreement)
                .order_by(desc(AIConsensus.disagreement_score))
                .limit(limit)
            )
            records = result.scalars().all()
            return [self._consensus_to_dict(r) for r in records]
        except Exception as e:
            logger.error("Failed to get disagreed markets", error=str(e))
            return []

    async def _get_ml_prediction(self, market_id: str) -> Optional[Dict]:
        try:
            result = await self.db.execute(
                select(Prediction)
                .where(Prediction.market_id == market_id)
                .order_by(desc(Prediction.prediction_time))
                .limit(1)
            )
            pred = result.scalar_one_or_none()
            if pred:
                return {"probability": float(pred.model_probability), "confidence": float(pred.confidence), "model": "ml_ensemble", "edge": float(pred.edge)}
        except Exception:
            pass
        return None

    async def _get_technical_prediction(self, market_id: str) -> Optional[Dict]:
        try:
            from .price_history_service import PriceHistoryService
            ph = PriceHistoryService(self.db)
            indicators = await ph.compute_indicators(market_id, hours=48)
            signal = indicators.get("signal", {})
            direction = signal.get("direction", "NEUTRAL")
            strength = signal.get("strength", 0.5)

            if direction == "BULLISH":
                prob = 0.5 + strength * 0.3
            elif direction == "BEARISH":
                prob = 0.5 - strength * 0.3
            else:
                prob = 0.5

            return {"probability": round(prob, 4), "confidence": round(strength, 4), "model": "technical_analysis", "direction": direction}
        except Exception:
            return None

    async def _get_sentiment_prediction(self, market_id: str) -> Optional[Dict]:
        try:
            from ..database.models import SentimentMomentum
            result = await self.db.execute(
                select(SentimentMomentum)
                .where(SentimentMomentum.market_id == market_id)
                .order_by(desc(SentimentMomentum.measured_at))
                .limit(1)
            )
            sm = result.scalar_one_or_none()
            if sm:
                return {"probability": float(sm.sentiment_score), "confidence": 0.5, "model": "sentiment", "divergence": sm.divergence_signal}
        except Exception:
            pass
        return None

    async def _get_smart_money_prediction(self, market_id: str) -> Optional[Dict]:
        try:
            from .smart_money_service import SmartMoneyService
            sms = SmartMoneyService(self.db)
            flow = await sms.get_smart_money_flow(market_id=market_id, hours=24)
            direction = flow.get("flow_direction", "NEUTRAL")
            buy_pct = flow.get("buy_pct", 50) / 100

            return {"probability": round(buy_pct, 4), "confidence": 0.4, "model": "smart_money_flow", "direction": direction}
        except Exception:
            return None

    def _consensus_to_dict(self, c: AIConsensus) -> Dict:
        return {
            "id": c.id, "market_id": c.market_id, "market_question": c.market_question,
            "model_predictions": c.model_predictions,
            "consensus_probability": float(c.consensus_probability),
            "consensus_confidence": float(c.consensus_confidence),
            "disagreement_score": float(c.disagreement_score),
            "strongest_signal": c.strongest_signal,
            "num_models": c.num_models, "num_bullish": c.num_bullish, "num_bearish": c.num_bearish,
            "market_price": float(c.market_price) if c.market_price else None,
            "edge_vs_market": float(c.edge_vs_market) if c.edge_vs_market else None,
            "calculated_at": c.calculated_at.isoformat() if c.calculated_at else None,
        }

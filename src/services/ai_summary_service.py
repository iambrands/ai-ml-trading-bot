"""AI Market Summaries Service - LLM-powered market analysis."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import AIMarketSummary, Market, Prediction, NewsArticle, NewsMarketLink
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AIMarketSummaryService:
    """Generates AI-powered market analysis summaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_summary(self, market_id: str, market_data: Optional[Dict] = None) -> Optional[Dict]:
        """Generate an AI analysis summary for a market."""
        try:
            market_info = await self._get_market_info(market_id)
            predictions = await self._get_recent_predictions(market_id)
            news = await self._get_related_news(market_id)

            if not market_info and not market_data:
                return None

            question = (market_data or {}).get("question", market_info.get("question", "Unknown"))
            category = (market_data or {}).get("category", market_info.get("category"))
            current_price = (market_data or {}).get("yes_price", market_info.get("yes_price"))

            key_factors = self._analyze_key_factors(predictions, news, current_price)
            sentiment = self._aggregate_sentiment(news)
            prob_assessment = self._assess_probability(predictions, current_price)
            risk = self._assess_risk(predictions, current_price, news)
            recommendation = self._generate_recommendation(prob_assessment, risk, current_price, predictions)
            summary_text = self._compose_summary(question, current_price, key_factors, sentiment, risk, recommendation)

            summary = AIMarketSummary(
                market_id=market_id,
                market_question=question,
                summary=summary_text,
                key_factors=key_factors,
                sentiment_score=sentiment.get("score"),
                probability_assessment=prob_assessment,
                confidence=predictions[0]["confidence"] if predictions else None,
                risk_level=risk["level"],
                recommendation=recommendation,
                news_sources=[n.get("title") for n in news[:5]] if news else None,
                model_used="internal_ensemble",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            )
            self.db.add(summary)
            await self.db.commit()
            await self.db.refresh(summary)

            return self._summary_to_dict(summary)
        except Exception as e:
            logger.error("Failed to generate summary", market=market_id, error=str(e))
            await self.db.rollback()
            return None

    async def get_summary(self, market_id: str) -> Optional[Dict]:
        """Get the latest summary for a market."""
        try:
            result = await self.db.execute(
                select(AIMarketSummary)
                .where(AIMarketSummary.market_id == market_id)
                .order_by(desc(AIMarketSummary.generated_at))
                .limit(1)
            )
            summary = result.scalar_one_or_none()

            if summary and summary.expires_at and summary.expires_at > datetime.now(timezone.utc):
                return self._summary_to_dict(summary)

            return self._summary_to_dict(summary) if summary else None
        except Exception as e:
            logger.error("Failed to get summary", market=market_id, error=str(e))
            return None

    async def get_latest_summaries(self, limit: int = 20) -> List[Dict]:
        """Get latest AI summaries across all markets."""
        try:
            result = await self.db.execute(
                select(AIMarketSummary)
                .order_by(desc(AIMarketSummary.generated_at))
                .limit(limit)
            )
            summaries = result.scalars().all()
            return [self._summary_to_dict(s) for s in summaries]
        except Exception as e:
            logger.error("Failed to get latest summaries", error=str(e))
            return []

    async def get_summaries_by_recommendation(self, recommendation: str, limit: int = 20) -> List[Dict]:
        """Get summaries filtered by recommendation type."""
        try:
            result = await self.db.execute(
                select(AIMarketSummary)
                .where(AIMarketSummary.recommendation == recommendation.upper())
                .order_by(desc(AIMarketSummary.generated_at))
                .limit(limit)
            )
            summaries = result.scalars().all()
            return [self._summary_to_dict(s) for s in summaries]
        except Exception as e:
            logger.error("Failed to get summaries by recommendation", error=str(e))
            return []

    async def _get_market_info(self, market_id: str) -> Dict:
        try:
            result = await self.db.execute(
                select(Market).where(Market.market_id == market_id)
            )
            market = result.scalar_one_or_none()
            if market:
                return {
                    "question": market.question,
                    "category": market.category,
                    "resolution_date": market.resolution_date,
                    "outcome": market.outcome,
                }
        except Exception:
            pass
        return {}

    async def _get_recent_predictions(self, market_id: str) -> List[Dict]:
        try:
            result = await self.db.execute(
                select(Prediction)
                .where(Prediction.market_id == market_id)
                .order_by(desc(Prediction.prediction_time))
                .limit(10)
            )
            predictions = result.scalars().all()
            return [
                {
                    "model_probability": float(p.model_probability),
                    "market_price": float(p.market_price),
                    "edge": float(p.edge),
                    "confidence": float(p.confidence),
                    "prediction_time": p.prediction_time.isoformat(),
                }
                for p in predictions
            ]
        except Exception:
            return []

    async def _get_related_news(self, market_id: str) -> List[Dict]:
        try:
            result = await self.db.execute(
                select(NewsArticle)
                .join(NewsMarketLink)
                .where(NewsMarketLink.market_id == market_id)
                .order_by(desc(NewsArticle.published_at))
                .limit(10)
            )
            articles = result.scalars().all()
            return [
                {
                    "title": a.title,
                    "source": a.source,
                    "sentiment_score": float(a.sentiment_score) if a.sentiment_score else None,
                    "sentiment_label": a.sentiment_label,
                    "published_at": a.published_at.isoformat() if a.published_at else None,
                }
                for a in articles
            ]
        except Exception:
            return []

    def _analyze_key_factors(self, predictions: List[Dict], news: List[Dict], current_price: Optional[float]) -> List[str]:
        factors = []

        if predictions:
            latest = predictions[0]
            edge = latest["edge"]
            if abs(edge) > 0.10:
                factors.append(f"Model detects significant {'positive' if edge > 0 else 'negative'} edge of {edge*100:.1f}%")
            if latest["confidence"] > 0.8:
                factors.append(f"High model confidence at {latest['confidence']*100:.1f}%")

            if len(predictions) >= 3:
                edges = [p["edge"] for p in predictions[:5]]
                if all(e > 0 for e in edges):
                    factors.append("Consistently positive edge across recent predictions")
                elif all(e < 0 for e in edges):
                    factors.append("Consistently negative edge - market may be overpriced")

        if news:
            positive = sum(1 for n in news if n.get("sentiment_label") == "POSITIVE")
            negative = sum(1 for n in news if n.get("sentiment_label") == "NEGATIVE")
            if positive > negative * 2:
                factors.append(f"News sentiment strongly positive ({positive} positive vs {negative} negative articles)")
            elif negative > positive * 2:
                factors.append(f"News sentiment strongly negative ({negative} negative vs {positive} positive articles)")
            factors.append(f"{len(news)} relevant news articles tracked")

        if current_price:
            if current_price > 0.85:
                factors.append("Market strongly favors YES outcome")
            elif current_price < 0.15:
                factors.append("Market strongly favors NO outcome")
            elif 0.45 < current_price < 0.55:
                factors.append("Market is near 50/50 - high uncertainty")

        if not factors:
            factors.append("Limited data available for comprehensive analysis")

        return factors

    def _aggregate_sentiment(self, news: List[Dict]) -> Dict:
        if not news:
            return {"score": 0.5, "label": "NEUTRAL", "article_count": 0}

        scores = [n["sentiment_score"] for n in news if n.get("sentiment_score") is not None]
        if not scores:
            return {"score": 0.5, "label": "NEUTRAL", "article_count": len(news)}

        avg = sum(scores) / len(scores)
        label = "POSITIVE" if avg > 0.6 else "NEGATIVE" if avg < 0.4 else "NEUTRAL"
        return {"score": round(avg, 4), "label": label, "article_count": len(news)}

    def _assess_probability(self, predictions: List[Dict], current_price: Optional[float]) -> Optional[float]:
        if predictions:
            return predictions[0]["model_probability"]
        return current_price

    def _assess_risk(self, predictions: List[Dict], current_price: Optional[float], news: List[Dict]) -> Dict:
        risk_score = 0

        if predictions and len(predictions) >= 2:
            edges = [abs(p["edge"]) for p in predictions[:5]]
            variance = sum((e - sum(edges)/len(edges))**2 for e in edges) / len(edges)
            if variance > 0.01:
                risk_score += 3

        if current_price and (current_price > 0.9 or current_price < 0.1):
            risk_score += 2

        if len(news) < 2:
            risk_score += 1

        level = "HIGH" if risk_score >= 4 else "MEDIUM" if risk_score >= 2 else "LOW"
        return {"level": level, "score": risk_score}

    def _generate_recommendation(self, prob: Optional[float], risk: Dict, price: Optional[float], predictions: List[Dict]) -> str:
        if not predictions or not price:
            return "HOLD"

        edge = predictions[0]["edge"]
        confidence = predictions[0]["confidence"]

        if risk["level"] == "HIGH" and confidence < 0.7:
            return "AVOID"

        if abs(edge) > 0.10 and confidence > 0.65:
            return "BUY_YES" if edge > 0 else "BUY_NO"
        elif abs(edge) > 0.05 and confidence > 0.60:
            return "BUY_YES" if edge > 0 else "BUY_NO"

        return "HOLD"

    def _compose_summary(self, question: str, price: Optional[float], factors: List[str], sentiment: Dict, risk: Dict, recommendation: str) -> str:
        lines = [f"**Market Analysis: {question}**\n"]

        if price:
            lines.append(f"Current implied probability: {price*100:.1f}%\n")

        lines.append("**Key Factors:**")
        for f in factors:
            lines.append(f"- {f}")

        lines.append(f"\n**Sentiment:** {sentiment['label']} (score: {sentiment['score']:.2f}, {sentiment['article_count']} articles)")
        lines.append(f"**Risk Level:** {risk['level']}")

        rec_labels = {
            "BUY_YES": "Buy YES - Model sees positive edge",
            "BUY_NO": "Buy NO - Model sees negative edge",
            "HOLD": "Hold - Insufficient edge for entry",
            "AVOID": "Avoid - High risk with low confidence",
        }
        lines.append(f"**Recommendation:** {rec_labels.get(recommendation, recommendation)}")

        return "\n".join(lines)

    def _summary_to_dict(self, summary: AIMarketSummary) -> Dict:
        return {
            "id": summary.id,
            "market_id": summary.market_id,
            "market_question": summary.market_question,
            "summary": summary.summary,
            "key_factors": summary.key_factors,
            "sentiment_score": float(summary.sentiment_score) if summary.sentiment_score else None,
            "probability_assessment": float(summary.probability_assessment) if summary.probability_assessment else None,
            "confidence": float(summary.confidence) if summary.confidence else None,
            "risk_level": summary.risk_level,
            "recommendation": summary.recommendation,
            "news_sources": summary.news_sources,
            "model_used": summary.model_used,
            "generated_at": summary.generated_at.isoformat() if summary.generated_at else None,
            "expires_at": summary.expires_at.isoformat() if summary.expires_at else None,
        }

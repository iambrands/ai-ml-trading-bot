"""Portfolio Hedging Engine - Auto-suggest hedges across correlated markets.

Analyzes open positions and suggests hedging trades using negatively correlated
markets. No other Polymarket platform offers automated portfolio hedging.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import HedgeSuggestion, Trade, MarketCorrelation, Market
from ..utils.logging import get_logger

logger = get_logger(__name__)


class HedgingService:
    """Suggests and tracks portfolio hedges across correlated markets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def suggest_hedges(self, min_effectiveness: float = 0.3) -> List[Dict]:
        """Analyze open positions and suggest hedging trades."""
        suggestions = []
        try:
            result = await self.db.execute(
                select(Trade).where(Trade.status == "OPEN").order_by(desc(Trade.entry_time))
            )
            open_trades = result.scalars().all()

            if not open_trades:
                return []

            for trade in open_trades:
                hedges = await self._find_hedges_for_position(trade, min_effectiveness)
                suggestions.extend(hedges)

            portfolio_hedges = await self._suggest_portfolio_level_hedges(open_trades)
            suggestions.extend(portfolio_hedges)

            for s in suggestions:
                await self._save_suggestion(s)

            if suggestions:
                await self.db.commit()

            logger.info("Generated hedge suggestions", count=len(suggestions))
            return suggestions
        except Exception as e:
            logger.error("Failed to suggest hedges", error=str(e))
            await self.db.rollback()
            return []

    async def get_suggestions(self, market_id: Optional[str] = None, executed: Optional[bool] = None, limit: int = 20) -> List[Dict]:
        """Get hedge suggestions."""
        try:
            query = select(HedgeSuggestion)
            if market_id:
                query = query.where(HedgeSuggestion.source_market_id == market_id)
            if executed is not None:
                query = query.where(HedgeSuggestion.is_executed == executed)
            query = query.order_by(desc(HedgeSuggestion.created_at)).limit(limit)

            result = await self.db.execute(query)
            suggestions = result.scalars().all()
            return [self._suggestion_to_dict(s) for s in suggestions]
        except Exception as e:
            logger.error("Failed to get hedge suggestions", error=str(e))
            return []

    async def analyze_portfolio_risk(self) -> Dict:
        """Analyze current portfolio risk exposure."""
        try:
            result = await self.db.execute(
                select(Trade).where(Trade.status == "OPEN")
            )
            open_trades = result.scalars().all()

            if not open_trades:
                return {"total_positions": 0, "risk_level": "NONE", "message": "No open positions"}

            total_exposure = sum(float(t.size) for t in open_trades)
            yes_exposure = sum(float(t.size) for t in open_trades if t.side == "YES")
            no_exposure = sum(float(t.size) for t in open_trades if t.side == "NO")

            markets = set(t.market_id for t in open_trades)
            concentration = max(float(t.size) for t in open_trades) / total_exposure if total_exposure > 0 else 0
            directional_bias = abs(yes_exposure - no_exposure) / total_exposure if total_exposure > 0 else 0

            risk_score = 0
            if concentration > 0.5:
                risk_score += 30
            if directional_bias > 0.7:
                risk_score += 30
            if len(markets) < 3:
                risk_score += 20
            if total_exposure > 5000:
                risk_score += 20

            risk_level = "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 30 else "LOW"

            return {
                "total_positions": len(open_trades),
                "total_exposure": round(total_exposure, 2),
                "yes_exposure": round(yes_exposure, 2),
                "no_exposure": round(no_exposure, 2),
                "unique_markets": len(markets),
                "concentration_ratio": round(concentration, 4),
                "directional_bias": round(directional_bias, 4),
                "directional_direction": "YES" if yes_exposure > no_exposure else "NO",
                "risk_score": risk_score,
                "risk_level": risk_level,
                "recommendations": self._generate_risk_recommendations(risk_score, concentration, directional_bias, len(markets)),
            }
        except Exception as e:
            logger.error("Failed to analyze portfolio risk", error=str(e))
            return {"risk_level": "UNKNOWN", "error": str(e)}

    async def _find_hedges_for_position(self, trade: Trade, min_effectiveness: float) -> List[Dict]:
        """Find hedging opportunities for a single position."""
        hedges = []
        try:
            result = await self.db.execute(
                select(MarketCorrelation)
                .where(
                    ((MarketCorrelation.market_id_a == trade.market_id) | (MarketCorrelation.market_id_b == trade.market_id)),
                    MarketCorrelation.correlation < -0.3,
                )
                .order_by(MarketCorrelation.correlation)
                .limit(5)
            )
            correlations = result.scalars().all()

            for corr in correlations:
                hedge_market = corr.market_id_b if corr.market_id_a == trade.market_id else corr.market_id_a
                correlation = float(corr.correlation)
                effectiveness = abs(correlation)

                if effectiveness < min_effectiveness:
                    continue

                hedge_side = "NO" if trade.side == "YES" else "YES"
                hedge_size = float(trade.size) * effectiveness
                risk_reduction = effectiveness * 100

                hedges.append({
                    "source_market_id": trade.market_id,
                    "source_side": trade.side,
                    "source_size": float(trade.size),
                    "hedge_market_id": hedge_market,
                    "hedge_side": hedge_side,
                    "hedge_size": round(hedge_size, 2),
                    "correlation": correlation,
                    "hedge_effectiveness": round(effectiveness, 4),
                    "risk_reduction_pct": round(risk_reduction, 2),
                    "hedge_type": "DIRECT" if effectiveness > 0.7 else "PROXY",
                    "reasoning": f"Market {hedge_market} has {correlation:.2f} correlation - hedges {risk_reduction:.0f}% of position risk",
                })
        except Exception as e:
            logger.error("Failed to find hedges", market=trade.market_id, error=str(e))

        return hedges

    async def _suggest_portfolio_level_hedges(self, trades: List[Trade]) -> List[Dict]:
        """Suggest portfolio-level hedges for aggregate risk."""
        suggestions = []
        yes_exposure = sum(float(t.size) for t in trades if t.side == "YES")
        no_exposure = sum(float(t.size) for t in trades if t.side == "NO")
        imbalance = yes_exposure - no_exposure

        if abs(imbalance) > 500:
            hedge_side = "NO" if imbalance > 0 else "YES"
            suggestions.append({
                "source_market_id": "PORTFOLIO",
                "source_side": "YES" if imbalance > 0 else "NO",
                "source_size": abs(imbalance),
                "hedge_market_id": "DIVERSIFIED",
                "hedge_side": hedge_side,
                "hedge_size": round(abs(imbalance) * 0.5, 2),
                "correlation": -1.0,
                "hedge_effectiveness": 0.5,
                "risk_reduction_pct": 50.0,
                "hedge_type": "PORTFOLIO",
                "reasoning": f"Portfolio has ${abs(imbalance):.0f} {'YES' if imbalance > 0 else 'NO'} directional bias - consider offsetting positions",
            })

        return suggestions

    def _generate_risk_recommendations(self, score: int, concentration: float, bias: float, markets: int) -> List[str]:
        recs = []
        if concentration > 0.5:
            recs.append(f"Reduce concentration: largest position is {concentration*100:.0f}% of portfolio")
        if bias > 0.7:
            recs.append(f"Reduce directional bias: {bias*100:.0f}% tilted to one side")
        if markets < 3:
            recs.append(f"Diversify across more markets (currently {markets})")
        if score < 30:
            recs.append("Portfolio risk is well-managed")
        return recs

    async def _save_suggestion(self, suggestion: Dict):
        try:
            record = HedgeSuggestion(
                source_market_id=suggestion["source_market_id"],
                source_side=suggestion["source_side"],
                source_size=suggestion.get("source_size"),
                hedge_market_id=suggestion["hedge_market_id"],
                hedge_side=suggestion["hedge_side"],
                hedge_size=suggestion["hedge_size"],
                correlation=suggestion["correlation"],
                hedge_effectiveness=suggestion["hedge_effectiveness"],
                risk_reduction_pct=suggestion["risk_reduction_pct"],
                hedge_type=suggestion["hedge_type"],
                reasoning=suggestion.get("reasoning"),
            )
            self.db.add(record)
        except Exception as e:
            logger.error("Failed to save hedge suggestion", error=str(e))

    def _suggestion_to_dict(self, s: HedgeSuggestion) -> Dict:
        return {
            "id": s.id, "source_market_id": s.source_market_id, "source_side": s.source_side,
            "source_size": float(s.source_size) if s.source_size else None,
            "hedge_market_id": s.hedge_market_id, "hedge_side": s.hedge_side,
            "hedge_size": float(s.hedge_size), "correlation": float(s.correlation),
            "hedge_effectiveness": float(s.hedge_effectiveness),
            "risk_reduction_pct": float(s.risk_reduction_pct),
            "hedge_type": s.hedge_type, "reasoning": s.reasoning,
            "is_executed": s.is_executed,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }

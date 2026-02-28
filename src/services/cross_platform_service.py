"""Cross-Platform Odds Comparison Service."""

import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import CrossPlatformOdds
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CrossPlatformService:
    """Compares odds across prediction market platforms (Polymarket, Kalshi, PredictIt, Metaculus)."""

    PLATFORMS = ["polymarket", "kalshi", "predictit", "metaculus"]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compare_odds(self, polymarket_id: str, market_question: str, polymarket_yes: float, polymarket_no: float, polymarket_volume: Optional[float] = None) -> Optional[Dict]:
        """Compare odds for a market across platforms."""
        try:
            other_platforms = await self._fetch_cross_platform_odds(market_question)

            kalshi_yes = other_platforms.get("kalshi", {}).get("yes")
            kalshi_no = other_platforms.get("kalshi", {}).get("no")
            predictit_yes = other_platforms.get("predictit", {}).get("yes")
            predictit_no = other_platforms.get("predictit", {}).get("no")
            metaculus_pred = other_platforms.get("metaculus", {}).get("prediction")

            all_yes = [p for p in [polymarket_yes, kalshi_yes, predictit_yes, metaculus_pred] if p is not None]
            max_spread = max(all_yes) - min(all_yes) if len(all_yes) >= 2 else 0

            has_arb = False
            arb_profit = 0.0
            if kalshi_yes and kalshi_no:
                poly_buy_yes = polymarket_yes
                kalshi_buy_no = kalshi_no
                total_cost = poly_buy_yes + kalshi_buy_no
                if total_cost < 0.98:
                    has_arb = True
                    arb_profit = (1.0 - total_cost) / total_cost * 100

            record = CrossPlatformOdds(
                market_question=market_question,
                polymarket_id=polymarket_id,
                polymarket_yes=polymarket_yes,
                polymarket_no=polymarket_no,
                polymarket_volume=polymarket_volume,
                kalshi_yes=kalshi_yes,
                kalshi_no=kalshi_no,
                kalshi_volume=other_platforms.get("kalshi", {}).get("volume"),
                predictit_yes=predictit_yes,
                predictit_no=predictit_no,
                metaculus_prediction=metaculus_pred,
                max_spread=max_spread,
                arbitrage_opportunity=has_arb,
                arbitrage_profit_pct=arb_profit if has_arb else None,
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)

            return self._record_to_dict(record)
        except Exception as e:
            logger.error("Failed to compare odds", error=str(e))
            await self.db.rollback()
            return None

    async def get_comparisons(self, limit: int = 50, arbitrage_only: bool = False) -> List[Dict]:
        """Get recent odds comparisons."""
        try:
            query = select(CrossPlatformOdds)
            if arbitrage_only:
                query = query.where(CrossPlatformOdds.arbitrage_opportunity == True)
            query = query.order_by(desc(CrossPlatformOdds.matched_at)).limit(limit)

            result = await self.db.execute(query)
            records = result.scalars().all()
            return [self._record_to_dict(r) for r in records]
        except Exception as e:
            logger.error("Failed to get comparisons", error=str(e))
            return []

    async def get_arbitrage_opportunities(self, min_profit_pct: float = 0.5) -> List[Dict]:
        """Get current cross-platform arbitrage opportunities."""
        try:
            result = await self.db.execute(
                select(CrossPlatformOdds)
                .where(
                    CrossPlatformOdds.arbitrage_opportunity == True,
                    CrossPlatformOdds.arbitrage_profit_pct >= min_profit_pct,
                )
                .order_by(desc(CrossPlatformOdds.arbitrage_profit_pct))
                .limit(20)
            )
            records = result.scalars().all()
            return [self._record_to_dict(r) for r in records]
        except Exception as e:
            logger.error("Failed to get arbitrage opportunities", error=str(e))
            return []

    async def get_spread_analysis(self) -> Dict:
        """Analyze spreads across platforms."""
        try:
            result = await self.db.execute(
                select(
                    func.count(CrossPlatformOdds.id),
                    func.avg(CrossPlatformOdds.max_spread),
                    func.max(CrossPlatformOdds.max_spread),
                    func.count(CrossPlatformOdds.id).filter(
                        CrossPlatformOdds.arbitrage_opportunity == True
                    ),
                )
            )
            row = result.one()

            return {
                "total_comparisons": row[0] or 0,
                "avg_spread": round(float(row[1]), 4) if row[1] else 0,
                "max_spread": round(float(row[2]), 4) if row[2] else 0,
                "arbitrage_count": row[3] or 0,
                "platforms_tracked": self.PLATFORMS,
            }
        except Exception as e:
            logger.error("Failed to get spread analysis", error=str(e))
            return {"total_comparisons": 0, "platforms_tracked": self.PLATFORMS}

    async def _fetch_cross_platform_odds(self, question: str) -> Dict:
        """Fetch odds from other platforms using their public APIs."""
        import aiohttp
        platforms = {}

        kalshi_data = await self._fetch_kalshi_odds(question)
        if kalshi_data:
            platforms["kalshi"] = kalshi_data

        metaculus_data = await self._fetch_metaculus_odds(question)
        if metaculus_data:
            platforms["metaculus"] = metaculus_data

        return platforms

    async def _fetch_kalshi_odds(self, question: str) -> Optional[Dict]:
        """Fetch matching market from Kalshi's public API."""
        import aiohttp
        try:
            keywords = [w for w in question.lower().split() if len(w) > 4][:3]
            search_term = " ".join(keywords)

            async with aiohttp.ClientSession() as session:
                url = "https://api.elections.kalshi.com/trade-api/v2/markets"
                params = {"limit": 10, "status": "open"}
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        markets = data.get("markets", [])
                        for market in markets:
                            title = (market.get("title") or "").lower()
                            if any(kw in title for kw in keywords):
                                yes_price = market.get("yes_ask", market.get("last_price"))
                                if yes_price:
                                    yes_price = float(yes_price) / 100 if float(yes_price) > 1 else float(yes_price)
                                    return {
                                        "yes": round(yes_price, 4),
                                        "no": round(1 - yes_price, 4),
                                        "volume": float(market.get("volume", 0)),
                                        "ticker": market.get("ticker"),
                                    }
        except Exception as e:
            logger.debug("Kalshi API fetch failed (may be rate limited)", error=str(e)[:100])
        return None

    async def _fetch_metaculus_odds(self, question: str) -> Optional[Dict]:
        """Fetch matching prediction from Metaculus public API."""
        import aiohttp
        try:
            keywords = [w for w in question.lower().split() if len(w) > 4][:3]
            search_term = " ".join(keywords)

            async with aiohttp.ClientSession() as session:
                url = "https://www.metaculus.com/api2/questions/"
                params = {"search": search_term, "limit": 5, "status": "open"}
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        for q in results:
                            community = q.get("community_prediction", {})
                            if community and community.get("full", {}).get("q2"):
                                prediction = float(community["full"]["q2"])
                                return {"prediction": round(prediction, 4), "metaculus_id": q.get("id")}
        except Exception as e:
            logger.debug("Metaculus API fetch failed", error=str(e)[:100])
        return None

    def _record_to_dict(self, record: CrossPlatformOdds) -> Dict:
        platforms = {"polymarket": {"yes": float(record.polymarket_yes) if record.polymarket_yes else None, "no": float(record.polymarket_no) if record.polymarket_no else None, "volume": float(record.polymarket_volume) if record.polymarket_volume else None}}

        if record.kalshi_yes:
            platforms["kalshi"] = {"yes": float(record.kalshi_yes), "no": float(record.kalshi_no) if record.kalshi_no else None, "volume": float(record.kalshi_volume) if record.kalshi_volume else None}
        if record.predictit_yes:
            platforms["predictit"] = {"yes": float(record.predictit_yes), "no": float(record.predictit_no) if record.predictit_no else None}
        if record.metaculus_prediction:
            platforms["metaculus"] = {"prediction": float(record.metaculus_prediction)}

        return {
            "id": record.id,
            "market_question": record.market_question,
            "polymarket_id": record.polymarket_id,
            "platforms": platforms,
            "max_spread": round(float(record.max_spread), 4) if record.max_spread else 0,
            "arbitrage_opportunity": record.arbitrage_opportunity,
            "arbitrage_profit_pct": round(float(record.arbitrage_profit_pct), 2) if record.arbitrage_profit_pct else None,
            "matched_at": record.matched_at.isoformat() if record.matched_at else None,
        }

"""Semantic Market Clustering - AI-powered grouping of related markets.

Uses keyword extraction and semantic similarity to discover market clusters
that move together, enabling cross-market intelligence no competitor offers.
"""

from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import MarketCluster, Market, MarketCorrelation
from ..utils.logging import get_logger

logger = get_logger(__name__)

STOP_WORDS = {"the", "a", "an", "is", "will", "be", "to", "of", "in", "for", "and", "or", "on", "at", "by", "it", "this", "that", "with", "from", "as", "are", "was", "were", "has", "have", "had", "do", "does", "did", "but", "not", "what", "which", "who", "when", "where", "how", "all", "each", "every", "both", "few", "more", "most", "other", "some", "such", "than", "too", "very", "can", "just", "should", "now"}

CATEGORY_KEYWORDS = {
    "US Politics": {"trump", "biden", "president", "election", "congress", "senate", "house", "democrat", "republican", "gop", "vote", "governor", "primary", "nominee"},
    "Crypto & DeFi": {"bitcoin", "btc", "ethereum", "eth", "crypto", "defi", "solana", "sol", "token", "blockchain", "mining", "halving", "nft"},
    "Economics & Fed": {"fed", "inflation", "cpi", "rate", "fomc", "gdp", "unemployment", "recession", "interest", "treasury", "tariff", "trade"},
    "Geopolitics": {"war", "ukraine", "russia", "china", "nato", "sanctions", "military", "peace", "ceasefire", "iran", "israel"},
    "Sports": {"nba", "nfl", "super bowl", "champion", "playoff", "world cup", "soccer", "football", "basketball", "baseball", "mvp"},
    "Technology": {"ai", "openai", "google", "apple", "meta", "microsoft", "launch", "release", "chatgpt", "agi"},
    "Climate & Science": {"climate", "temperature", "hurricane", "earthquake", "nasa", "space", "spacex", "mars"},
    "Entertainment": {"oscar", "grammy", "movie", "album", "netflix", "spotify", "box office", "celebrity"},
}


class MarketClusterService:
    """Discovers and manages semantically related market clusters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def discover_clusters(self, min_cluster_size: int = 2) -> List[Dict]:
        """Automatically discover market clusters from active markets."""
        try:
            result = await self.db.execute(
                select(Market).where(Market.outcome.is_(None)).order_by(desc(Market.created_at)).limit(500)
            )
            markets = result.scalars().all()

            if not markets:
                return []

            keyword_groups: Dict[str, List] = {}
            for market in markets:
                question = (market.question or "").lower()
                words = set(question.split()) - STOP_WORDS
                for category, cat_keywords in CATEGORY_KEYWORDS.items():
                    overlap = words & cat_keywords
                    if overlap:
                        if category not in keyword_groups:
                            keyword_groups[category] = []
                        keyword_groups[category].append({
                            "market_id": market.market_id,
                            "question": market.question,
                            "keywords": list(overlap),
                            "category": market.category,
                        })

            sub_clusters = self._refine_clusters(keyword_groups)

            created = []
            for cluster_name, members in sub_clusters.items():
                if len(members) < min_cluster_size:
                    continue

                market_ids = [m["market_id"] for m in members]
                all_keywords = []
                for m in members:
                    all_keywords.extend(m.get("keywords", []))
                top_keywords = [w for w, _ in Counter(all_keywords).most_common(10)]

                cluster = MarketCluster(
                    cluster_name=cluster_name,
                    theme=self._generate_theme(cluster_name, top_keywords),
                    keywords=top_keywords,
                    market_ids=market_ids,
                    market_count=len(market_ids),
                    leading_market_id=market_ids[0] if market_ids else None,
                )
                self.db.add(cluster)
                created.append({"name": cluster_name, "markets": len(market_ids), "keywords": top_keywords})

            if created:
                await self.db.commit()
                logger.info("Discovered market clusters", count=len(created))

            return created
        except Exception as e:
            logger.error("Failed to discover clusters", error=str(e))
            await self.db.rollback()
            return []

    async def get_clusters(self, limit: int = 20) -> List[Dict]:
        """Get all market clusters."""
        try:
            result = await self.db.execute(
                select(MarketCluster).order_by(desc(MarketCluster.market_count)).limit(limit)
            )
            clusters = result.scalars().all()
            return [self._cluster_to_dict(c) for c in clusters]
        except Exception as e:
            logger.error("Failed to get clusters", error=str(e))
            return []

    async def get_cluster(self, cluster_id: int) -> Optional[Dict]:
        """Get a specific cluster with market details."""
        try:
            result = await self.db.execute(
                select(MarketCluster).where(MarketCluster.id == cluster_id)
            )
            cluster = result.scalar_one_or_none()
            if not cluster:
                return None

            cdict = self._cluster_to_dict(cluster)
            market_details = []
            for mid in (cluster.market_ids or []):
                mresult = await self.db.execute(
                    select(Market).where(Market.market_id == mid)
                )
                market = mresult.scalar_one_or_none()
                if market:
                    market_details.append({"market_id": market.market_id, "question": market.question, "category": market.category, "outcome": market.outcome})
            cdict["market_details"] = market_details
            return cdict
        except Exception as e:
            logger.error("Failed to get cluster", error=str(e))
            return None

    async def find_market_cluster(self, market_id: str) -> List[Dict]:
        """Find which clusters a market belongs to."""
        try:
            result = await self.db.execute(select(MarketCluster))
            clusters = result.scalars().all()
            matches = []
            for c in clusters:
                if market_id in (c.market_ids or []):
                    matches.append(self._cluster_to_dict(c))
            return matches
        except Exception as e:
            logger.error("Failed to find market cluster", error=str(e))
            return []

    def _refine_clusters(self, groups: Dict[str, List]) -> Dict[str, List]:
        """Refine broad categories into tighter sub-clusters."""
        refined = {}
        for category, members in groups.items():
            if len(members) <= 5:
                refined[category] = members
                continue

            sub_groups: Dict[str, List] = {}
            for m in members:
                kws = frozenset(m.get("keywords", []))
                placed = False
                for sub_name, sub_members in sub_groups.items():
                    existing_kws = set()
                    for sm in sub_members:
                        existing_kws.update(sm.get("keywords", []))
                    if kws & existing_kws:
                        sub_groups[sub_name].append(m)
                        placed = True
                        break
                if not placed:
                    sub_name = f"{category}: {', '.join(list(kws)[:3])}"
                    sub_groups[sub_name] = [m]

            for name, members in sub_groups.items():
                refined[name] = members

        return refined

    def _generate_theme(self, cluster_name: str, keywords: List[str]) -> str:
        return f"Markets related to {cluster_name.lower()} ({', '.join(keywords[:5])})"

    def _cluster_to_dict(self, cluster: MarketCluster) -> Dict:
        return {
            "id": cluster.id, "cluster_name": cluster.cluster_name, "theme": cluster.theme,
            "keywords": cluster.keywords, "market_ids": cluster.market_ids,
            "market_count": cluster.market_count,
            "avg_correlation": float(cluster.avg_correlation) if cluster.avg_correlation else None,
            "cluster_sentiment": float(cluster.cluster_sentiment) if cluster.cluster_sentiment else None,
            "leading_market_id": cluster.leading_market_id,
            "created_at": cluster.created_at.isoformat() if cluster.created_at else None,
        }

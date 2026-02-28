"""Automated Data Collection Pipeline - Feeds all platform services.

Central service that collects price history, order book snapshots, news,
and market data from Polymarket APIs and stores it for all other services
to consume. Should be called periodically (e.g., every 5 minutes alongside
the prediction pipeline).
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..data.sources.polymarket import PolymarketDataSource
from ..database.models import (
    PriceHistory, OrderBookSnapshot, Market,
    NewsArticle, NewsMarketLink,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DataCollectionService:
    """Orchestrates data collection across all Polymarket APIs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_all(self, market_limit: int = 50) -> Dict:
        """Run full data collection cycle for all services."""
        results = {
            "prices_collected": 0,
            "orderbooks_collected": 0,
            "news_collected": 0,
            "markets_updated": 0,
            "errors": [],
        }

        try:
            async with PolymarketDataSource() as polymarket:
                markets = await polymarket.fetch_active_markets(limit=market_limit)
                results["markets_updated"] = len(markets)

                price_tasks = []
                for market in markets:
                    price_tasks.append(
                        self._collect_price(market)
                    )

                if price_tasks:
                    batch_size = 10
                    for i in range(0, len(price_tasks), batch_size):
                        batch = price_tasks[i:i + batch_size]
                        batch_results = await asyncio.gather(*batch, return_exceptions=True)
                        for r in batch_results:
                            if isinstance(r, Exception):
                                results["errors"].append(str(r)[:100])
                            elif r:
                                results["prices_collected"] += 1

                ob_count = 0
                for market in markets[:20]:
                    try:
                        ob = await self._collect_orderbook(polymarket, market)
                        if ob:
                            ob_count += 1
                    except Exception as e:
                        results["errors"].append(f"OB {market.id[:20]}: {str(e)[:50]}")
                results["orderbooks_collected"] = ob_count

                try:
                    news_count = await self._collect_news(markets[:10])
                    results["news_collected"] = news_count
                except Exception as e:
                    results["errors"].append(f"News: {str(e)[:100]}")

                await self.db.commit()

        except Exception as e:
            logger.error("Data collection failed", error=str(e))
            results["errors"].append(str(e))
            await self.db.rollback()

        logger.info(
            "Data collection complete",
            prices=results["prices_collected"],
            orderbooks=results["orderbooks_collected"],
            news=results["news_collected"],
        )
        return results

    async def collect_prices(self, market_limit: int = 50) -> int:
        """Collect price snapshots for active markets."""
        count = 0
        try:
            async with PolymarketDataSource() as polymarket:
                markets = await polymarket.fetch_active_markets(limit=market_limit)
                for market in markets:
                    try:
                        result = await self._collect_price(market)
                        if result:
                            count += 1
                    except Exception as e:
                        logger.debug("Price collection failed", market=market.id[:20], error=str(e))
                await self.db.commit()
        except Exception as e:
            logger.error("Price collection failed", error=str(e))
            await self.db.rollback()
        return count

    async def collect_orderbooks(self, market_limit: int = 20) -> int:
        """Collect order book snapshots for top markets."""
        count = 0
        try:
            async with PolymarketDataSource() as polymarket:
                markets = await polymarket.fetch_active_markets(limit=market_limit)
                for market in markets:
                    try:
                        result = await self._collect_orderbook(polymarket, market)
                        if result:
                            count += 1
                    except Exception as e:
                        logger.debug("Orderbook collection failed", market=market.id[:20], error=str(e))
                await self.db.commit()
        except Exception as e:
            logger.error("Orderbook collection failed", error=str(e))
            await self.db.rollback()
        return count

    async def collect_news_for_markets(self, market_limit: int = 20) -> int:
        """Collect news articles relevant to active markets."""
        try:
            async with PolymarketDataSource() as polymarket:
                markets = await polymarket.fetch_active_markets(limit=market_limit)
                count = await self._collect_news(markets)
                await self.db.commit()
                return count
        except Exception as e:
            logger.error("News collection failed", error=str(e))
            await self.db.rollback()
            return 0

    async def _collect_price(self, market) -> bool:
        """Collect and store a single price data point."""
        try:
            if not market or not market.id:
                return False

            price = PriceHistory(
                market_id=market.id,
                yes_price=market.yes_price or 0.5,
                no_price=market.no_price or 0.5,
                volume=market.volume_24h or 0,
                liquidity=market.liquidity or 0,
                bid_price=None,
                ask_price=None,
                spread=None,
                open_interest=None,
                interval="5m",
                timestamp=datetime.now(timezone.utc),
            )
            self.db.add(price)
            return True
        except Exception as e:
            logger.debug("Failed to store price", error=str(e))
            return False

    async def _collect_orderbook(self, polymarket: PolymarketDataSource, market) -> bool:
        """Collect and store an order book snapshot."""
        try:
            market_data = await polymarket.fetch_market_data(market.id)
            if not market_data:
                return False

            try:
                ob_data = polymarket.client.get_order_book(market.id)
            except Exception:
                return False

            if not ob_data or not isinstance(ob_data, dict):
                return False

            raw_bids = ob_data.get("bids", [])
            raw_asks = ob_data.get("asks", [])

            bids = [{"price": float(b.get("price", 0)), "size": float(b.get("size", 0))} for b in raw_bids[:20]]
            asks = [{"price": float(a.get("price", 0)), "size": float(a.get("size", 0))} for a in raw_asks[:20]]

            if not bids and not asks:
                return False

            best_bid = bids[0]["price"] if bids else None
            best_ask = asks[0]["price"] if asks else None
            mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else None
            spread = best_ask - best_bid if best_bid and best_ask else None
            spread_pct = (spread / mid_price * 100) if spread and mid_price else None

            total_bid_vol = sum(b["size"] * b["price"] for b in bids)
            total_ask_vol = sum(a["size"] * a["price"] for a in asks)
            imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol) if (total_bid_vol + total_ask_vol) > 0 else 0

            snapshot = OrderBookSnapshot(
                market_id=market.id,
                bids=bids,
                asks=asks,
                best_bid=best_bid,
                best_ask=best_ask,
                mid_price=mid_price,
                spread=spread,
                spread_pct=spread_pct,
                imbalance_ratio=imbalance,
                total_bid_volume=total_bid_vol,
                total_ask_volume=total_ask_vol,
                snapshot_time=datetime.now(timezone.utc),
            )
            self.db.add(snapshot)
            return True
        except Exception as e:
            logger.debug("Failed to store orderbook", error=str(e))
            return False

    async def _collect_news(self, markets) -> int:
        """Collect news articles for markets using RSS feeds."""
        count = 0
        try:
            from ..data.sources.rss_news import RSSNewsDataSource

            keywords = set()
            market_keyword_map = {}

            for market in markets:
                question = (market.question or "").lower()
                words = question.split()
                important = [w for w in words if len(w) > 4 and w not in {"about", "which", "would", "could", "should", "there", "where", "their", "these", "those", "being", "other"}]
                if important:
                    keyword = " ".join(important[:3])
                    keywords.add(keyword)
                    market_keyword_map[keyword] = market.id

            async with RSSNewsDataSource() as rss:
                for keyword in list(keywords)[:5]:
                    try:
                        articles = await rss.fetch(keyword, max_articles=5)
                        for article_data in articles:
                            title = article_data.get("title", "")
                            url = article_data.get("url", "")
                            if not title or not url:
                                continue

                            from sqlalchemy import select
                            existing = await self.db.execute(
                                select(NewsArticle.id).where(NewsArticle.url == url)
                            )
                            if existing.scalar():
                                continue

                            article = NewsArticle(
                                title=title,
                                source=article_data.get("source", "RSS"),
                                url=url,
                                summary=article_data.get("description", "")[:500] if article_data.get("description") else None,
                                category=article_data.get("category"),
                                sentiment_score=article_data.get("sentiment_score"),
                                sentiment_label=article_data.get("sentiment_label"),
                                published_at=article_data.get("published_at", datetime.now(timezone.utc)),
                            )
                            self.db.add(article)
                            count += 1
                    except Exception as e:
                        logger.debug("News fetch failed for keyword", keyword=keyword[:30], error=str(e))

        except Exception as e:
            logger.error("News collection pipeline failed", error=str(e))

        return count

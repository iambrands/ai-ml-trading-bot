"""Polymarket data source for fetching market data."""

from datetime import datetime
from typing import List, Optional

import aiohttp
from ..models import Market, MarketData
from ...config.settings import get_settings
from ...utils.logging import get_logger
from ...utils.retry import retry

logger = get_logger(__name__)


class PolymarketDataSource:
    """Fetch market data from Polymarket API."""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Polymarket data source.

        Args:
            api_url: Polymarket API base URL (defaults to settings)
            api_key: Optional API key for authentication (defaults to settings)
        """
        settings = get_settings()
        self.api_url = (api_url or settings.polymarket_api_url).rstrip("/")
        self.api_key = api_key or getattr(settings, "polymarket_api_key", None)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    @retry(max_attempts=3, delay=1.0)
    async def fetch_market(self, market_id: str) -> Optional[Market]:
        """
        Fetch market data by ID.

        Args:
            market_id: Market ID

        Returns:
            Market object or None if not found
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.api_url}/markets/{market_id}"
        try:
            async with self.session.get(url) as response:
                if response.status == 404:
                    return None
                response.raise_for_status()
                data = await response.json()

                return self._parse_market(data)
        except Exception as e:
            logger.error("Failed to fetch market", market_id=market_id, error=str(e))
            raise

    @retry(max_attempts=3, delay=1.0)
    async def fetch_active_markets(self, limit: int = 100) -> List[Market]:
        """
        Fetch active markets.

        Args:
            limit: Maximum number of markets to fetch

        Returns:
            List of active markets
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.api_url}/markets"
        params = {"active": "true", "limit": limit}

        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                markets = []
                for item in data.get("results", []):
                    market = self._parse_market(item)
                    if market:
                        markets.append(market)

                return markets
        except Exception as e:
            logger.error("Failed to fetch active markets", error=str(e))
            raise

    @retry(max_attempts=3, delay=1.0)
    async def fetch_resolved_markets(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 1000
    ) -> List[Market]:
        """
        Fetch resolved markets for training data.

        Note: The Polymarket API may require authentication or have changed endpoints.
        This method attempts multiple endpoint variations.

        Args:
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of markets to fetch

        Returns:
            List of resolved markets
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        # Try different endpoint variations
        endpoints_to_try = [
            f"{self.api_url}/markets",
            f"{self.api_url}/v1/markets",
            f"{self.api_url}/api/v1/markets",
        ]

        params = {"limit": limit}
        
        # Add API key to headers if available
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        
        # Try without active filter first, then filter client-side
        for url in endpoints_to_try:
            try:
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        markets = []
                        for item in data.get("results", []) or data.get("data", []) or []:
                            market = self._parse_market(item)
                            if market:
                                # Filter for resolved markets
                                if market.outcome:
                                    # Apply date filters if provided
                                    if start_date and market.resolved_at:
                                        if market.resolved_at < start_date:
                                            continue
                                    if end_date and market.resolved_at:
                                        if market.resolved_at > end_date:
                                            continue
                                    markets.append(market)
                        
                        if markets:
                            logger.info("Successfully fetched resolved markets", count=len(markets), endpoint=url)
                            return markets[:limit]
                    elif response.status == 403:
                        logger.warning(
                            "API returned 403 Forbidden",
                            endpoint=url,
                            hint="API may require authentication or endpoint may have changed",
                        )
                        continue
                    else:
                        logger.debug("Endpoint returned status", status=response.status, endpoint=url)
                        continue
            except Exception as e:
                logger.debug("Failed to fetch from endpoint", endpoint=url, error=str(e))
                continue

        # If all endpoints failed, return empty list with warning
        logger.warning(
            "Could not fetch resolved markets from any endpoint. "
            "This may be due to: "
            "1) API authentication required (check POLYMARKET_API_KEY in .env), "
            "2) API endpoint changes, "
            "3) Network issues. "
            "Returning empty list - you may need to provide training data manually."
        )
        return []

    async def fetch_market_data(self, market_id: str) -> Optional[MarketData]:
        """
        Fetch complete market data including orderbook.

        Args:
            market_id: Market ID

        Returns:
            MarketData object or None
        """
        market = await self.fetch_market(market_id)
        if not market:
            return None

        # Fetch orderbook if available
        bid_price = market.yes_price
        ask_price = market.yes_price  # Simplified, would fetch from orderbook
        spread = abs(ask_price - bid_price) if bid_price and ask_price else None

        return MarketData(
            market=market,
            timestamp=datetime.utcnow(),
            bid_price=bid_price,
            ask_price=ask_price,
            spread=spread,
        )

    def _parse_market(self, data: dict) -> Optional[Market]:
        """
        Parse market data from API response.

        Args:
            data: Raw API response

        Returns:
            Market object or None
        """
        try:
            # Parse outcome
            outcome = None
            if data.get("resolved"):
                outcome_map = {"YES": "YES", "NO": "NO"}
                outcome = outcome_map.get(data.get("outcome", "").upper())

            # Parse prices
            tokens = data.get("tokens", [])
            yes_token = next((t for t in tokens if t.get("outcome") == "YES"), {})
            no_token = next((t for t in tokens if t.get("outcome") == "NO"), {})

            yes_price = float(yes_token.get("price", 0.0)) if yes_token else 0.0
            no_price = float(no_token.get("price", 0.0)) if no_token else 0.0

            # Parse dates
            resolution_date = None
            if data.get("endDate"):
                try:
                    resolution_date = datetime.fromisoformat(data["endDate"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            created_at = None
            if data.get("created"):
                try:
                    created_at = datetime.fromisoformat(data["created"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            resolved_at = None
            if data.get("resolvedAt"):
                try:
                    resolved_at = datetime.fromisoformat(data["resolvedAt"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            return Market(
                id=str(data.get("id", "")),
                condition_id=str(data.get("conditionId", "")),
                question=str(data.get("question", "")),
                category=data.get("category"),
                resolution_date=resolution_date,
                outcome=outcome,
                yes_price=yes_price,
                no_price=no_price,
                volume_24h=float(data.get("volume24h", 0.0)),
                liquidity=float(data.get("liquidity", 0.0)),
                created_at=created_at,
                resolved_at=resolved_at,
            )
        except Exception as e:
            logger.error("Failed to parse market data", error=str(e), data=data)
            return None


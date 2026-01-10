"""Polymarket data source using py-clob-client."""

from datetime import datetime, timezone
from typing import List, Optional

from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

from ..models import Market, MarketData
from ...config.settings import get_settings
from ...utils.logging import get_logger
from ...utils.retry import retry

logger = get_logger(__name__)


class PolymarketDataSource:
    """Fetch market data from Polymarket using py-clob-client."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        private_key: Optional[str] = None,
        chain_id: int = POLYGON,
    ):
        """
        Initialize Polymarket data source using py-clob-client.

        Args:
            api_url: Polymarket CLOB API URL (defaults to mainnet)
            private_key: Optional private key for authenticated operations
            chain_id: Chain ID (defaults to POLYGON mainnet)
        """
        settings = get_settings()
        self.api_url = api_url or "https://clob.polymarket.com"
        self.private_key = private_key or settings.polymarket_private_key
        self.chain_id = chain_id

        # Initialize ClobClient
        # For read-only operations, we don't need private key
        if self.private_key:
            try:
                self.client = ClobClient(
                    self.api_url,
                    key=self.private_key,
                    chain_id=self.chain_id,
                )
                # Set API credentials if needed for authenticated endpoints
                try:
                    self.client.set_api_creds(self.client.create_or_derive_api_creds())
                except Exception as e:
                    logger.debug("Could not set API credentials", error=str(e))
                    # Continue with read-only access
            except Exception as e:
                logger.warning("Failed to initialize authenticated client, using read-only", error=str(e))
                self.client = ClobClient(self.api_url)
        else:
            # Read-only client (no authentication needed for fetching markets)
            self.client = ClobClient(self.api_url)
            logger.info("Initialized read-only ClobClient", api_url=self.api_url)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass  # ClobClient doesn't need explicit cleanup

    @retry(max_attempts=3, delay=1.0)
    async def fetch_market(self, market_id: str) -> Optional[Market]:
        """
        Fetch market data by ID.

        Args:
            market_id: Market ID or condition ID

        Returns:
            Market object or None if not found
        """
        try:
            # Try to get full market details using get_market()
            try:
                market_data = self.client.get_market(market_id)
                if market_data:
                    return self._parse_market(market_data)
            except Exception as e:
                logger.debug("get_market() failed, trying get_markets()", market_id=market_id, error=str(e))

            # Fallback: search through all markets
            markets_data = self.client.get_markets()
            
            if isinstance(markets_data, dict) and "data" in markets_data:
                markets_list = markets_data["data"]
            elif isinstance(markets_data, list):
                markets_list = markets_data
            else:
                logger.warning("Unexpected markets data format", data_type=type(markets_data))
                return None

            # Find market by ID or condition ID
            for market_data in markets_list:
                condition_id = str(market_data.get("condition_id", ""))
                question_id = str(market_data.get("question_id", ""))
                
                if (
                    condition_id == market_id
                    or question_id == market_id
                    or str(market_data.get("id", "")) == market_id
                ):
                    return self._parse_market(market_data)

            logger.debug("Market not found", market_id=market_id)
            return None

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
        try:
            # Use get_markets() for full market details including question
            markets_data = self.client.get_markets()

            if isinstance(markets_data, dict) and "data" in markets_data:
                markets_list = markets_data["data"]
            elif isinstance(markets_data, list):
                markets_list = markets_data
            else:
                logger.warning("Unexpected markets data format", data_type=type(markets_data))
                return []

            markets = []
            for item in markets_list:
                # Filter for active markets: accepting_orders=True is the best indicator
                # Also check: active=True, closed=False, not archived
                is_active = (
                    item.get("accepting_orders", False)
                    or (
                        item.get("active")
                        and not item.get("closed")
                        and not item.get("archived")
                    )
                )
                
                if is_active:
                    market = self._parse_market(item)
                    if market and not market.outcome:
                        markets.append(market)
                        if len(markets) >= limit:
                            break

            # If no markets found with strict criteria, try a more lenient approach
            if not markets:
                logger.debug("No markets found with strict criteria, trying lenient filter")
                for item in markets_list:
                    # More lenient: just check if it's not closed and not archived
                    if not item.get("closed") and not item.get("archived"):
                        market = self._parse_market(item)
                        if market and not market.outcome:
                            markets.append(market)
                            if len(markets) >= limit:
                                break

            logger.info("Fetched active markets", count=len(markets), limit=limit)
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

        Args:
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of markets to fetch

        Returns:
            List of resolved markets
        """
        try:
            # Use get_markets() for full market details
            markets_data = self.client.get_markets()

            if isinstance(markets_data, dict) and "data" in markets_data:
                markets_list = markets_data["data"]
            elif isinstance(markets_data, list):
                markets_list = markets_data
            else:
                logger.warning("Unexpected markets data format", data_type=type(markets_data))
                return []

            resolved_markets = []
            for item in markets_list:
                # Filter for closed/resolved markets
                if item.get("closed") and not item.get("archived"):
                    market = self._parse_market(item)
                    if market and market.outcome:
                        # Apply date filters if provided
                        if start_date and market.resolved_at:
                            if market.resolved_at < start_date:
                                continue
                        if end_date and market.resolved_at:
                            if market.resolved_at > end_date:
                                continue

                        resolved_markets.append(market)
                        if len(resolved_markets) >= limit:
                            break

            logger.info("Fetched resolved markets", count=len(resolved_markets), limit=limit)
            return resolved_markets

        except Exception as e:
            logger.error("Failed to fetch resolved markets", error=str(e))
            # Return empty list instead of raising to allow graceful degradation
            logger.warning(
                "Could not fetch resolved markets. "
                "This may be due to API limitations or network issues. "
                "You may need to provide training data manually."
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

        try:
            # Try to get midpoint price (most reliable)
            midpoint = self.client.get_midpoint(market_id)
            if midpoint is not None and midpoint > 0:
                bid_price = float(midpoint)
                ask_price = float(midpoint)
                spread = 0.0
                # Update market prices with midpoint
                market.yes_price = bid_price
                market.no_price = 1.0 - bid_price
            else:
                bid_price = market.yes_price
                ask_price = market.yes_price
                spread = None

            # Try to get orderbook for depth information
            try:
                orderbook = self.client.get_order_book(market_id)
                if orderbook and isinstance(orderbook, dict):
                    bids = orderbook.get("bids", [])
                    asks = orderbook.get("asks", [])
                    
                    if bids and len(bids) > 0:
                        bid_price = float(bids[0].get("price", bid_price))
                    if asks and len(asks) > 0:
                        ask_price = float(asks[0].get("price", ask_price))
                    
                    spread = abs(ask_price - bid_price) if bid_price and ask_price else None
                    orderbook_depth = len(bids) + len(asks)
                else:
                    orderbook_depth = None
            except Exception:
                orderbook_depth = None

        except Exception as e:
            logger.debug("Could not fetch midpoint/orderbook", market_id=market_id, error=str(e))
            # Use market prices as fallback
            bid_price = market.yes_price
            ask_price = market.yes_price
            spread = abs(ask_price - bid_price) if bid_price and ask_price else None
            orderbook_depth = None

        return MarketData(
            market=market,
            timestamp=datetime.now(timezone.utc),
            bid_price=bid_price,
            ask_price=ask_price,
            spread=spread,
            orderbook_depth=orderbook_depth,
        )

    def _parse_market(self, data: dict) -> Optional[Market]:
        """
        Parse market data from py-clob-client response.

        Args:
            data: Market data from get_markets() or get_market()

        Returns:
            Market object or None
        """
        try:
            condition_id = str(data.get("condition_id", ""))
            if not condition_id:
                logger.warning("Market data missing condition_id", data_keys=list(data.keys()))
                return None

            # Parse outcome from tokens (winner field)
            outcome = None
            if data.get("closed"):
                tokens = data.get("tokens", [])
                winner_token = next((t for t in tokens if t.get("winner") is True), None)
                if winner_token:
                    # Map token outcome to YES/NO if it's a binary market
                    # For now, we'll use the token outcome as-is
                    token_outcome = winner_token.get("outcome", "")
                    # Simple heuristic: if it's a binary market, try to determine YES/NO
                    # This may need adjustment based on actual market structure
                    if len(tokens) == 2:
                        # Binary market - check if we can determine YES/NO
                        outcomes = [t.get("outcome", "") for t in tokens]
                        if "YES" in outcomes or "NO" in outcomes:
                            outcome = "YES" if winner_token.get("outcome", "").upper() == "YES" else "NO"
                        else:
                            # Non-standard binary market - use first token as YES equivalent
                            outcome = "YES" if winner_token == tokens[0] else "NO"

            # Parse prices from tokens
            yes_price = 0.0
            no_price = 0.0
            tokens = data.get("tokens", [])
            
            if tokens:
                # Try to find YES/NO tokens
                yes_token = next((t for t in tokens if t.get("outcome", "").upper() == "YES"), None)
                no_token = next((t for t in tokens if t.get("outcome", "").upper() == "NO"), None)
                
                if yes_token and no_token:
                    yes_price = float(yes_token.get("price", 0.0))
                    no_price = float(no_token.get("price", 0.0))
                elif len(tokens) == 2:
                    # Binary market with non-standard outcomes - use first as YES
                    yes_price = float(tokens[0].get("price", 0.0))
                    no_price = float(tokens[1].get("price", 0.0)) if len(tokens) > 1 else (1.0 - yes_price)
                elif len(tokens) == 1:
                    # Single token - assume it's YES
                    yes_price = float(tokens[0].get("price", 0.0))
                    no_price = 1.0 - yes_price

            # Try to get midpoint price if available (more accurate than token prices)
            try:
                midpoint = self.client.get_midpoint(condition_id)
                if midpoint is not None and midpoint > 0:
                    yes_price = float(midpoint)
                    no_price = 1.0 - yes_price
            except Exception:
                pass  # Midpoint not available, use token prices or defaults

            # Parse dates
            resolution_date = None
            if data.get("end_date_iso"):
                try:
                    resolution_date = datetime.fromisoformat(data["end_date_iso"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            # For resolved markets, use end_date_iso as resolved_at if closed
            resolved_at = None
            if data.get("closed") and resolution_date:
                resolved_at = resolution_date

            # Get question/title
            question = data.get("question", data.get("title", ""))
            if not question:
                # Try to construct from description or other fields
                question = data.get("description", "")[:100] if data.get("description") else "Unknown Market"

            return Market(
                id=condition_id,
                condition_id=condition_id,
                question=question,
                category=data.get("category"),
                resolution_date=resolution_date,
                outcome=outcome,
                yes_price=yes_price,
                no_price=no_price,
                volume_24h=float(data.get("volume24h", data.get("volume_24h", 0.0))),
                liquidity=float(data.get("liquidity", 0.0)),
                created_at=None,  # Not available in get_markets() response
                resolved_at=resolved_at,
            )
        except Exception as e:
            logger.error("Failed to parse market data", error=str(e), data_keys=list(data.keys()) if isinstance(data, dict) else "not_dict")
            return None

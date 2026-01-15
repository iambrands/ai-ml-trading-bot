"""Polymarket data source using py-clob-client and Gamma API."""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
import aiohttp

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
        self.gamma_api_url = "https://gamma-api.polymarket.com"  # Gamma API for volume data
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
        pass
    
    async def _fetch_gamma_markets(self, limit: int = 100) -> List[dict]:
        """
        Fetch markets from Gamma API which includes volume data.
        
        Args:
            limit: Maximum number of markets to return
            
        Returns:
            List of market dictionaries from Gamma API
        """
        from ...utils.rate_limiter import get_rate_limiter, RateLimitExceeded
        
        try:
            # Check rate limit
            limiter = get_rate_limiter()
            if not limiter.check_and_increment('gamma'):
                remaining = limiter.get_remaining('gamma')
                logger.warning(
                    "Gamma API rate limit exceeded, continuing without volume data",
                    remaining=remaining
                )
                return []
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.gamma_api_url}/markets"
                params = {
                    "limit": limit,
                    "active": "true",
                    "closed": "false",
                    "order": "volume24hr",
                    "ascending": "false",
                }
                logger.debug("Fetching from Gamma API", url=url, params=params)
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Gamma API might return list directly or wrapped
                        if isinstance(data, list):
                            logger.debug("Gamma API returned list", count=len(data))
                            return data
                        elif isinstance(data, dict) and "data" in data:
                            logger.debug("Gamma API returned dict with data", count=len(data.get("data", [])))
                            return data["data"]
                        else:
                            logger.warning("Unexpected Gamma API response format", data_type=type(data), keys=list(data.keys()) if isinstance(data, dict) else None)
                            return []
                    else:
                        error_text = await response.text()
                        logger.warning("Gamma API request failed", status=response.status, error=error_text[:200])
                        return []
        except RateLimitExceeded as e:
            logger.warning("Gamma API rate limit exceeded, continuing without volume data", error=str(e))
            return []
        except Exception as e:
            logger.warning("Failed to fetch from Gamma API, continuing without volume data", error=str(e), exc_info=True)
            return []

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
        Fetch active markets, combining volume from Gamma API and prices from CLOB API.

        Args:
            limit: Maximum number of markets to fetch

        Returns:
            List of active markets
        """
        try:
            # 1. Try to fetch markets from Gamma API for volume and other metadata
            gamma_markets_map = {}
            try:
                gamma_markets_data = await self._fetch_gamma_markets(limit=limit * 2)  # Fetch more to increase match chances
                gamma_markets_map = {m.get('id'): m for m in gamma_markets_data if m.get('id')}
                gamma_markets_map.update({m.get('conditionId'): m for m in gamma_markets_data if m.get('conditionId')})  # Also index by conditionId
                logger.info("Fetched Gamma API markets", count=len(gamma_markets_data), mapped=len(gamma_markets_map))
            except Exception as e:
                logger.warning("Gamma API fetch failed, continuing without volume data", error=str(e))

            # 2. Fetch markets from CLOB API for real-time prices and order book
            markets_data = self.client.get_markets()

            if isinstance(markets_data, dict) and "data" in markets_data:
                clob_markets_list = markets_data["data"]
            elif isinstance(markets_data, list):
                clob_markets_list = markets_data
            else:
                logger.warning("Unexpected CLOB markets data format", data_type=type(markets_data))
                return []

            logger.info("Fetched CLOB markets", count=len(clob_markets_list))
            
            # Log sample markets from both APIs for debugging
            if clob_markets_list and len(clob_markets_list) > 0:
                sample_clob = clob_markets_list[0]
                logger.info("Sample CLOB market structure", 
                           condition_id_snake=sample_clob.get('condition_id', 'N/A')[:20] if sample_clob.get('condition_id') else None,
                           condition_id_camel=sample_clob.get('conditionId', 'N/A')[:20] if sample_clob.get('conditionId') else None,
                           id_field=sample_clob.get('id', 'N/A')[:20] if sample_clob.get('id') else None,
                           question_id=sample_clob.get('question_id', 'N/A')[:20] if sample_clob.get('question_id') else None,
                           accepting_orders=sample_clob.get('accepting_orders'),
                           active=sample_clob.get('active'),
                           closed=sample_clob.get('closed'),
                           archived=sample_clob.get('archived'),
                           all_keys=list(sample_clob.keys()))
            
            if gamma_markets_data and len(gamma_markets_data) > 0:
                sample_gamma = gamma_markets_data[0]
                logger.debug("Sample Gamma market",
                           id=sample_gamma.get('id', 'N/A')[:20],
                           conditionId=sample_gamma.get('conditionId', 'N/A')[:20],
                           keys=list(sample_gamma.keys())[:15])

            markets = []
            strict_filtered = 0
            parse_failed = 0
            outcome_filtered = 0
            no_market_id = 0
            
            for item in clob_markets_list:
                # CLOB API may use 'condition_id' (snake_case) or 'conditionId' (camelCase)
                # Also check for 'id' or 'question_id'
                market_id = (
                    item.get('condition_id') or 
                    item.get('conditionId') or 
                    item.get('id') or 
                    item.get('question_id') or
                    item.get('questionId')
                )
                condition_id = (
                    item.get('condition_id') or 
                    item.get('conditionId') or 
                    item.get('id')
                )
                if not market_id:
                    no_market_id += 1
                    if no_market_id <= 3:
                        logger.warning("Market skipped - no ID found", 
                                     item_keys=list(item.keys())[:15],
                                     sample_item=dict(list(item.items())[:5]))
                    continue

                # Merge volume data from Gamma API if available (try both id and conditionId)
                gamma_market_item = gamma_markets_map.get(market_id) or gamma_markets_map.get(condition_id)
                if gamma_market_item:
                    # Merge volume data from Gamma API into the CLOB market item
                    item['volume24hr'] = gamma_market_item.get('volume24hr', 0.0)
                    item['liquidity'] = gamma_market_item.get('liquidity', 0.0)
                    item['volume'] = gamma_market_item.get('volume', 0.0)  # Total volume
                    logger.debug("Merged volume data from Gamma API", market_id=market_id[:20], volume24hr=item.get('volume24hr', 0.0))

                # Filter for valid markets
                # 1. Filter out archived markets (completely removed from platform)
                is_archived = item.get("archived", False)
                if is_archived:
                    strict_filtered += 1
                    if strict_filtered <= 5:  # Log first few to debug
                        logger.debug("Market filtered - archived", 
                                   market_id=market_id[:20],
                                   archived=is_archived)
                    continue
                
                # 2. Filter out markets that have already ended (stale data)
                end_date_str = item.get("end_date_iso") or item.get("end_date")
                if end_date_str:
                    try:
                        # Parse ISO date string
                        if end_date_str.endswith('Z'):
                            end_date_str = end_date_str.replace('Z', '+00:00')
                        end_date = datetime.fromisoformat(end_date_str)
                        # Use UTC if timezone-naive
                        if end_date.tzinfo is None:
                            end_date = end_date.replace(tzinfo=timezone.utc)
                        # Filter out markets that ended more than 1 day ago
                        # (Allow some buffer for recently resolved markets)
                        now = datetime.now(timezone.utc)
                        if end_date < (now - timedelta(days=1)):
                            strict_filtered += 1
                            if strict_filtered <= 5:
                                logger.debug("Market filtered - ended", 
                                           market_id=market_id[:20],
                                           end_date=end_date_str,
                                           days_ago=(now - end_date).days)
                            continue
                    except (ValueError, TypeError) as e:
                        # If date parsing fails, log but don't filter (might be valid market)
                        logger.debug("Could not parse end_date", market_id=market_id[:20], end_date=end_date_str, error=str(e))
                
                # 3. Parse market object
                market = self._parse_market(item)
                if not market:
                    parse_failed += 1
                    if parse_failed <= 3:
                        logger.debug("Market parse failed", market_id=market_id[:20], item_keys=list(item.keys())[:10])
                    continue
                    
                # 4. Filter out markets with resolved outcomes (already resolved)
                if market.outcome:
                    outcome_filtered += 1
                    continue
                
                markets.append(market)
                if len(markets) >= limit:
                    break

            logger.info("Filter results", 
                       total_clob=len(clob_markets_list),
                       no_market_id=no_market_id,
                       strict_filtered=strict_filtered, 
                       parse_failed=parse_failed, 
                       outcome_filtered=outcome_filtered,
                       markets_found=len(markets))

            # If no markets found, log detailed debugging info
            if not markets:
                logger.warning("No active markets found after filtering", 
                             total_clob=len(clob_markets_list),
                             strict_filtered=strict_filtered,
                             parse_failed=parse_failed,
                             outcome_filtered=outcome_filtered,
                             no_market_id=no_market_id)
                
                # Log first few markets that were filtered to understand why
                sample_count = 0
                for item in clob_markets_list[:10]:
                    market_id = (
                        item.get('condition_id') or 
                        item.get('conditionId') or 
                        item.get('id') or 
                        item.get('question_id') or
                        item.get('questionId')
                    )
                    if market_id:
                        logger.debug("Sample filtered market",
                                   market_id=market_id[:20],
                                   question=item.get('question', item.get('title', 'N/A'))[:50],
                                   closed=item.get('closed'),
                                   archived=item.get('archived'),
                                   accepting_orders=item.get('accepting_orders'),
                                   active=item.get('active'))
                        sample_count += 1
                        if sample_count >= 5:
                            break

            logger.info("Fetched active markets", count=len(markets), limit=limit, gamma_matches=len([m for m in markets if m.volume_24h > 0]))
            return markets

        except Exception as e:
            logger.error("Failed to fetch active markets", error=str(e), exc_info=True)
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
            
            # Debug: Log available keys if volume is missing (only first time to avoid spam)
            if "volume_24h" not in data and "volume24h" not in data and "volume" not in data:
                logger.debug(
                    "Volume fields not found in market data",
                    market_id=data.get("condition_id", "unknown")[:20],
                    available_keys=[k for k in data.keys() if "vol" in k.lower() or "liq" in k.lower() or "trade" in k.lower()],
                    all_keys_sample=list(data.keys())[:10],
                )

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
                # Use volume24hr from Gamma API (correct field name per Polymarket docs)
                # Fallback to other variations if needed
                volume_24h=float(
                    data.get("volume24hr")  # Correct field name from Gamma API
                    or data.get("volume24h")
                    or data.get("volume_24h")
                    or data.get("volume24H")
                    or data.get("volumeUSD")
                    or data.get("volume_usd")
                    or data.get("volume")
                    or 0.0
                ),
                liquidity=float(data.get("liquidity") or data.get("totalLiquidity") or data.get("total_liquidity") or 0.0),
                created_at=None,  # Not available in get_markets() response
                resolved_at=resolved_at,
            )
        except Exception as e:
            logger.error("Failed to parse market data", error=str(e), data_keys=list(data.keys()) if isinstance(data, dict) else "not_dict")
            return None

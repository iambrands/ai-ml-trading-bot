"""Market feature extraction."""

from typing import Dict

from ..data.models import Market, MarketData
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MarketFeatureExtractor:
    """Extract market-based features."""

    def extract(self, market_data: MarketData) -> Dict[str, float]:
        """
        Extract market features.

        Args:
            market_data: MarketData object

        Returns:
            Dictionary of feature names to values
        """
        market = market_data.market
        features = {}

        # Price features
        features["current_price"] = market.yes_price
        features["no_price"] = market.no_price
        features["price_sum"] = market.yes_price + market.no_price  # Should be close to 1.0

        # Spread features
        if market_data.spread is not None:
            features["bid_ask_spread"] = market_data.spread
        else:
            features["bid_ask_spread"] = abs(market.yes_price - market.no_price)

        # Volume and liquidity features
        features["volume_24h"] = market.volume_24h
        features["liquidity"] = market.liquidity
        features["volume_liquidity_ratio"] = (
            market.volume_24h / market.liquidity if market.liquidity > 0 else 0.0
        )

        # Price momentum (would need historical data for proper calculation)
        # For now, use simple heuristic based on price proximity to 0 or 1
        features["price_extremity"] = abs(market.yes_price - 0.5) * 2  # 0 to 1
        features["price_confidence"] = max(market.yes_price, market.no_price)  # Higher = more confident

        # Orderbook depth (if available)
        if market_data.orderbook_depth is not None:
            features["orderbook_depth"] = market_data.orderbook_depth
        else:
            features["orderbook_depth"] = market.liquidity

        return features


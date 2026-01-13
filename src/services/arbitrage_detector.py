"""Arbitrage detection service for Polymarket markets.

Polymarket YES/NO prices should always add to $1.00. When they don't,
there's a guaranteed profit opportunity by buying both sides.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict
import logging

from ..data.models import Market
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ArbitrageOpportunity:
    """Represents an arbitrage opportunity."""

    def __init__(
        self,
        market_id: str,
        question: str,
        yes_price: float,
        no_price: float,
        combined_price: float,
        profit: float,
        profit_percent: float,
        volume_24h: float = 0.0,
        liquidity: float = 0.0,
        detected_at: Optional[datetime] = None,
    ):
        self.market_id = market_id
        self.question = question
        self.yes_price = yes_price
        self.no_price = no_price
        self.combined_price = combined_price
        self.profit = profit
        self.profit_percent = profit_percent
        self.volume_24h = volume_24h
        self.liquidity = liquidity
        self.detected_at = detected_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        return {
            "market_id": self.market_id,
            "question": self.question,
            "yes_price": self.yes_price,
            "no_price": self.no_price,
            "combined_price": self.combined_price,
            "profit": self.profit,
            "profit_percent": self.profit_percent,
            "volume_24h": self.volume_24h,
            "liquidity": self.liquidity,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }

    def __repr__(self):
        return (
            f"ArbitrageOpportunity(market_id={self.market_id[:20]}, "
            f"profit=${self.profit:.4f}, profit_percent={self.profit_percent:.2f}%)"
        )


class ArbitrageDetector:
    """Detects arbitrage opportunities in Polymarket markets."""

    def __init__(
        self,
        min_profit: float = 0.025,  # Minimum 2.5% profit
        min_liquidity: float = 100.0,  # Minimum $100 liquidity
        min_volume: float = 0.0,  # Minimum 24h volume (optional)
    ):
        """
        Initialize arbitrage detector.

        Args:
            min_profit: Minimum profit threshold (default: 0.025 = 2.5%)
            min_liquidity: Minimum liquidity required (default: $100)
            min_volume: Minimum 24h volume (default: 0 = no filter)
        """
        self.min_profit = min_profit
        self.min_liquidity = min_liquidity
        self.min_volume = min_volume
        logger.info(
            "Arbitrage detector initialized",
            min_profit=f"{min_profit:.2%}",
            min_liquidity=f"${min_liquidity:.2f}",
            min_volume=f"${min_volume:.2f}",
        )

    def detect_arbitrage(self, market: Market) -> Optional[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunity in a single market.

        Args:
            market: Market object with yes_price and no_price

        Returns:
            ArbitrageOpportunity if found, None otherwise
        """
        try:
            # Get prices
            yes_price = float(market.yes_price) if market.yes_price else 0.0
            no_price = float(market.no_price) if market.no_price else 0.0

            # Validate prices
            if yes_price <= 0 or no_price <= 0:
                return None

            # Calculate combined price
            combined_price = yes_price + no_price

            # Check if arbitrage exists (combined < 1.00)
            if combined_price >= 1.0:
                return None

            # Calculate profit
            profit = 1.0 - combined_price
            profit_percent = (profit / combined_price) * 100

            # Check minimum profit threshold
            if profit < self.min_profit:
                return None

            # Check liquidity (if available)
            liquidity = getattr(market, "liquidity", 0.0) or getattr(market, "volume_24h", 0.0) or 0.0
            if liquidity > 0 and liquidity < self.min_liquidity:
                return None

            # Check volume (if available and required)
            volume_24h = getattr(market, "volume_24h", 0.0) or 0.0
            if self.min_volume > 0 and volume_24h < self.min_volume:
                return None

            # Create opportunity
            opportunity = ArbitrageOpportunity(
                market_id=market.id,
                question=market.question,
                yes_price=yes_price,
                no_price=no_price,
                combined_price=combined_price,
                profit=profit,
                profit_percent=profit_percent,
                volume_24h=volume_24h,
                liquidity=liquidity,
            )

            logger.debug(
                "Arbitrage opportunity detected",
                market_id=market.id[:20],
                profit=f"${profit:.4f}",
                profit_percent=f"{profit_percent:.2f}%",
            )

            return opportunity

        except Exception as e:
            logger.warning(
                "Failed to detect arbitrage for market",
                market_id=market.id if hasattr(market, "id") else "unknown",
                error=str(e),
            )
            return None

    def detect_arbitrage_batch(
        self, markets: List[Market]
    ) -> List[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunities in multiple markets.

        Args:
            markets: List of Market objects

        Returns:
            List of ArbitrageOpportunity objects, sorted by profit (highest first)
        """
        opportunities = []

        for market in markets:
            opportunity = self.detect_arbitrage(market)
            if opportunity:
                opportunities.append(opportunity)

        # Sort by profit (highest first)
        opportunities.sort(key=lambda x: x.profit, reverse=True)

        logger.info(
            "Arbitrage detection complete",
            markets_checked=len(markets),
            opportunities_found=len(opportunities),
        )

        return opportunities

    def calculate_execution_cost(
        self, opportunity: ArbitrageOpportunity, trade_size: float = 100.0
    ) -> Dict:
        """
        Calculate the cost and profit of executing an arbitrage trade.

        Args:
            opportunity: ArbitrageOpportunity to execute
            trade_size: Size of trade in dollars (default: $100)

        Returns:
            Dictionary with execution details
        """
        # Calculate how much to buy of each side
        yes_amount = trade_size * (opportunity.yes_price / opportunity.combined_price)
        no_amount = trade_size * (opportunity.no_price / opportunity.combined_price)

        # Total cost
        total_cost = yes_amount + no_amount

        # Guaranteed payout (always $1.00 per share)
        total_payout = trade_size

        # Net profit
        net_profit = total_payout - total_cost
        net_profit_percent = (net_profit / total_cost) * 100

        # Calculate shares
        yes_shares = yes_amount / opportunity.yes_price
        no_shares = no_amount / opportunity.no_price

        return {
            "trade_size": trade_size,
            "yes_amount": yes_amount,
            "no_amount": no_amount,
            "yes_shares": yes_shares,
            "no_shares": no_shares,
            "total_cost": total_cost,
            "total_payout": total_payout,
            "net_profit": net_profit,
            "net_profit_percent": net_profit_percent,
            "opportunity": opportunity.to_dict(),
        }

    def get_arbitrage_stats(self, opportunities: List[ArbitrageOpportunity]) -> Dict:
        """
        Get statistics about arbitrage opportunities.

        Args:
            opportunities: List of ArbitrageOpportunity objects

        Returns:
            Dictionary with statistics
        """
        if not opportunities:
            return {
                "total_opportunities": 0,
                "total_profit_potential": 0.0,
                "avg_profit_percent": 0.0,
                "max_profit": 0.0,
                "min_profit": 0.0,
            }

        total_profit = sum(opp.profit for opp in opportunities)
        avg_profit_percent = sum(opp.profit_percent for opp in opportunities) / len(opportunities)
        max_profit = max(opp.profit for opp in opportunities)
        min_profit = min(opp.profit for opp in opportunities)

        return {
            "total_opportunities": len(opportunities),
            "total_profit_potential": total_profit,
            "avg_profit_percent": avg_profit_percent,
            "max_profit": max_profit,
            "min_profit": min_profit,
            "max_profit_percent": max(opp.profit_percent for opp in opportunities),
            "min_profit_percent": min(opp.profit_percent for opp in opportunities),
        }


"""Position sizing using Kelly Criterion."""

from typing import Optional

from .signal_generator import TradingSignal
from ..config.settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PositionSizer:
    """Position sizing using Kelly Criterion with fractional Kelly for safety."""

    def __init__(
        self,
        kelly_fraction: Optional[float] = None,
        max_position_pct: Optional[float] = None,
        max_total_exposure: Optional[float] = None,
        min_position_size: float = 10.0,
    ):
        """
        Initialize position sizer.

        Args:
            kelly_fraction: Fraction of Kelly to use (default from settings)
            max_position_pct: Maximum % of bankroll per trade (default from settings)
            max_total_exposure: Maximum total exposure (default from settings)
            min_position_size: Minimum position size in USD
        """
        settings = get_settings()
        self.kelly_fraction = kelly_fraction if kelly_fraction is not None else settings.kelly_fraction
        self.max_position_pct = max_position_pct if max_position_pct is not None else settings.max_position_pct
        self.max_total_exposure = max_total_exposure if max_total_exposure is not None else settings.max_total_exposure
        self.min_position_size = min_position_size

    def calculate_kelly(self, edge: float, market_price: float) -> float:
        """
        Calculate Kelly fraction for binary bet.

        Simplified Kelly for prediction markets:
        f* ≈ edge / market_price

        Args:
            edge: Edge (model_prob - market_price)
            market_price: Current market price

        Returns:
            Kelly fraction (0 to 1)
        """
        if market_price <= 0 or market_price >= 1:
            return 0.0

        # Simplified Kelly: edge / price
        kelly = edge / market_price

        # Clamp to [0, 1]
        kelly = max(0.0, min(1.0, kelly))

        return kelly

    def calculate_position_size(
        self,
        signal: TradingSignal,
        bankroll: float,
        current_exposure: float = 0.0,
    ) -> float:
        """
        Calculate position size with all constraints.

        Args:
            signal: TradingSignal object
            bankroll: Current bankroll
            current_exposure: Current total exposure

        Returns:
            Position size in USD
        """
        if bankroll <= 0:
            return 0.0

        # Calculate raw Kelly
        if signal.side == "YES":
            price = signal.market_probability
            edge = signal.model_probability - price
        else:
            price = 1.0 - signal.market_probability
            edge = (1.0 - signal.model_probability) - price

        kelly = self.calculate_kelly(edge, price)

        # Apply fractional Kelly
        kelly_size = bankroll * kelly * self.kelly_fraction

        # Apply confidence adjustment
        kelly_size *= signal.confidence

        # Cap at maximum position percentage
        max_size = bankroll * self.max_position_pct
        size = min(kelly_size, max_size)

        # Check total exposure limit
        remaining_exposure = (self.max_total_exposure * bankroll) - current_exposure
        size = min(size, remaining_exposure)

        # Apply minimum size constraint
        size = max(size, self.min_position_size)

        # Final check: don't exceed bankroll
        size = min(size, bankroll)

        logger.debug(
            "Calculated position size",
            signal_id=signal.market_id,
            side=signal.side,
            size=size,
            kelly=kelly,
            edge=edge,
        )

        return max(0.0, size)




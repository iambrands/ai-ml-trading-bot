"""Risk limits and position constraints."""

from typing import Dict, Optional

from ..trading.portfolio import Portfolio
from ..trading.signal_generator import TradingSignal
from ..config.settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RiskLimits:
    """Risk limits and position constraints."""

    def __init__(
        self,
        max_position_pct: Optional[float] = None,
        max_total_exposure: Optional[float] = None,
        max_positions: int = 20,
        max_daily_loss: Optional[float] = None,
    ):
        """
        Initialize risk limits.

        Args:
            max_position_pct: Maximum % of bankroll per trade
            max_total_exposure: Maximum total exposure
            max_positions: Maximum number of concurrent positions
            max_daily_loss: Maximum daily loss as fraction of capital
        """
        settings = get_settings()
        self.max_position_pct = max_position_pct or settings.max_position_pct
        self.max_total_exposure = max_total_exposure or settings.max_total_exposure
        self.max_positions = max_positions
        self.max_daily_loss = max_daily_loss or settings.max_daily_loss

    def check_position_limit(self, portfolio: Portfolio, size: float) -> bool:
        """
        Check if position size is within limits.

        Args:
            portfolio: Portfolio instance
            size: Proposed position size

        Returns:
            True if within limits, False otherwise
        """
        total_value = portfolio.total_value

        # Check max position percentage
        if size > total_value * self.max_position_pct:
            logger.warning(
                "Position size exceeds limit",
                size=size,
                max_size=total_value * self.max_position_pct,
                max_pct=self.max_position_pct,
            )
            return False

        # Check total exposure
        new_exposure = portfolio.total_exposure + size
        if new_exposure > total_value * self.max_total_exposure:
            logger.warning(
                "Total exposure would exceed limit",
                current_exposure=portfolio.total_exposure,
                new_exposure=new_exposure,
                max_exposure=total_value * self.max_total_exposure,
            )
            return False

        # Check max positions
        if len(portfolio.positions) >= self.max_positions:
            logger.warning(
                "Maximum positions reached",
                current_positions=len(portfolio.positions),
                max_positions=self.max_positions,
            )
            return False

        return True

    def check_daily_loss_limit(self, portfolio: Portfolio, initial_value: float) -> bool:
        """
        Check if daily loss limit is exceeded.

        Args:
            portfolio: Portfolio instance
            initial_value: Portfolio value at start of day

        Returns:
            True if within limit, False if limit exceeded
        """
        current_value = portfolio.total_value
        daily_loss = (initial_value - current_value) / initial_value

        if daily_loss > self.max_daily_loss:
            logger.error(
                "Daily loss limit exceeded",
                daily_loss=daily_loss,
                max_daily_loss=self.max_daily_loss,
                initial_value=initial_value,
                current_value=current_value,
            )
            return False

        return True

    def can_open_position(
        self, portfolio: Portfolio, signal: TradingSignal, size: float
    ) -> tuple[bool, str]:
        """
        Check if a new position can be opened.

        Args:
            portfolio: Portfolio instance
            signal: Trading signal
            size: Proposed position size

        Returns:
            Tuple of (can_open, reason)
        """
        # Check if position already exists
        if portfolio.get_position(signal.market_id):
            return False, "Position already exists"

        # Check position limits
        if not self.check_position_limit(portfolio, size):
            return False, "Position limit exceeded"

        # Check cash availability
        if portfolio.cash < size:
            return False, "Insufficient cash"

        return True, "OK"



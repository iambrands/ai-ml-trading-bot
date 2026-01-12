"""Circuit breaker for emergency stops."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from ..trading.portfolio import Portfolio
from .drawdown import DrawdownMonitor
from .limits import RiskLimits
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Trading halted
    HALF_OPEN = "half_open"  # Testing if conditions improved


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    max_drawdown: float = 0.15
    max_daily_loss: float = 0.05
    consecutive_losses: int = 5
    cooldown_minutes: int = 60


class CircuitBreaker:
    """Circuit breaker for emergency trading stops."""

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.risk_limits = RiskLimits()
        self.drawdown_monitor = DrawdownMonitor(max_drawdown=self.config.max_drawdown)
        self.consecutive_losses = 0
        self.last_open_time: Optional[datetime] = None
        self.initial_value: Optional[float] = None

    def check(self, portfolio: Portfolio) -> bool:
        """
        Check if trading should continue.

        Args:
            portfolio: Portfolio instance

        Returns:
            True if trading can continue, False if circuit breaker is open
        """
        # Initialize initial value on first check
        if self.initial_value is None:
            self.initial_value = portfolio.total_value

        # Update drawdown monitor
        snapshot = self.drawdown_monitor.update(portfolio)

        # Check drawdown limit
        if snapshot.drawdown > self.config.max_drawdown:
            self._open("Maximum drawdown exceeded", snapshot.drawdown)
            return False

        # Check daily loss limit
        if self.initial_value:
            daily_loss = (self.initial_value - portfolio.total_value) / self.initial_value
            if daily_loss > self.config.max_daily_loss:
                self._open("Daily loss limit exceeded", daily_loss)
                return False

        # Check consecutive losses
        if portfolio.trades:
            recent_trades = portfolio.trades[-self.config.consecutive_losses:]
            if len(recent_trades) >= self.config.consecutive_losses:
                if all(t.pnl < 0 for t in recent_trades):
                    self._open("Too many consecutive losses", len(recent_trades))
                    return False

        # Reset consecutive losses if we have a win
        if portfolio.trades and portfolio.trades[-1].pnl > 0:
            self.consecutive_losses = 0

        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == CircuitBreakerState.OPEN:
            if self.last_open_time:
                elapsed = (datetime.utcnow() - self.last_open_time).total_seconds() / 60
                if elapsed >= self.config.cooldown_minutes:
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN")

        # HALF_OPEN state: allow limited trading to test conditions
        if self.state == CircuitBreakerState.HALF_OPEN:
            # If conditions improved, close circuit breaker
            if snapshot.drawdown < self.config.max_drawdown * 0.5:
                self._close()
                return True
            # If conditions worsened, open again
            elif snapshot.drawdown > self.config.max_drawdown:
                self._open("Conditions worsened in HALF_OPEN", snapshot.drawdown)
                return False

        return self.state == CircuitBreakerState.CLOSED or self.state == CircuitBreakerState.HALF_OPEN

    def _open(self, reason: str, value: float) -> None:
        """Open circuit breaker."""
        if self.state != CircuitBreakerState.OPEN:
            logger.error("Circuit breaker OPEN", reason=reason, value=value)
            self.state = CircuitBreakerState.OPEN
            self.last_open_time = datetime.utcnow()

    def _close(self) -> None:
        """Close circuit breaker."""
        logger.info("Circuit breaker CLOSED")
        self.state = CircuitBreakerState.CLOSED
        self.last_open_time = None
        self.consecutive_losses = 0
        # Reset initial value for new day
        self.initial_value = None

    def reset_daily(self) -> None:
        """Reset daily tracking (call at start of each day)."""
        self.initial_value = None
        self.consecutive_losses = 0
        if self.state == CircuitBreakerState.OPEN:
            # Reset to HALF_OPEN after cooldown
            self.state = CircuitBreakerState.HALF_OPEN




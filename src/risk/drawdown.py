"""Drawdown monitoring and management."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..trading.portfolio import Portfolio
from ..config.settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DrawdownSnapshot:
    """Drawdown snapshot at a point in time."""

    timestamp: datetime
    peak_value: float
    current_value: float
    drawdown: float  # As fraction (0 to 1)
    drawdown_pct: float  # As percentage


class DrawdownMonitor:
    """Monitor and manage drawdown."""

    def __init__(self, max_drawdown: Optional[float] = None):
        """
        Initialize drawdown monitor.

        Args:
            max_drawdown: Maximum allowed drawdown as fraction (e.g., 0.15 = 15%)
        """
        settings = get_settings()
        self.max_drawdown = max_drawdown or settings.max_drawdown
        self.peak_value: Optional[float] = None
        self.snapshots: List[DrawdownSnapshot] = []

    def update(self, portfolio: Portfolio) -> DrawdownSnapshot:
        """
        Update drawdown tracking.

        Args:
            portfolio: Portfolio instance

        Returns:
            DrawdownSnapshot
        """
        current_value = portfolio.total_value

        # Update peak value
        if self.peak_value is None or current_value > self.peak_value:
            self.peak_value = current_value

        # Calculate drawdown
        drawdown = (self.peak_value - current_value) / self.peak_value
        drawdown_pct = drawdown * 100

        snapshot = DrawdownSnapshot(
            timestamp=datetime.utcnow(),
            peak_value=self.peak_value,
            current_value=current_value,
            drawdown=drawdown,
            drawdown_pct=drawdown_pct,
        )

        self.snapshots.append(snapshot)

        # Check if drawdown limit exceeded
        if drawdown > self.max_drawdown:
            logger.error(
                "Maximum drawdown exceeded",
                drawdown=drawdown,
                max_drawdown=self.max_drawdown,
                peak_value=self.peak_value,
                current_value=current_value,
            )

        return snapshot

    def get_current_drawdown(self) -> float:
        """Get current drawdown."""
        if not self.snapshots:
            return 0.0
        return self.snapshots[-1].drawdown

    def is_drawdown_limit_exceeded(self) -> bool:
        """Check if drawdown limit is exceeded."""
        return self.get_current_drawdown() > self.max_drawdown

    def get_max_drawdown(self) -> float:
        """Get maximum drawdown seen."""
        if not self.snapshots:
            return 0.0
        return max(s.drawdown for s in self.snapshots)



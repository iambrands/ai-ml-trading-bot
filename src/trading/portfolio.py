"""Portfolio management and tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .signal_generator import TradingSignal
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Position:
    """Open position in a market."""

    market_id: str
    side: str  # YES or NO
    entry_price: float
    size: float
    entry_time: datetime
    current_price: Optional[float] = None
    unrealized_pnl: float = 0.0

    def update_pnl(self, current_price: float) -> None:
        """Update unrealized P&L based on current price."""
        self.current_price = current_price

        if self.side == "YES":
            # Profit if price goes up
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:
            # Profit if price goes down (NO side)
            no_entry_price = 1.0 - self.entry_price
            no_current_price = 1.0 - current_price
            self.unrealized_pnl = (no_current_price - no_entry_price) * self.size


@dataclass
class Trade:
    """Completed trade."""

    market_id: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    entry_time: datetime
    exit_time: datetime
    fees: float = 0.0


@dataclass
class Portfolio:
    """Portfolio state and management."""

    initial_capital: float
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    realized_pnl: float = 0.0

    def __post_init__(self):
        """Initialize cash to initial capital."""
        self.cash = self.initial_capital

    @property
    def total_exposure(self) -> float:
        """Calculate total exposure across all positions."""
        return sum(pos.size for pos in self.positions.values())

    @property
    def unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    @property
    def total_value(self) -> float:
        """Calculate total portfolio value."""
        return self.cash + self.total_exposure + self.unrealized_pnl

    @property
    def total_pnl(self) -> float:
        """Calculate total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    def add_position(self, signal: TradingSignal, size: float, current_price: float) -> Position:
        """
        Add a new position.

        Args:
            signal: Trading signal
            size: Position size
            current_price: Current market price

        Returns:
            Position object
        """
        if self.cash < size:
            raise ValueError(f"Insufficient cash: {self.cash} < {size}")

        # Deduct cash
        self.cash -= size

        # Create position
        position = Position(
            market_id=signal.market_id,
            side=signal.side,
            entry_price=current_price,
            size=size,
            entry_time=datetime.utcnow(),
        )
        position.update_pnl(current_price)

        self.positions[signal.market_id] = position

        logger.info(
            "Position opened",
            market_id=signal.market_id,
            side=signal.side,
            size=size,
            entry_price=current_price,
        )

        return position

    def close_position(self, market_id: str, exit_price: float, fees: float = 0.02) -> Optional[Trade]:
        """
        Close a position.

        Args:
            market_id: Market ID
            exit_price: Exit price
            fees: Trading fees (as fraction, e.g., 0.02 = 2%)

        Returns:
            Trade object if position was closed, None otherwise
        """
        if market_id not in self.positions:
            logger.warning("Position not found", market_id=market_id)
            return None

        position = self.positions[market_id]
        position.update_pnl(exit_price)

        # Calculate P&L
        pnl = position.unrealized_pnl

        # Apply fees (only on winning trades)
        if pnl > 0:
            pnl *= 1.0 - fees

        # Return cash (original size + P&L)
        self.cash += position.size + pnl
        self.realized_pnl += pnl

        # Create trade record
        trade = Trade(
            market_id=market_id,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            size=position.size,
            pnl=pnl,
            entry_time=position.entry_time,
            exit_time=datetime.utcnow(),
            fees=fees * position.size if pnl > 0 else 0.0,
        )

        self.trades.append(trade)

        # Remove position
        del self.positions[market_id]

        logger.info(
            "Position closed",
            market_id=market_id,
            pnl=pnl,
            exit_price=exit_price,
        )

        return trade

    def update_positions(self, market_prices: Dict[str, float]) -> None:
        """
        Update all positions with current prices.

        Args:
            market_prices: Dictionary of market_id to current price
        """
        for market_id, position in self.positions.items():
            if market_id in market_prices:
                position.update_pnl(market_prices[market_id])

    def get_position(self, market_id: str) -> Optional[Position]:
        """Get position for a market."""
        return self.positions.get(market_id)


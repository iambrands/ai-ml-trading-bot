"""Automatic processing of predictions into signals, trades, and portfolio updates."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, desc

from ..database.connection import get_db
from ..database.models import Prediction, Signal, Trade, PortfolioSnapshot
from ..data.models import Market
from ..models.ensemble import EnsemblePrediction
from ..trading.signal_generator import SignalGenerator
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AutoProcessor:
    """Automatically process predictions into signals, trades, and portfolio updates."""

    def __init__(self, auto_signals: bool = True, auto_trades: bool = False):
        """
        Initialize auto processor.

        Args:
            auto_signals: Automatically generate signals from predictions
            auto_trades: Automatically create trades from signals
        """
        self.auto_signals = auto_signals
        self.auto_trades = auto_trades
        self.signal_generator = SignalGenerator() if auto_signals else None

    async def process_prediction(
        self, market: Market, prediction: EnsemblePrediction, db_prediction: Prediction, db
    ) -> tuple[int, int]:
        """
        Process a prediction: generate signal and optionally create trade.

        Args:
            market: Market object
            prediction: EnsemblePrediction object
            db_prediction: Database Prediction object
            db: Database session

        Returns:
            Tuple of (signals_created, trades_created)
        """
        signals_created = 0
        trades_created = 0

        if not self.auto_signals or not self.signal_generator:
            return signals_created, trades_created

        try:
            # Generate signal
            signal = self.signal_generator.generate_signal(market, prediction)
            if signal:
                # Check if signal already exists for this prediction
                result = await db.execute(
                    select(Signal).where(Signal.prediction_id == db_prediction.id)
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    db_signal = Signal(
                        prediction_id=db_prediction.id,
                        market_id=signal.market_id,
                        side=signal.side,
                        signal_strength=signal.signal_strength,
                        suggested_size=Decimal(str(signal.suggested_size)) if signal.suggested_size else None,
                        executed=False,
                    )
                    db.add(db_signal)
                    await db.commit()
                    await db.refresh(db_signal)
                    signals_created = 1
                    logger.debug("Signal auto-generated", market_id=market.id[:20], side=signal.side)

                    # Auto-create trade if enabled
                    if self.auto_trades:
                        try:
                            db_trade = Trade(
                                signal_id=db_signal.id,
                                market_id=signal.market_id,
                                side=signal.side,
                                entry_price=Decimal(str(market.yes_price)),
                                size=Decimal(str(signal.suggested_size)) if signal.suggested_size else Decimal("100.0"),
                                exit_price=None,
                                pnl=None,
                                status="OPEN",
                                entry_time=datetime.now(timezone.utc).replace(tzinfo=None),
                                exit_time=None,
                            )
                            db.add(db_trade)
                            await db.commit()
                            trades_created = 1
                            logger.debug("Trade auto-created", market_id=market.id[:20])
                        except Exception as e:
                            logger.warning("Failed to auto-create trade", market_id=market.id, error=str(e))
                            await db.rollback()

        except Exception as e:
            logger.warning("Failed to process prediction", market_id=market.id, error=str(e))
            await db.rollback()

        return signals_created, trades_created

    async def update_portfolio_snapshot(self, db) -> None:
        """Update or create portfolio snapshot based on current trades."""
        try:
            # Get current trades
            result = await db.execute(select(Trade).where(Trade.status == "OPEN"))
            open_trades = result.scalars().all()

            # Calculate portfolio metrics
            total_exposure = sum(float(trade.size) for trade in open_trades)
            positions_value = total_exposure  # Simplified

            # Calculate P&L
            total_pnl = sum(float(trade.pnl) for trade in open_trades if trade.pnl is not None)

            # Get latest snapshot or create new one
            result = await db.execute(
                select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.snapshot_time)).limit(1)
            )
            latest = result.scalar_one_or_none()

            base_value = Decimal("10000.00")  # Starting capital
            current_cash = base_value - Decimal(str(total_exposure))

            if latest:
                # Update existing snapshot
                latest.total_value = current_cash + Decimal(str(positions_value))
                latest.cash = current_cash
                latest.total_exposure = Decimal(str(total_exposure))
                latest.positions_value = Decimal(str(positions_value))
                latest.unrealized_pnl = Decimal(str(total_pnl))
                latest.snapshot_time = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                # Create new snapshot
                snapshot = PortfolioSnapshot(
                    total_value=current_cash + Decimal(str(positions_value)),
                    cash=current_cash,
                    positions_value=Decimal(str(positions_value)),
                    total_exposure=Decimal(str(total_exposure)),
                    daily_pnl=Decimal("0.00"),
                    unrealized_pnl=Decimal(str(total_pnl)),
                    realized_pnl=Decimal("0.00"),
                    snapshot_time=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                db.add(snapshot)

            await db.commit()
            logger.debug("Portfolio snapshot updated")
        except Exception as e:
            logger.warning("Failed to update portfolio snapshot", error=str(e))
            await db.rollback()



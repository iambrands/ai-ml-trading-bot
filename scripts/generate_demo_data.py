#!/usr/bin/env python3
"""Generate demo data for Signals, Trades, and Portfolio tabs."""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models import Signal, Trade, PortfolioSnapshot, Prediction
from sqlalchemy import select, func, desc
from src.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def generate_demo_signals():
    """Generate demo signals from existing predictions."""
    async for db in get_db():
        try:
            # Get predictions that don't have signals
            result = await db.execute(
                select(Prediction)
                .where(~Prediction.id.in_(
                    select(Signal.prediction_id).where(Signal.prediction_id.isnot(None))
                ))
                .order_by(desc(Prediction.edge))
                .limit(10)
            )
            predictions = result.scalars().all()
            
            signals_created = 0
            for pred in predictions:
                # Only create signals for predictions with positive edge
                if pred.edge > 0.05:  # 5% minimum edge
                    side = "YES" if pred.model_probability > pred.market_price else "NO"
                    strength = "STRONG" if abs(pred.edge) > 0.20 else "MEDIUM" if abs(pred.edge) > 0.10 else "WEAK"
                    
                    db_signal = Signal(
                        prediction_id=pred.id,
                        market_id=pred.market_id,
                        side=side,
                        signal_strength=strength,
                        suggested_size=Decimal("100.0"),
                        executed=False,
                    )
                    
                    db.add(db_signal)
                    signals_created += 1
            
            await db.commit()
            logger.info("Demo signals created", count=signals_created)
            break
        except Exception as e:
            logger.error("Error creating demo signals", error=str(e))
            await db.rollback()
            break


async def generate_demo_trades():
    """Generate demo trades from existing signals."""
    async for db in get_db():
        try:
            # Get signals that don't have trades
            result = await db.execute(
                select(Signal)
                .where(~Signal.id.in_(
                    select(Trade.signal_id).where(Trade.signal_id.isnot(None))
                ))
                .where(Signal.executed == False)
                .limit(5)
            )
            signals = result.scalars().all()
            
            trades_created = 0
            for signal in signals:
                # Create an OPEN trade
                db_trade = Trade(
                    signal_id=signal.id,
                    market_id=signal.market_id,
                    side=signal.side,
                    entry_price=Decimal("0.50"),  # Demo entry price
                    size=signal.suggested_size or Decimal("100.0"),
                    exit_price=None,
                    pnl=None,
                    status="OPEN",
                    entry_time=datetime.now(timezone.utc).replace(tzinfo=None),
                    exit_time=None,
                )
                
                db.add(db_trade)
                trades_created += 1
            
            await db.commit()
            logger.info("Demo trades created", count=trades_created)
            break
        except Exception as e:
            logger.error("Error creating demo trades", error=str(e))
            await db.rollback()
            break


async def generate_demo_portfolio():
    """Generate demo portfolio snapshot."""
    async for db in get_db():
        try:
            # Check if portfolio snapshot exists
            result = await db.execute(select(func.count(PortfolioSnapshot.id)))
            count = result.scalar()
            
            if count == 0:
                # Create initial portfolio snapshot
                snapshot = PortfolioSnapshot(
                    total_value=Decimal("10000.00"),
                    cash=Decimal("9500.00"),
                    positions_value=Decimal("500.00"),
                    total_exposure=Decimal("500.00"),
                    daily_pnl=Decimal("25.30"),
                    unrealized_pnl=Decimal("125.50"),
                    realized_pnl=Decimal("0.00"),
                    snapshot_time=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                
                db.add(snapshot)
                await db.commit()
                logger.info("Demo portfolio snapshot created")
            else:
                logger.info("Portfolio snapshot already exists")
            break
        except Exception as e:
            logger.error("Error creating demo portfolio", error=str(e))
            await db.rollback()
            break


async def main():
    """Generate all demo data."""
    configure_logging()
    
    logger.info("Generating demo data for UI tabs...")
    
    await generate_demo_signals()
    await generate_demo_trades()
    await generate_demo_portfolio()
    
    logger.info("Demo data generation complete!")


if __name__ == "__main__":
    asyncio.run(main())


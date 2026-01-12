"""Create trades from existing signals that don't have trades yet."""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select
from src.database.connection import AsyncSessionLocal
from src.database.models import Signal, Trade, Market as DBMarket, Prediction
from src.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def create_trades_from_signals():
    """Create trades from signals that don't have associated trades yet."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all signals that don't have trades yet
            result = await db.execute(
                select(Signal)
                .where(Signal.executed == False)
                .where(~Signal.id.in_(
                    select(Trade.signal_id).where(Trade.signal_id.isnot(None))
                ))
            )
            signals = result.scalars().all()
            
            logger.info(f"Found {len(signals)} signals without trades")
            
            if not signals:
                logger.info("No signals need trades created")
                return
            
            trades_created = 0
            for signal in signals:
                try:
                    # Get the prediction to get market price
                    pred_result = await db.execute(
                        select(Prediction).where(Prediction.id == signal.prediction_id)
                    )
                    prediction = pred_result.scalar_one_or_none()
                    
                    if not prediction:
                        logger.warning(f"Prediction not found for signal {signal.id}")
                        continue
                    
                    # Get market to get current price
                    market_result = await db.execute(
                        select(DBMarket).where(DBMarket.market_id == signal.market_id)
                    )
                    market = market_result.scalar_one_or_none()
                    
                    if not market:
                        logger.warning(f"Market not found for signal {signal.id}")
                        continue
                    
                    # Use prediction's market_price as entry price
                    entry_price = Decimal(str(prediction.market_price))
                    
                    # Use suggested_size or default
                    size = signal.suggested_size if signal.suggested_size else Decimal("100.0")
                    
                    # Create trade
                    trade = Trade(
                        signal_id=signal.id,
                        market_id=signal.market_id,
                        side=signal.side,
                        entry_price=entry_price,
                        size=size,
                        exit_price=None,
                        pnl=None,
                        status="OPEN",
                        paper_trading=False,  # Real trade
                        entry_time=datetime.now(timezone.utc).replace(tzinfo=None),
                        exit_time=None,
                    )
                    
                    db.add(trade)
                    await db.commit()
                    await db.refresh(trade)
                    
                    trades_created += 1
                    logger.info(
                        f"Created trade {trade.id} from signal {signal.id}",
                        market_id=signal.market_id[:20],
                        side=signal.side,
                        size=float(size),
                        entry_price=float(entry_price),
                    )
                except Exception as e:
                    logger.error(f"Failed to create trade from signal {signal.id}", error=str(e))
                    await db.rollback()
                    continue
            
            logger.info(f"Successfully created {trades_created} trades from {len(signals)} signals")
            
        except Exception as e:
            logger.error("Failed to create trades from signals", error=str(e))
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_trades_from_signals())


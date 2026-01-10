#!/usr/bin/env python3
"""Generate trading signals from existing predictions and save to database."""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings
from src.database.connection import get_db
from src.database.models import Prediction, Signal, Market as DBMarket
from src.trading.signal_generator import SignalGenerator
from src.models.ensemble import EnsemblePrediction
from sqlalchemy import select, desc
from src.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def generate_signals_from_predictions():
    """Generate signals from existing predictions."""
    configure_logging()
    
    logger.info("Starting signal generation from predictions")
    
    # Initialize signal generator
    signal_generator = SignalGenerator()
    
    signals_created = 0
    
    async for db in get_db():
        try:
            # Get all predictions that don't have signals yet
            result = await db.execute(
                select(Prediction)
                .where(~Prediction.id.in_(
                    select(Signal.prediction_id).where(Signal.prediction_id.isnot(None))
                ))
                .order_by(desc(Prediction.prediction_time))
            )
            predictions = result.scalars().all()
            
            logger.info("Found predictions without signals", count=len(predictions))
            
            if not predictions:
                logger.info("No predictions found to generate signals from")
                break
            
            for pred in predictions:
                try:
                    # Get market
                    result = await db.execute(
                        select(DBMarket).where(DBMarket.market_id == pred.market_id)
                    )
                    db_market = result.scalar_one_or_none()
                    
                    if not db_market:
                        logger.warning("Market not found for prediction", market_id=pred.market_id)
                        continue
                    
                    # Create a Market object for signal generator
                    from src.data.models import Market
                    market = Market(
                        id=db_market.market_id,
                        condition_id=db_market.condition_id,
                        question=db_market.question,
                        category=db_market.category,
                        resolution_date=db_market.resolution_date,
                        outcome=db_market.outcome,
                        yes_price=float(pred.market_price),
                        no_price=1.0 - float(pred.market_price),
                    )
                    
                    # Create EnsemblePrediction from database prediction
                    model_predictions = pred.model_predictions if pred.model_predictions else {}
                    ensemble_pred = EnsemblePrediction(
                        probability=float(pred.model_probability),
                        confidence=float(pred.confidence),
                        model_predictions=model_predictions,
                    )
                    
                    # Generate signal
                    signal = signal_generator.generate_signal(market, ensemble_pred)
                    
                    if signal:
                        # Save signal to database
                        db_signal = Signal(
                            prediction_id=pred.id,
                            market_id=signal.market_id,
                            side=signal.side,
                            signal_strength=signal.signal_strength,
                            suggested_size=float(signal.suggested_size) if signal.suggested_size else None,
                            executed=False,
                        )
                        
                        db.add(db_signal)
                        await db.commit()
                        signals_created += 1
                        
                        logger.info(
                            "Signal created",
                            market_id=signal.market_id[:20],
                            side=signal.side,
                            strength=signal.signal_strength,
                            edge=signal.edge,
                        )
                    else:
                        logger.debug("No signal generated", market_id=market.id, edge=pred.edge)
                        
                except Exception as e:
                    logger.error("Failed to generate signal", prediction_id=pred.id, error=str(e))
                    await db.rollback()
                    continue
            
            logger.info("Signal generation complete", signals_created=signals_created)
            break
            
        except Exception as e:
            logger.error("Database error", error=str(e))
            break


if __name__ == "__main__":
    asyncio.run(generate_signals_from_predictions())


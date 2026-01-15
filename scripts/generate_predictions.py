#!/usr/bin/env python3
"""Generate predictions for active markets and save to database."""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings
from src.data.sources.aggregator import DataAggregator
from src.data.sources.polymarket import PolymarketDataSource
from src.features.pipeline import FeaturePipeline
from src.models.ensemble import EnsembleModel, EnsemblePrediction
from src.models.xgboost_model import XGBoostProbabilityModel
from src.models.lightgbm_model import LightGBMProbabilityModel
from src.database.connection import AsyncSessionLocal, get_db
from src.database.models import Market as DBMarket, Prediction, Signal, Trade, PortfolioSnapshot
from src.trading.signal_generator import SignalGenerator
from src.utils.logging import configure_logging, get_logger
from src.utils.async_utils import batch_process
from sqlalchemy import select, func, desc
from decimal import Decimal

logger = get_logger(__name__)


async def load_models():
    """Load trained models."""
    # Get absolute path relative to project root
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "data" / "models"
    
    logger.info("Loading models...", models_dir=str(models_dir))
    
    # Check if models directory exists
    if not models_dir.exists():
        logger.error("Models directory not found", path=str(models_dir))
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    
    # Check if model files exist
    xgb_path = models_dir / "xgboost_model.pkl"
    if not xgb_path.exists():
        logger.error("XGBoost model file not found", path=str(xgb_path))
        logger.debug("Available files in models directory", files=list(models_dir.glob("*")))
        raise FileNotFoundError(f"XGBoost model not found: {xgb_path}")
    
    # Load XGBoost
    xgb_model = XGBoostProbabilityModel()
    xgb_model.load(str(xgb_path))
    logger.info("XGBoost model loaded", path=str(xgb_path))
    
    # Load LightGBM (if available and working)
    models = {"xgboost": xgb_model}
    try:
        lgb_path = models_dir / "lightgbm_model.pkl"
        lgb_model = LightGBMProbabilityModel()
        lgb_model.load(str(lgb_path))
        models["lightgbm"] = lgb_model
        logger.info("LightGBM model loaded", path=str(lgb_path))
    except Exception as e:
        logger.warning("LightGBM model not available, using XGBoost only", error=str(e))
    
    # Create ensemble
    ensemble = EnsembleModel(models=models)
    logger.info("Ensemble model created", model_count=len(models))
    
    return ensemble


async def save_market_to_db(market, db):
    """Save or update market in database."""
    from sqlalchemy import select
    
    # Check if market exists
    result = await db.execute(select(DBMarket).where(DBMarket.market_id == market.id))
    db_market = result.scalar_one_or_none()
    
    if not db_market:
        # Convert timezone-aware datetime to naive for database
        resolution_date = None
        if market.resolution_date:
            if market.resolution_date.tzinfo is not None:
                resolution_date = market.resolution_date.replace(tzinfo=None)
            else:
                resolution_date = market.resolution_date
        
        db_market = DBMarket(
            market_id=market.id,
            condition_id=market.condition_id,
            question=market.question,
            category=market.category,
            resolution_date=resolution_date,
            outcome=market.outcome,
        )
        db.add(db_market)
        try:
            await db.commit()
            await db.refresh(db_market)
            logger.debug("Market saved to database", market_id=market.id)
        except Exception as e:
            await db.rollback()
            logger.error("Failed to save market", market_id=market.id, error=str(e))
            raise
    
    return db_market


async def save_prediction_to_db(market, prediction: EnsemblePrediction, model_predictions: dict, db, signal_generator=None, auto_create_trades=False):
    """Save prediction to database and automatically generate signal and trade."""
    market_prob = float(market.yes_price)
    model_prob = prediction.probability
    edge = model_prob - market_prob
    
    # Convert timezone-aware datetime to naive for database
    prediction_time = datetime.now(timezone.utc)
    if prediction_time.tzinfo is not None:
        prediction_time = prediction_time.replace(tzinfo=None)
    
    db_prediction = Prediction(
        market_id=market.id,
        prediction_time=prediction_time,
        model_probability=model_prob,
        market_price=market_prob,
        edge=edge,
        confidence=prediction.confidence,
        model_version="v1.0",
        model_predictions=model_predictions,
    )
    
    db.add(db_prediction)
    try:
        await db.commit()
        await db.refresh(db_prediction)
        logger.info(
            "Prediction saved",
            market_id=market.id,
            model_prob=model_prob,
            market_price=market_prob,
            edge=edge,
        )
        
        # Automatically generate signal if generator provided and edge is significant
        if signal_generator and abs(edge) > 0.05:  # 5% minimum edge
            try:
                signal = signal_generator.generate_signal(market, prediction)
                if signal:
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
                    logger.info(
                        "Signal auto-generated",
                        market_id=signal.market_id[:20],
                        side=signal.side,
                        strength=signal.signal_strength,
                    )
                    
                    # Send alerts for new signal
                    try:
                        from ...services.alert_service import AlertService
                        alert_service = AlertService(db)
                        await alert_service.check_and_send_alerts(db_signal)
                    except Exception as e:
                        logger.warning("Failed to send alerts", signal_id=db_signal.id, error=str(e))
                        # Don't fail if alerts fail
                    
                    # Auto-create trade if enabled
                    if auto_create_trades:
                        try:
                            # Check if paper trading mode is enabled
                            from ...config.settings import get_settings
                            settings = get_settings()
                            paper_trading = settings.paper_trading_mode
                            
                            db_trade = Trade(
                                signal_id=db_signal.id,
                                market_id=signal.market_id,
                                side=signal.side,
                                entry_price=Decimal(str(market.yes_price)),
                                size=Decimal(str(signal.suggested_size)) if signal.suggested_size else Decimal("100.0"),
                                exit_price=None,
                                pnl=None,
                                status="OPEN",
                                paper_trading=paper_trading,  # Use setting for demo/real trading
                                entry_time=datetime.now(timezone.utc).replace(tzinfo=None),
                                exit_time=None,
                            )
                            db.add(db_trade)
                            await db.commit()
                            logger.debug("Trade auto-created", market_id=market.id[:20])
                        except Exception as e:
                            logger.warning("Failed to auto-create trade", market_id=market.id, error=str(e))
                            await db.rollback()
            except Exception as e:
                logger.warning("Failed to auto-generate signal", market_id=market.id, error=str(e))
                # Don't fail the whole process if signal generation fails
        
    except Exception as e:
        await db.rollback()
        logger.error("Failed to save prediction", market_id=market.id, error=str(e))
        raise


async def generate_predictions(limit: int = 10, auto_generate_signals: bool = True, auto_create_trades: bool = False):
    """Generate predictions for active markets and save to database.
    
    Args:
        limit: Number of markets to process
        auto_generate_signals: Automatically generate signals from predictions
        auto_create_trades: Automatically create trades from signals (default: False)
    """
    configure_logging()
    
    logger.info("Starting prediction generation", limit=limit, auto_signals=auto_generate_signals)
    
    # Initialize prediction cache
    from src.caching.prediction_cache import get_prediction_cache
    cache = get_prediction_cache()
    
    # Load models
    ensemble = await load_models()
    
    # Initialize signal generator if needed
    signal_generator = SignalGenerator() if auto_generate_signals else None
    
    # Initialize components
    settings = get_settings()
    async with PolymarketDataSource() as polymarket:
        data_aggregator = DataAggregator(polymarket=polymarket)
        feature_pipeline = FeaturePipeline()
        
        # Get active markets
        markets = await polymarket.fetch_active_markets(limit=limit)
        logger.info("Found active markets", count=len(markets))
        
        if not markets:
            logger.warning("No active markets found")
            return
        
        # Create database session directly (not using get_db() dependency)
        if not AsyncSessionLocal:
            logger.error("Database not configured - cannot generate predictions")
            return
        
        # Process markets in batches to improve performance and avoid timeouts
        # Use smaller batches to prevent database session exhaustion
        batch_size = min(5, limit)  # Process 5 markets at a time
        predictions_saved = 0
        signals_created = 0
        trades_created = 0
        cache_hits = 0
        
        async def process_single_market(market):
            """Process a single market - extracted for parallel processing."""
            # Create new database session for each market to avoid session exhaustion
            async with AsyncSessionLocal() as db:
                try:
                    # Save market to database first
                    await save_market_to_db(market, db)
                    
                    # Check cache first
                    current_price = float(market.yes_price)
                    resolution_date = market.resolution_date
                    
                    # Check if we should use cached prediction
                    should_regenerate = await cache.should_regenerate(
                        market.id, 
                        current_price,
                        resolution_date
                    )
                    
                    if not should_regenerate:
                        cached_pred = cache.get_cached(market.id)
                        if cached_pred:
                            logger.info(
                                "Using cached prediction",
                                market_id=market.id[:20],
                                cached_pred=f"{cached_pred:.2%}"
                            )
                            # Still need to save to DB for tracking, but skip expensive operations
                            # For now, we'll still generate to ensure data freshness
                    
                    # Fetch all data for market (with timeout protection)
                    import asyncio
                    try:
                        data = await asyncio.wait_for(
                            data_aggregator.fetch_all_for_market(market),
                            timeout=30.0  # 30 second timeout per market
                        )
                    except asyncio.TimeoutError:
                        logger.warning("Market data fetch timeout", market_id=market.id[:20])
                        return 0, 0, 0  # Skip this market
                    
                    # Generate features
                    features = await feature_pipeline.generate_features(market, data)
                    
                    # Get feature names
                    feature_names = feature_pipeline.get_feature_names()
                    if not feature_names:
                        feature_names = sorted(features.features.keys())
                    
                    # Get predictions from individual models
                    import numpy as np
                    X = np.array([[features.features.get(name, 0.0) for name in feature_names]])
                    
                    model_predictions = {}
                    for name, model in ensemble.models.items():
                        try:
                            pred = model.predict_proba(X)[0]
                            model_predictions[name] = float(pred)
                        except Exception as e:
                            logger.warning("Model prediction failed", model=name, error=str(e))
                            # Use XGBoost prediction as fallback if available
                            if name == "lightgbm" and "xgboost" in model_predictions:
                                model_predictions[name] = model_predictions["xgboost"]
                            else:
                                model_predictions[name] = 0.5
                    
                    # Get ensemble prediction
                    prediction = ensemble.predict_proba(market, features, feature_names)
                    
                    # Update cache with new prediction
                    cache.update_cache(market.id, prediction.probability, current_price)
                    
                    # Save prediction to database (and auto-generate signal/trade if enabled)
                    await save_prediction_to_db(market, prediction, model_predictions, db, signal_generator, auto_create_trades)
                    
                    logger.info(
                        "Prediction generated",
                        market_id=market.id[:20],
                        model_prob=f"{prediction.probability:.4f}",
                        market_price=f"{market.yes_price:.4f}",
                        edge=f"{prediction.probability - market.yes_price:.4f}",
                    )
                    
                    return 1, 1 if signal_generator else 0, 1 if auto_create_trades else 0
                    
                except Exception as e:
                    logger.error("Failed to process market", market_id=market.id, error=str(e), exc_info=True)
                    try:
                        await db.rollback()  # Rollback on error
                    except:
                        pass
                    return 0, 0, 0
        
        # Process markets in batches with controlled concurrency
        # This prevents overwhelming the database and APIs
        logger.info("Processing markets in batches", total_markets=len(markets), batch_size=batch_size, concurrency=3)
        
        results = await batch_process(
            markets,
            process_single_market,
            batch_size=batch_size,
            concurrency=3  # Process 3 markets concurrently (not all at once)
        )
        
        # Sum up results
        for pred_count, signal_count, trade_count in results:
            predictions_saved += pred_count
            signals_created += signal_count
            trades_created += trade_count
        
        # Update portfolio snapshot if we created trades (single session for this)
        if trades_created > 0:
            async with AsyncSessionLocal() as db:
                try:
                    await update_portfolio_snapshot(db)
                except Exception as e:
                    logger.warning("Failed to update portfolio snapshot", error=str(e))
        
        # Get cache stats
        cache_stats = cache.get_cache_stats()
        
        logger.info(
            "Prediction generation complete",
            predictions_saved=predictions_saved,
            signals_created=signals_created,
            trades_created=trades_created,
            cache_hits=cache_hits,
            cache_stats=cache_stats,
        )


async def update_portfolio_snapshot(db):
    """Update or create portfolio snapshot based on current trades."""
    try:
        # Get current trades
        result = await db.execute(
            select(Trade).where(Trade.status == "OPEN")
        )
        open_trades = result.scalars().all()
        
        # Calculate portfolio metrics
        total_exposure = sum(float(trade.size) for trade in open_trades)
        positions_value = total_exposure  # Simplified
        
        # Get latest snapshot or create new one
        result = await db.execute(
            select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.snapshot_time)).limit(1)
        )
        latest = result.scalar_one_or_none()
        
        if latest:
            # Update existing snapshot
            latest.total_exposure = Decimal(str(total_exposure))
            latest.positions_value = Decimal(str(positions_value))
            latest.snapshot_time = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            # Create new snapshot
            snapshot = PortfolioSnapshot(
                total_value=Decimal("10000.00"),
                cash=Decimal("10000.00") - Decimal(str(total_exposure)),
                positions_value=Decimal(str(positions_value)),
                total_exposure=Decimal(str(total_exposure)),
                daily_pnl=Decimal("0.00"),
                unrealized_pnl=Decimal("0.00"),
                realized_pnl=Decimal("0.00"),
                snapshot_time=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.add(snapshot)
        
        await db.commit()
        logger.debug("Portfolio snapshot updated")
    except Exception as e:
        logger.error("Failed to update portfolio snapshot", error=str(e))
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate predictions and save to database")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of markets to process (default: 10)",
    )
    parser.add_argument(
        "--auto-signals",
        action="store_true",
        default=True,
        help="Automatically generate signals from predictions (default: True)",
    )
    parser.add_argument(
        "--no-auto-signals",
        dest="auto_signals",
        action="store_false",
        help="Disable automatic signal generation",
    )
    parser.add_argument(
        "--auto-trades",
        action="store_true",
        default=False,
        help="Automatically create trades from signals (default: False)",
    )
    
    args = parser.parse_args()
    
    asyncio.run(generate_predictions(
        limit=args.limit,
        auto_generate_signals=args.auto_signals,
        auto_create_trades=args.auto_trades,
    ))


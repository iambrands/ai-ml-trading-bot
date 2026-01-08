"""Main orchestration for AI trading bot."""

import asyncio
from datetime import datetime

from .config.model_config import ModelConfig
from .config.settings import get_settings
from .data.sources.aggregator import DataAggregator
from .data.sources.polymarket import PolymarketDataSource
from .features.pipeline import FeaturePipeline
from .models.ensemble import EnsembleModel
from .models.xgboost_model import XGBoostProbabilityModel
from .models.lightgbm_model import LightGBMProbabilityModel
from .risk.circuit_breaker import CircuitBreaker
from .risk.limits import RiskLimits
from .trading.executor import TradeExecutor
from .trading.portfolio import Portfolio
from .trading.position_sizer import PositionSizer
from .trading.signal_generator import SignalGenerator
from .utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def main():
    """Main entry point for trading bot."""
    # Configure logging
    configure_logging()

    logger.info("Starting Polymarket AI Trading Bot")

    # Load configuration
    settings = get_settings()
    model_config = ModelConfig.from_file()

    # Initialize components
    logger.info("Initializing components")

    # Data layer
    polymarket = PolymarketDataSource(settings.polymarket_api_url)
    data_aggregator = DataAggregator(polymarket=polymarket)
    feature_pipeline = FeaturePipeline()

    # Models (would load from disk in production)
    models = {
        "xgboost": XGBoostProbabilityModel(model_config.xgboost),
        "lightgbm": LightGBMProbabilityModel(model_config.lightgbm),
        # "neural": NeuralModel(model_config.neural),  # Would implement
        # "nlp": NLPModel(model_config.nlp),  # Would implement
    }

    ensemble = EnsembleModel(models, model_config.ensemble)

    # Trading
    signal_generator = SignalGenerator()
    position_sizer = PositionSizer()
    portfolio = Portfolio(settings.initial_capital)
    executor = TradeExecutor(portfolio)

    # Risk management
    risk_limits = RiskLimits()
    circuit_breaker = CircuitBreaker()

    logger.info("Initialization complete")

    # Start background tasks
    async with polymarket:
        try:
            await run_prediction_engine(
                polymarket,
                data_aggregator,
                feature_pipeline,
                ensemble,
                signal_generator,
                position_sizer,
                portfolio,
                executor,
                risk_limits,
                circuit_breaker,
            )
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error("Fatal error", error=str(e))
            raise


async def run_prediction_engine(
    polymarket,
    data_aggregator,
    feature_pipeline,
    ensemble,
    signal_generator,
    position_sizer,
    portfolio,
    executor,
    risk_limits,
    circuit_breaker,
):
    """
    Main prediction loop.
    Run every 5 minutes for active markets.
    """
    logger.info("Starting prediction engine")

    while True:
        try:
            # Get active markets
            markets = await polymarket.fetch_active_markets(limit=50)

            logger.info("Processing markets", count=len(markets))

            for market in markets:
                try:
                    # Fetch all data for market
                    data = await data_aggregator.fetch_all_for_market(market)

                    # Generate features
                    features = await feature_pipeline.generate_features(market, data)

                    # Get feature names
                    feature_names = feature_pipeline.get_feature_names()
                    if not feature_names:
                        feature_names = sorted(features.features.keys())

                    # Set feature names in models (for feature importance)
                    for model in ensemble.models.values():
                        if hasattr(model, "feature_names"):
                            model.feature_names = feature_names

                    # Get ensemble prediction
                    prediction = ensemble.predict_proba(market, features, feature_names)

                    logger.debug(
                        "Prediction generated",
                        market_id=market.id,
                        model_prob=prediction.probability,
                        market_prob=market.yes_price,
                        edge=prediction.probability - market.yes_price,
                        confidence=prediction.confidence,
                    )

                    # Generate signal
                    signal = signal_generator.generate_signal(market, prediction)

                    if signal:
                        logger.info(
                            "Signal generated",
                            market_id=signal.market_id,
                            side=signal.side,
                            edge=signal.edge,
                            strength=signal.signal_strength,
                        )

                        # Check circuit breaker
                        if not circuit_breaker.check(portfolio):
                            logger.warning("Circuit breaker is open, skipping trade", market_id=market.id)
                            continue

                        # Calculate position size
                        size = position_sizer.calculate_position_size(
                            signal, portfolio.total_value, portfolio.total_exposure
                        )

                        # Check risk limits
                        can_open, reason = risk_limits.can_open_position(portfolio, signal, size)
                        if not can_open:
                            logger.warning("Cannot open position", market_id=market.id, reason=reason)
                            continue

                        # Execute trade
                        success = await executor.execute_signal(signal, size, market.yes_price)

                        if success:
                            logger.info(
                                "Trade executed",
                                market_id=signal.market_id,
                                side=signal.side,
                                size=size,
                            )
                        else:
                            logger.warning("Trade execution failed", market_id=signal.market_id)

                except Exception as e:
                    logger.error("Error processing market", market_id=market.id, error=str(e))
                    continue

            # Update positions with current prices
            market_prices = {m.id: m.yes_price for m in markets}
            portfolio.update_positions(market_prices)

            # Check risk limits
            risk_limits.check_daily_loss_limit(portfolio, portfolio.initial_capital)

            logger.info(
                "Prediction cycle complete",
                portfolio_value=portfolio.total_value,
                positions=len(portfolio.positions),
                total_pnl=portfolio.total_pnl,
            )

            await asyncio.sleep(300)  # 5 minutes

        except Exception as e:
            logger.error("Prediction engine error", error=str(e))
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())


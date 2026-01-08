"""Script for backtesting trading strategy."""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting.simulator import BacktestSimulator
from src.config.model_config import ModelConfig
from src.config.settings import get_settings
from src.data.sources.aggregator import DataAggregator
from src.data.sources.polymarket import PolymarketDataSource
from src.features.pipeline import FeaturePipeline
from src.models.ensemble import EnsembleModel
from src.models.lightgbm_model import LightGBMProbabilityModel
from src.models.xgboost_model import XGBoostProbabilityModel
from src.trading.position_sizer import PositionSizer
from src.trading.signal_generator import SignalGenerator
from src.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def run_backtest(start_date: datetime, end_date: datetime, initial_capital: float):
    """Run backtest simulation."""
    logger.info("Running backtest", start_date=start_date, end_date=end_date, initial_capital=initial_capital)

    settings = get_settings()
    model_config = ModelConfig.from_file()

    async with PolymarketDataSource(settings.polymarket_api_url) as polymarket:
        # Initialize components
        data_aggregator = DataAggregator(polymarket=polymarket)
        feature_pipeline = FeaturePipeline()

        # Load models (would load from disk in production)
        models = {
            "xgboost": XGBoostProbabilityModel(model_config.xgboost),
            "lightgbm": LightGBMProbabilityModel(model_config.lightgbm),
        }
        ensemble = EnsembleModel(models, model_config.ensemble)

        signal_generator = SignalGenerator()
        position_sizer = PositionSizer()

        # Create simulator
        simulator = BacktestSimulator(
            data_aggregator=data_aggregator,
            feature_pipeline=feature_pipeline,
            ensemble=ensemble,
            signal_generator=signal_generator,
            position_sizer=position_sizer,
        )

        # Run backtest
        result = await simulator.run_backtest(start_date, end_date, initial_capital)

        # Report results
        logger.info("Backtest complete")
        logger.info("Backtest metrics", **result.metrics)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run backtest")
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date for backtest (ISO format)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date for backtest (ISO format)",
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=10000.0,
        help="Initial capital",
    )

    args = parser.parse_args()

    configure_logging()

    start_date = datetime.fromisoformat(args.start_date)
    end_date = datetime.fromisoformat(args.end_date)

    await run_backtest(start_date, end_date, args.initial_capital)


if __name__ == "__main__":
    asyncio.run(main())


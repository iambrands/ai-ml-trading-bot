"""Script for training ML models."""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.model_config import ModelConfig
from src.config.settings import get_settings
from src.data.sources.aggregator import DataAggregator
from src.data.sources.polymarket import PolymarketDataSource
from src.features.pipeline import FeaturePipeline
from src.models.training.trainer import ModelTrainer
from src.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train ML models")
    parser.add_argument(
        "--start-date",
        type=str,
        default=(datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
        help="Start date for training data (ISO format)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=datetime.now(timezone.utc).isoformat(),
        help="End date for training data (ISO format)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Data directory",
    )
    parser.add_argument(
        "--time-points",
        type=int,
        nargs="+",
        default=[1, 3, 7, 14],
        help="Days before resolution to sample features",
    )

    args = parser.parse_args()

    configure_logging()

    start_date = datetime.fromisoformat(args.start_date)
    end_date = datetime.fromisoformat(args.end_date)
    data_dir = Path(args.data_dir)
    models_dir = data_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting model training", start_date=start_date, end_date=end_date)

    # Initialize components
    settings = get_settings()
    async with PolymarketDataSource(settings.polymarket_api_url) as polymarket:
        data_aggregator = DataAggregator(polymarket=polymarket)
        feature_pipeline = FeaturePipeline()

        # Create trainer
        trainer = ModelTrainer(data_aggregator, feature_pipeline)

        # Collect training data
        logger.info("Collecting training data...")
        examples = await trainer.collect_training_data(
            start_date, end_date, time_points=args.time_points
        )

        if not examples:
            logger.error("No training examples collected. Exiting.")
            return

        # Train models
        logger.info("Training models...")
        models = await trainer.train_all_models(examples, models_dir)

        logger.info("Model training complete!", models_dir=models_dir)


if __name__ == "__main__":
    asyncio.run(main())


"""Backtesting simulator for historical strategy validation."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..config.settings import get_settings
from ..data.models import Market
from ..data.sources.aggregator import DataAggregator
from ..data.sources.polymarket import PolymarketDataSource
from ..features.pipeline import FeaturePipeline
from ..models.ensemble import EnsembleModel
from ..trading.executor import TradeExecutor
from ..trading.portfolio import Portfolio
from ..trading.position_sizer import PositionSizer
from ..trading.signal_generator import SignalGenerator
from ..utils.logging import get_logger

logger = get_logger(__name__)


class BacktestSimulator:
    """Historical simulation to validate strategy performance."""

    def __init__(
        self,
        data_aggregator: DataAggregator,
        feature_pipeline: FeaturePipeline,
        ensemble: EnsembleModel,
        signal_generator: SignalGenerator,
        position_sizer: PositionSizer,
    ):
        """
        Initialize backtest simulator.

        Args:
            data_aggregator: Data aggregator instance
            feature_pipeline: Feature pipeline instance
            ensemble: Ensemble model
            signal_generator: Signal generator
            position_sizer: Position sizer
        """
        self.data_aggregator = data_aggregator
        self.feature_pipeline = feature_pipeline
        self.ensemble = ensemble
        self.signal_generator = signal_generator
        self.position_sizer = position_sizer

    async def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        time_points: Optional[List[int]] = None,
    ) -> "BacktestResult":
        """
        Run full backtest simulation.

        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_capital: Initial capital
            time_points: Days before resolution to generate predictions

        Returns:
            BacktestResult object
        """
        if time_points is None:
            time_points = [14, 7, 3, 1]

        logger.info(
            "Starting backtest",
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
        )

        # Initialize portfolio
        portfolio = Portfolio(initial_capital)
        executor = TradeExecutor(portfolio)

        # Fetch resolved markets in period
        polymarket = self.data_aggregator.polymarket
        markets = await polymarket.fetch_resolved_markets(
            start_date=start_date,
            end_date=end_date,
            limit=1000,
        )

        logger.info("Markets for backtest", count=len(markets))

        # Sort by resolution date
        markets.sort(key=lambda m: m.resolution_date or datetime.max)

        # Process each market
        for market in markets:
            if not market.resolution_date or not market.outcome:
                continue

            # Generate predictions at various time points before resolution
            for days_before in time_points:
                prediction_time = market.resolution_date - timedelta(days=days_before)

                # Skip if prediction time is outside backtest period
                if prediction_time < start_date or prediction_time > end_date:
                    continue

                # Skip if prediction time is before market creation
                if market.created_at and prediction_time < market.created_at:
                    continue

                try:
                    # Fetch data at prediction time (simulated - would need historical data)
                    data = await self.data_aggregator.fetch_all_for_market(market)

                    # Generate features
                    features = await self.feature_pipeline.generate_features(market, data)

                    # Get feature names
                    feature_names = self.feature_pipeline.get_feature_names()
                    if not feature_names:
                        feature_names = sorted(features.features.keys())

                    # Set feature names in models
                    for model in self.ensemble.models.values():
                        if hasattr(model, "feature_names"):
                            model.feature_names = feature_names

                    # Get prediction
                    prediction = self.ensemble.predict_proba(market, features, feature_names)

                    # Get historical price (use current price as approximation)
                    historical_price = market.yes_price

                    # Generate signal
                    signal = self.signal_generator.generate_signal(market, prediction)

                    if signal:
                        # Calculate position size
                        size = self.position_sizer.calculate_position_size(
                            signal, portfolio.total_value, portfolio.total_exposure
                        )

                        if size > 0:
                            # Execute trade
                            success = await executor.execute_signal(
                                signal, size, historical_price
                            )

                            if success:
                                logger.debug(
                                    "Backtest trade executed",
                                    market_id=market.id,
                                    side=signal.side,
                                    size=size,
                                    price=historical_price,
                                )

                except Exception as e:
                    logger.warning(
                        "Error in backtest iteration",
                        market_id=market.id,
                        days_before=days_before,
                        error=str(e),
                    )
                    continue

            # Close position when market resolves
            if market.resolution_date and market.outcome:
                position = portfolio.get_position(market.id)
                if position:
                    # Determine exit price based on outcome
                    exit_price = 1.0 if market.outcome == "YES" else 0.0
                    await executor.close_position(market.id, exit_price)

        # Calculate metrics
        from .metrics import calculate_metrics

        metrics = calculate_metrics(portfolio, initial_capital, start_date, end_date)

        return BacktestResult(
            portfolio=portfolio,
            metrics=metrics,
            start_date=start_date,
            end_date=end_date,
        )


@dataclass
class BacktestResult:
    """Backtest result."""

    portfolio: Portfolio
    metrics: Dict[str, float]
    start_date: datetime
    end_date: datetime


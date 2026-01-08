"""Model training pipeline with data collection."""

import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.model_selection import TimeSeriesSplit

from ...config.model_config import ModelConfig, TrainingConfig
from ...data.models import FeatureVector, Market
from ...data.sources.aggregator import DataAggregator
from ...data.sources.polymarket import PolymarketDataSource
from ...features.pipeline import FeaturePipeline
from ...utils.logging import get_logger

logger = get_logger(__name__)


class ModelTrainer:
    """Training pipeline for all models."""

    def __init__(
        self,
        data_aggregator: DataAggregator,
        feature_pipeline: FeaturePipeline,
        model_config: Optional[ModelConfig] = None,
    ):
        """
        Initialize model trainer.

        Args:
            data_aggregator: Data aggregator instance
            feature_pipeline: Feature pipeline instance
            model_config: Model configuration
        """
        self.data_aggregator = data_aggregator
        self.feature_pipeline = feature_pipeline
        self.model_config = model_config or ModelConfig.from_file()
        self.training_config = self.model_config.training

    async def collect_training_data(
        self,
        start_date: datetime,
        end_date: datetime,
        time_points: Optional[List[int]] = None,
    ) -> List[Tuple[FeatureVector, int]]:
        """
        Collect historical data for training.

        For each resolved market, sample multiple time points before resolution
        and create training examples.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            time_points: Days before resolution to sample (default: [1, 3, 7, 14])

        Returns:
            List of (FeatureVector, label) tuples where label is 1 for YES, 0 for NO
        """
        if time_points is None:
            time_points = [1, 3, 7, 14]

        logger.info("Collecting training data", start_date=start_date, end_date=end_date)

        # Fetch resolved markets
        polymarket = self.data_aggregator.polymarket
        markets = await polymarket.fetch_resolved_markets(
            start_date=start_date,
            end_date=end_date,
            limit=1000,
        )

        logger.info("Found resolved markets", count=len(markets))

        if not markets:
            logger.warning(
                "No resolved markets found. "
                "This could be due to: "
                "1) API authentication issues (403 Forbidden), "
                "2) No markets resolved in the specified date range, "
                "3) API endpoint changes. "
                "Consider checking your API credentials or using a different date range."
            )
            return []

        training_examples = []

        for market in markets:
            if not market.outcome or not market.resolution_date:
                continue

            # Label: 1 for YES, 0 for NO
            label = 1 if market.outcome == "YES" else 0

            # Sample features at various time points before resolution
            for days_before in time_points:
                sample_time = market.resolution_date - timedelta(days=days_before)

                # Skip if sample time is before market creation
                if market.created_at and sample_time < market.created_at:
                    continue

                try:
                    # Fetch data at this time point (simulated - would need historical data API)
                    # For now, we'll use current data as approximation
                    data = await self.data_aggregator.fetch_all_for_market(market)

                    # Generate features
                    features = await self.feature_pipeline.generate_features(market, data)

                    # Store with label
                    training_examples.append((features, label))

                    logger.debug(
                        "Created training example",
                        market_id=market.id,
                        days_before=days_before,
                        label=label,
                    )

                except Exception as e:
                    logger.warning(
                        "Failed to create training example",
                        market_id=market.id,
                        days_before=days_before,
                        error=str(e),
                    )
                    continue

        logger.info("Collected training examples", count=len(training_examples))
        return training_examples

    def prepare_features(
        self, examples: List[Tuple[FeatureVector, int]], feature_names: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features for training.

        Args:
            examples: List of (FeatureVector, label) tuples
            feature_names: Optional list of feature names (will be extracted if None)

        Returns:
            Tuple of (X, y) where X is feature matrix and y is labels
        """
        if not examples:
            raise ValueError("No training examples provided")

        # Extract feature names from first example
        if feature_names is None:
            feature_names = sorted(examples[0][0].features.keys())
            logger.info("Extracted feature names", count=len(feature_names), features=feature_names)

        # Build feature matrix
        X = np.array([ex[0].to_array(feature_names) for ex in examples])
        y = np.array([ex[1] for ex in examples])

        logger.info("Prepared features", n_samples=X.shape[0], n_features=X.shape[1])

        return X, y, feature_names

    def train_with_time_series_cv(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_class,
        model_config,
        feature_names: List[str],
    ) -> Tuple:
        """
        Train model with time-series cross-validation.

        Args:
            X: Feature matrix
            y: Labels
            model_class: Model class to instantiate
            model_config: Model configuration
            feature_names: List of feature names

        Returns:
            Tuple of (trained_model, cv_scores)
        """
        tscv = TimeSeriesSplit(n_splits=self.training_config.time_series_splits)
        scores = []

        logger.info("Starting time-series cross-validation", n_splits=self.training_config.time_series_splits)

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            logger.info(
                "Training fold",
                fold=fold + 1,
                train_size=len(X_train),
                test_size=len(X_test),
            )

            # Create and train model
            model = model_class(model_config)
            model.feature_names = feature_names

            # Sample weights for recency (more recent = higher weight)
            sample_weights = self._calculate_sample_weights(len(X_train))

            model.train(
                X_train,
                y_train,
                eval_set=(X_test, y_test),
                sample_weights=sample_weights,
            )

            # Evaluate
            metrics = model.evaluate(X_test, y_test)
            scores.append(metrics)

            logger.info("Fold metrics", fold=fold + 1, **metrics)

        # Train final model on all data
        logger.info("Training final model on all data")
        final_model = model_class(model_config)
        final_model.feature_names = feature_names
        sample_weights = self._calculate_sample_weights(len(X))
        final_model.train(X, y, sample_weights=sample_weights)

        return final_model, scores

    def _calculate_sample_weights(self, n_samples: int) -> np.ndarray:
        """
        Calculate sample weights with recency decay.

        Args:
            n_samples: Number of samples

        Returns:
            Array of sample weights
        """
        # More recent samples get higher weight
        weights = np.array(
            [
                self.training_config.sample_weight_decay ** (n_samples - i - 1)
                for i in range(n_samples)
            ]
        )
        # Normalize
        weights = weights / weights.sum() * n_samples
        return weights

    async def train_all_models(
        self, examples: List[Tuple[FeatureVector, int]], save_dir: Path
    ) -> Dict[str, any]:
        """
        Train all models and save them.

        Args:
            examples: Training examples
            save_dir: Directory to save models

        Returns:
            Dictionary of model name to trained model
        """
        save_dir.mkdir(parents=True, exist_ok=True)

        # Prepare features
        X, y, feature_names = self.prepare_features(examples)

        # Check minimum samples
        if len(X) < self.training_config.min_samples_per_split:
            raise ValueError(
                f"Not enough samples: {len(X)} < {self.training_config.min_samples_per_split}"
            )

        models = {}

        # Train XGBoost
        logger.info("Training XGBoost model")
        from ..xgboost_model import XGBoostProbabilityModel

        xgb_model, xgb_scores = self.train_with_time_series_cv(
            X, y, XGBoostProbabilityModel, self.model_config.xgboost, feature_names
        )
        xgb_model.save(str(save_dir / "xgboost.model"))
        models["xgboost"] = xgb_model
        logger.info("XGBoost training complete", avg_accuracy=np.mean([s["accuracy"] for s in xgb_scores]))

        # Train LightGBM
        logger.info("Training LightGBM model")
        from ..lightgbm_model import LightGBMProbabilityModel

        lgb_model, lgb_scores = self.train_with_time_series_cv(
            X, y, LightGBMProbabilityModel, self.model_config.lightgbm, feature_names
        )
        lgb_model.save(str(save_dir / "lightgbm.model"))
        models["lightgbm"] = lgb_model
        logger.info("LightGBM training complete", avg_accuracy=np.mean([s["accuracy"] for s in lgb_scores]))

        # Save feature names
        with open(save_dir / "feature_names.pkl", "wb") as f:
            pickle.dump(feature_names, f)

        logger.info("All models trained and saved", save_dir=save_dir)

        return models


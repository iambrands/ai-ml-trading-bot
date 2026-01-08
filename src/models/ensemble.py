"""Ensemble model combining multiple models."""

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

from ..data.models import FeatureVector, Market
from .base import BaseModel
from ..config.model_config import EnsembleConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EnsemblePrediction:
    """Ensemble prediction result."""

    probability: float  # Ensemble probability (0 to 1)
    confidence: float  # Confidence in prediction (0 to 1)
    model_predictions: Dict[str, float]  # Individual model predictions
    feature_importances: Optional[Dict[str, float]] = None


class EnsembleModel:
    """Ensemble that combines multiple models for robust predictions."""

    def __init__(
        self,
        models: Dict[str, BaseModel],
        config: Optional[EnsembleConfig] = None,
    ):
        """
        Initialize ensemble model.

        Args:
            models: Dictionary of model name to model instance
            config: Ensemble configuration
        """
        self.models = models
        self.config = config or EnsembleConfig()
        self.weights = self.config.weights.copy()
        self.recent_accuracy: Dict[str, float] = {name: 0.5 for name in models}

    def predict_proba(self, market: Market, features: FeatureVector, feature_names: list) -> EnsemblePrediction:
        """
        Generate ensemble prediction with confidence estimation.

        Args:
            market: Market object
            features: FeatureVector object
            feature_names: List of feature names for model input

        Returns:
            EnsemblePrediction object
        """
        predictions = {}

        # Convert features to array
        X = np.array([[features.features.get(name, 0.0) for name in feature_names]])

        # Get predictions from each model
        for name, model in self.models.items():
            try:
                pred = model.predict_proba(X)[0]  # Get single prediction
                predictions[name] = float(pred)
            except Exception as e:
                logger.warning("Model prediction failed", model=name, error=str(e))
                # Use default prediction if model fails
                predictions[name] = 0.5

        # Calculate weighted average
        ensemble_prob = sum(
            predictions[name] * self.weights.get(name, 0.0) for name in self.models.keys() if name in self.weights
        )

        # Normalize weights (ensure they sum to 1)
        total_weight = sum(self.weights.get(name, 0.0) for name in self.models.keys() if name in self.weights)
        if total_weight > 0:
            ensemble_prob /= total_weight

        # Confidence from model agreement (variance)
        pred_values = list(predictions.values())
        variance = float(np.var(pred_values))
        # Lower variance = higher confidence
        agreement_confidence = max(0.0, 1.0 - min(variance * 10, 1.0))

        # Combine with historical accuracy if available
        avg_accuracy = np.mean([self.recent_accuracy.get(name, 0.5) for name in self.models.keys()])
        combined_confidence = (agreement_confidence + avg_accuracy) / 2.0

        return EnsemblePrediction(
            probability=float(ensemble_prob),
            confidence=float(combined_confidence),
            model_predictions=predictions,
        )

    def update_weights(self, recent_performance: Dict[str, float]) -> None:
        """
        Dynamically adjust weights based on recent accuracy.

        Args:
            recent_performance: Dictionary of model name to recent accuracy
        """
        if not self.config.dynamic_weighting:
            return

        # Update recent accuracy tracking
        self.recent_accuracy.update(recent_performance)

        # Normalize performance scores
        total = sum(self.recent_accuracy.values())
        if total > 0:
            # Calculate new weights based on performance
            new_weights = {
                name: max(
                    self.config.min_weight,
                    min(self.config.max_weight, self.recent_accuracy[name] / total),
                )
                for name in self.models.keys()
            }

            # Renormalize to sum to 1
            total_weight = sum(new_weights.values())
            if total_weight > 0:
                self.weights = {name: w / total_weight for name, w in new_weights.items()}

        logger.info("Updated ensemble weights", weights=self.weights)


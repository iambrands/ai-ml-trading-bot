"""Base model abstract class."""

from abc import ABC, abstractmethod
from typing import Dict, Optional

import numpy as np

from ..utils.logging import get_logger

logger = get_logger(__name__)


class BaseModel(ABC):
    """Abstract base class for all prediction models."""

    def __init__(self, model_name: str):
        """
        Initialize base model.

        Args:
            model_name: Name of the model
        """
        self.model_name = model_name
        self.model = None
        self.feature_names: Optional[list] = None

    @abstractmethod
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        eval_set: Optional[tuple] = None,
        sample_weights: Optional[np.ndarray] = None,
    ) -> "BaseModel":
        """
        Train the model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary labels (0/1 for NO/YES outcome)
            eval_set: Optional (X_val, y_val) for early stopping
            sample_weights: Optional sample weights

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probability of YES outcome.

        Args:
            X: Feature matrix

        Returns:
            Array of probabilities (0 to 1)
        """
        pass

    @abstractmethod
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model on test data.

        Args:
            X_test: Test feature matrix
            y_test: Test labels

        Returns:
            Dictionary of metrics
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """
        Save model to disk.

        Args:
            path: Path to save model
        """
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """
        Load model from disk.

        Args:
            path: Path to load model from
        """
        pass

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importances if available.

        Returns:
            Dictionary of feature names to importance scores, or None
        """
        return None

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        Predict binary class labels.

        Args:
            X: Feature matrix
            threshold: Probability threshold for positive class

        Returns:
            Array of binary predictions (0/1)
        """
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)



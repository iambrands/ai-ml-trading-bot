"""XGBoost model for probability prediction."""

from typing import Dict, Optional, Tuple

import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
import xgboost as xgb

from .base import BaseModel
from ..config.model_config import XGBoostConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


class XGBoostProbabilityModel(BaseModel):
    """XGBoost model for event probability prediction."""

    def __init__(self, config: Optional[XGBoostConfig] = None):
        """
        Initialize XGBoost model.

        Args:
            config: XGBoost configuration
        """
        super().__init__("xgboost")
        self.config = config or XGBoostConfig()
        self.params = {
            "objective": "binary:logistic",
            "eval_metric": ["logloss", "auc"],
            "n_estimators": self.config.n_estimators,
            "max_depth": self.config.max_depth,
            "learning_rate": self.config.learning_rate,
            "subsample": self.config.subsample,
            "colsample_bytree": self.config.colsample_bytree,
            "min_child_weight": self.config.min_child_weight,
            "reg_alpha": self.config.reg_alpha,
            "reg_lambda": self.config.reg_lambda,
            "random_state": self.config.random_state,
        }
        self.model = None
        self.feature_names = None

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        eval_set: Optional[Tuple] = None,
        sample_weights: Optional[np.ndarray] = None,
    ) -> "XGBoostProbabilityModel":
        """
        Train XGBoost model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Binary labels (0/1 for NO/YES outcome)
            eval_set: Optional (X_val, y_val) for early stopping
            sample_weights: Optional sample weights

        Returns:
            Self for method chaining
        """
        logger.info("Training XGBoost model", n_samples=X.shape[0], n_features=X.shape[1])

        fit_params = {}
        if sample_weights is not None:
            fit_params["sample_weight"] = sample_weights

        if eval_set:
            X_val, y_val = eval_set
            fit_params["eval_set"] = [(X_val, y_val)]
            fit_params["early_stopping_rounds"] = 20
            fit_params["verbose"] = False

        self.model = xgb.XGBClassifier(**self.params)
        self.model.fit(X, y, **fit_params)

        logger.info("XGBoost model training completed")
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probability of YES outcome.

        Args:
            X: Feature matrix

        Returns:
            Array of probabilities (0 to 1) for YES outcome
        """
        if self.model is None:
            raise ValueError("Model must be trained before prediction")

        proba = self.model.predict_proba(X)
        # Return probability of positive class (YES)
        return proba[:, 1]

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model on test data.

        Args:
            X_test: Test feature matrix
            y_test: Test labels

        Returns:
            Dictionary of metrics
        """
        if self.model is None:
            raise ValueError("Model must be trained before evaluation")

        y_pred_proba = self.predict_proba(X_test)
        y_pred = (y_pred_proba >= 0.5).astype(int)

        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "brier_score": float(brier_score_loss(y_test, y_pred_proba)),
            "log_loss": float(log_loss(y_test, y_pred_proba)),
            "auc_roc": float(roc_auc_score(y_test, y_pred_proba)),
        }

        return metrics

    def save(self, path: str) -> None:
        """
        Save model to disk.

        Args:
            path: Path to save model
        """
        if self.model is None:
            raise ValueError("Model must be trained before saving")

        self.model.save_model(path)
        logger.info("Saved XGBoost model", path=path)

    def load(self, path: str) -> None:
        """
        Load model from disk.

        Args:
            path: Path to load model from
        """
        self.model = xgb.XGBClassifier()
        self.model.load_model(path)
        logger.info("Loaded XGBoost model", path=path)

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importances.

        Returns:
            Dictionary of feature names to importance scores
        """
        if self.model is None or self.feature_names is None:
            return None

        importances = self.model.feature_importances_
        return dict(zip(self.feature_names, importances.tolist()))


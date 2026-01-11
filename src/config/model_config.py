"""Model configuration loaded from YAML."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml
from pathlib import Path

from .settings import get_settings


@dataclass
class XGBoostConfig:
    """XGBoost model configuration."""

    n_estimators: int = 300
    max_depth: int = 6
    learning_rate: float = 0.05
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    min_child_weight: int = 3
    reg_alpha: float = 0.1
    reg_lambda: float = 1.0
    random_state: int = 42

    @classmethod
    def from_dict(cls, data: Dict) -> "XGBoostConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class LightGBMConfig:
    """LightGBM model configuration."""

    n_estimators: int = 300
    max_depth: int = 6
    learning_rate: float = 0.05
    num_leaves: int = 31
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_alpha: float = 0.1
    reg_lambda: float = 1.0
    random_state: int = 42

    @classmethod
    def from_dict(cls, data: Dict) -> "LightGBMConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class NeuralConfig:
    """Neural network model configuration."""

    hidden_layers: List[int] = None
    dropout: float = 0.3
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 10

    def __post_init__(self):
        """Set default hidden layers if not provided."""
        if self.hidden_layers is None:
            self.hidden_layers = [128, 64, 32]

    @classmethod
    def from_dict(cls, data: Dict) -> "NeuralConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class NLPConfig:
    """NLP model configuration."""

    model_name: str = "distilbert-base-uncased"
    max_length: int = 512
    batch_size: int = 16
    learning_rate: float = 2e-5
    epochs: int = 5

    @classmethod
    def from_dict(cls, data: Dict) -> "NLPConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class EnsembleConfig:
    """Ensemble model configuration."""

    weights: Dict[str, float] = None
    dynamic_weighting: bool = True
    lookback_days: int = 30
    min_weight: float = 0.05
    max_weight: float = 0.50

    def __post_init__(self):
        """Set default weights if not provided."""
        if self.weights is None:
            self.weights = {
                "xgboost": 0.35,
                "lightgbm": 0.25,
                "neural": 0.20,
                "nlp": 0.20,
            }

    @classmethod
    def from_dict(cls, data: Dict) -> "EnsembleConfig":
        """Create from dictionary."""
        weights = data.get("weights", {})
        return cls(
            weights=weights if weights else None,
            dynamic_weighting=data.get("dynamic_weighting", True),
            lookback_days=data.get("lookback_days", 30),
            min_weight=data.get("min_weight", 0.05),
            max_weight=data.get("max_weight", 0.50),
        )


@dataclass
class TrainingConfig:
    """Training configuration."""

    time_series_splits: int = 5
    early_stopping_rounds: int = 20
    sample_weight_decay: float = 0.95
    min_samples_per_split: int = 1000

    @classmethod
    def from_dict(cls, data: Dict) -> "TrainingConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class ModelConfig:
    """Complete model configuration."""

    xgboost: XGBoostConfig
    lightgbm: LightGBMConfig
    neural: NeuralConfig
    nlp: NLPConfig
    ensemble: EnsembleConfig
    training: TrainingConfig

    @classmethod
    def from_file(cls, config_path: Optional[Path] = None) -> "ModelConfig":
        """Load configuration from YAML file."""
        if config_path is None:
            settings = get_settings()
            config_path = settings.config_dir / "model_params.yaml"

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        return cls(
            xgboost=XGBoostConfig.from_dict(data.get("xgboost", {})),
            lightgbm=LightGBMConfig.from_dict(data.get("lightgbm", {})),
            neural=NeuralConfig.from_dict(data.get("neural", {})),
            nlp=NLPConfig.from_dict(data.get("nlp", {})),
            ensemble=EnsembleConfig.from_dict(data.get("ensemble", {})),
            training=TrainingConfig.from_dict(data.get("training", {})),
        )



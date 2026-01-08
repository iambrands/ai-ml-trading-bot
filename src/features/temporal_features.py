"""Temporal feature extraction."""

from datetime import datetime, timedelta
from typing import Dict

import numpy as np

from ..data.models import Market
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TemporalFeatureExtractor:
    """Extract time-based features."""

    def extract(self, market: Market) -> Dict[str, float]:
        """
        Extract temporal features.

        Args:
            market: Market object

        Returns:
            Dictionary of feature names to values
        """
        features = {}
        now = datetime.utcnow()

        # Days to resolution
        if market.resolution_date:
            days_to_resolution = (market.resolution_date - now).total_seconds() / 86400.0
            features["days_to_resolution"] = max(0.0, float(days_to_resolution))
        else:
            features["days_to_resolution"] = 30.0  # Default assumption

        # Time of day features
        features["hour_of_day"] = float(now.hour)
        features["day_of_week"] = float(now.weekday())  # 0 = Monday, 6 = Sunday
        features["is_weekend"] = 1.0 if now.weekday() >= 5 else 0.0

        # Market age (days since creation)
        if market.created_at:
            market_age_days = (now - market.created_at).total_seconds() / 86400.0
            features["market_age_days"] = float(market_age_days)
        else:
            features["market_age_days"] = 0.0

        # Time-based cyclical features (for better model learning)
        features["hour_sin"] = np.sin(2 * np.pi * now.hour / 24.0)
        features["hour_cos"] = np.cos(2 * np.pi * now.hour / 24.0)
        features["day_sin"] = np.sin(2 * np.pi * now.weekday() / 7.0)
        features["day_cos"] = np.cos(2 * np.pi * now.weekday() / 7.0)

        # Month of year
        features["month_of_year"] = float(now.month)
        features["month_sin"] = np.sin(2 * np.pi * now.month / 12.0)
        features["month_cos"] = np.cos(2 * np.pi * now.month / 12.0)

        return features


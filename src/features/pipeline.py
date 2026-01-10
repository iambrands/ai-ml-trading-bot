"""Main feature engineering pipeline."""

from datetime import datetime, timezone
from typing import Dict, List

import numpy as np

from ..data.models import AggregatedData, FeatureVector, Market
from ..data.processors.embeddings import TextEmbedder
from ..data.processors.sentiment import SentimentAnalyzer
from .market_features import MarketFeatureExtractor
from .sentiment_features import SentimentFeatureExtractor
from .temporal_features import TemporalFeatureExtractor
from ..utils.logging import get_logger

logger = get_logger(__name__)


class FeaturePipeline:
    """Main pipeline for feature generation."""

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize feature pipeline.

        Args:
            embedding_model: Sentence transformer model name
        """
        self.market_features = MarketFeatureExtractor()
        self.sentiment_features = SentimentFeatureExtractor()
        self.temporal_features = TemporalFeatureExtractor()
        self.embedder = TextEmbedder(embedding_model)
        self._feature_names: List[str] = []

    async def generate_features(self, market: Market, data: AggregatedData) -> "FeatureVector":
        """
        Generate all features for a market.

        Args:
            market: Market object
            data: AggregatedData object

        Returns:
            FeatureVector object
        """
        features = {}

        # Market features
        market_feats = self.market_features.extract(data.market)
        features.update(market_feats)

        # Sentiment features
        sentiment_feats = self.sentiment_features.extract(data.news, data.social)
        features.update(sentiment_feats)

        # Temporal features
        temporal_feats = self.temporal_features.extract(market)
        features.update(temporal_feats)

        # Text embeddings
        embeddings = {
            "question": self.embedder.embed(market.question),
        }

        # News embeddings (aggregated)
        if data.news:
            news_texts = [f"{a.title} {a.description}" for a in data.news]
            embeddings["news"] = self.embedder.embed_aggregate(news_texts)
        else:
            embeddings["news"] = self.embedder.embed("")

        # Store feature names for later use
        if not self._feature_names:
            self._feature_names = sorted(features.keys())

        return FeatureVector(
            market_id=market.id,
            timestamp=datetime.now(timezone.utc),
            features=features,
            embeddings=embeddings,
        )

    def get_feature_names(self) -> List[str]:
        """Get list of feature names."""
        return self._feature_names if self._feature_names else sorted([])

    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize features (placeholder - would use standardization).

        Args:
            features: Raw features dictionary

        Returns:
            Normalized features dictionary
        """
        # Placeholder - would implement proper normalization/standardization
        # For now, just return as-is
        return features

    def to_feature_array(self, feature_vector: "FeatureVector", feature_names: List[str]) -> np.ndarray:
        """
        Convert FeatureVector to numpy array.

        Args:
            feature_vector: FeatureVector object
            feature_names: List of feature names to include

        Returns:
            Numpy array of features
        """
        return np.array([feature_vector.features.get(name, 0.0) for name in feature_names])


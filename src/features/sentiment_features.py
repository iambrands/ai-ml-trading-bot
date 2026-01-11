"""Sentiment feature extraction."""

import numpy as np
from typing import Dict, List, Optional

from ..data.models import NewsArticle, SocialSentiment
from ..data.processors.sentiment import SentimentAnalyzer
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SentimentFeatureExtractor:
    """Extract sentiment-based features."""

    def __init__(self, sentiment_analyzer: Optional[SentimentAnalyzer] = None):
        """
        Initialize sentiment feature extractor.

        Args:
            sentiment_analyzer: Optional sentiment analyzer instance
        """
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()

    def extract(
        self,
        news: List[NewsArticle],
        social: Optional[SocialSentiment] = None,
    ) -> Dict[str, float]:
        """
        Extract sentiment features.

        Args:
            news: List of NewsArticle objects
            social: Optional SocialSentiment object

        Returns:
            Dictionary of feature names to values
        """
        features = {}

        # News sentiment features
        if news:
            # Analyze news if not already analyzed
            for article in news:
                if article.sentiment_score is None:
                    result = self.sentiment_analyzer.analyze_text(f"{article.title} {article.description}")
                    article.sentiment_score = result.score
                    article.confidence = result.confidence

            sentiment_scores = [a.sentiment_score for a in news if a.sentiment_score is not None]
            confidence_scores = [a.confidence for a in news if a.confidence is not None]

            if sentiment_scores:
                features["news_sentiment_avg"] = float(np.mean(sentiment_scores))
                features["news_sentiment_std"] = float(np.std(sentiment_scores))
                features["news_sentiment_max"] = float(np.max(sentiment_scores))
                features["news_sentiment_min"] = float(np.min(sentiment_scores))
            else:
                features["news_sentiment_avg"] = 0.0
                features["news_sentiment_std"] = 0.0
                features["news_sentiment_max"] = 0.0
                features["news_sentiment_min"] = 0.0

            features["news_volume"] = float(len(news))
            features["news_avg_confidence"] = (
                float(np.mean(confidence_scores)) if confidence_scores else 0.0
            )
        else:
            features["news_sentiment_avg"] = 0.0
            features["news_sentiment_std"] = 0.0
            features["news_sentiment_max"] = 0.0
            features["news_sentiment_min"] = 0.0
            features["news_volume"] = 0.0
            features["news_avg_confidence"] = 0.0

        # Social sentiment features
        if social:
            features["social_sentiment_avg"] = social.average_sentiment
            features["social_sentiment_std"] = social.sentiment_std
            features["social_volume"] = float(social.volume)
            features["social_velocity"] = social.velocity
        else:
            features["social_sentiment_avg"] = 0.0
            features["social_sentiment_std"] = 0.0
            features["social_volume"] = 0.0
            features["social_velocity"] = 0.0

        # Sentiment divergence (news vs social)
        if news and social:
            features["sentiment_divergence"] = abs(
                features["news_sentiment_avg"] - features["social_sentiment_avg"]
            )
        else:
            features["sentiment_divergence"] = 0.0

        # Combined sentiment
        if news and social:
            # Weighted average (news gets higher weight)
            total_volume = features["news_volume"] + features["social_volume"]
            if total_volume > 0:
                news_weight = features["news_volume"] / total_volume
                social_weight = features["social_volume"] / total_volume
                features["combined_sentiment"] = (
                    features["news_sentiment_avg"] * news_weight
                    + features["social_sentiment_avg"] * social_weight
                )
            else:
                features["combined_sentiment"] = 0.0
        elif news:
            features["combined_sentiment"] = features["news_sentiment_avg"]
        elif social:
            features["combined_sentiment"] = features["social_sentiment_avg"]
        else:
            features["combined_sentiment"] = 0.0

        return features



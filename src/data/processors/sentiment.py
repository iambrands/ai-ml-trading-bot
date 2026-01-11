"""Sentiment analysis using transformer models."""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from ..models import NewsArticle, SocialPost
from ...utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SentimentResult:
    """Sentiment analysis result."""

    score: float  # -1 (negative) to +1 (positive)
    confidence: float  # 0 to 1
    label: str  # positive/negative/neutral


class SentimentAnalyzer:
    """Sentiment analysis using transformer models."""

    def __init__(self, model_name: str = "ProsusAI/finbert"):
        """
        Initialize sentiment analyzer.

        Args:
            model_name: Hugging Face model name
        """
        self.model_name = model_name
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.pipeline = pipeline(
                "sentiment-analysis", model=self.model, tokenizer=self.tokenizer, device=-1  # CPU
            )
            logger.info("Initialized sentiment analyzer", model=model_name)
        except Exception as e:
            logger.warning("Failed to load sentiment model, using simple fallback", error=str(e))
            self.pipeline = None

    def analyze_text(self, text: str) -> SentimentResult:
        """
        Analyze single text with proper preprocessing.

        Args:
            text: Text to analyze

        Returns:
            SentimentResult object
        """
        if not text or len(text.strip()) == 0:
            return SentimentResult(score=0.0, confidence=0.0, label="neutral")

        # Truncate if too long
        if len(text) > 512:
            text = text[:512]

        try:
            if self.pipeline:
                result = self.pipeline(text)[0]
                label = result["label"].lower()
                score_raw = result["score"]

                # Map labels to scores
                if "positive" in label:
                    score = score_raw
                elif "negative" in label:
                    score = -score_raw
                else:
                    score = 0.0

                return SentimentResult(score=float(score), confidence=float(score_raw), label=label)
            else:
                # Simple fallback (word-based)
                return self._simple_sentiment(text)

        except Exception as e:
            logger.error("Failed to analyze sentiment", error=str(e), text=text[:100])
            return SentimentResult(score=0.0, confidence=0.0, label="neutral")

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze batch of texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of SentimentResult objects
        """
        return [self.analyze_text(text) for text in texts]

    def analyze_news_articles(self, articles: List[NewsArticle]) -> float:
        """
        Aggregate sentiment from news articles.

        Args:
            articles: List of NewsArticle objects

        Returns:
            Average sentiment score
        """
        if not articles:
            return 0.0

        # Combine title and description for analysis
        texts = [f"{a.title} {a.description}" for a in articles]
        results = self.analyze_batch(texts)

        # Weight by recency and confidence
        scores = []
        for i, result in enumerate(results):
            # Simple weighting: more recent articles have higher weight
            weight = 1.0 / (i + 1)
            weighted_score = result.score * result.confidence * weight
            scores.append(weighted_score)

        if scores:
            return float(np.mean(scores))
        return 0.0

    def analyze_social_posts(self, posts: List[SocialPost]) -> float:
        """
        Aggregate sentiment from social posts.

        Args:
            posts: List of SocialPost objects

        Returns:
            Average sentiment score
        """
        if not posts:
            return 0.0

        # Analyze all posts
        texts = [post.text for post in posts]
        results = self.analyze_batch(texts)

        # Update posts with sentiment scores
        for post, result in zip(posts, results):
            post.sentiment_score = result.score
            post.confidence = result.confidence

        # Weight by engagement and recency
        scores = []
        for post, result in zip(posts, results):
            # Weight by engagement (more engagement = more weight)
            weight = 1.0 + np.log1p(post.engagement)
            weighted_score = result.score * result.confidence * weight
            scores.append(weighted_score)

        if scores:
            return float(np.mean(scores))
        return 0.0

    def aggregate_sentiment(
        self, results: List[SentimentResult], weights: Optional[List[float]] = None
    ) -> float:
        """
        Aggregate multiple sentiment scores.

        Args:
            results: List of SentimentResult objects
            weights: Optional weights for each result

        Returns:
            Weighted average sentiment score
        """
        if not results:
            return 0.0

        if weights is None:
            weights = [1.0] * len(results)

        # Ensure weights match results length
        if len(weights) != len(results):
            weights = [1.0] * len(results)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]

        # Weighted average
        weighted_sum = sum(r.score * r.confidence * w for r, w in zip(results, weights))

        return float(weighted_sum)

    def _simple_sentiment(self, text: str) -> SentimentResult:
        """Simple word-based sentiment analysis fallback."""
        positive_words = {
            "good",
            "great",
            "excellent",
            "positive",
            "bullish",
            "win",
            "success",
            "up",
            "rise",
            "gain",
            "profit",
            "strong",
            "high",
            "increase",
        }
        negative_words = {
            "bad",
            "terrible",
            "negative",
            "bearish",
            "loss",
            "fail",
            "down",
            "fall",
            "drop",
            "weak",
            "low",
            "decrease",
        }

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total = positive_count + negative_count
        if total == 0:
            return SentimentResult(score=0.0, confidence=0.5, label="neutral")

        score = (positive_count - negative_count) / total
        confidence = min(abs(score), 1.0)

        label = "positive" if score > 0 else "negative" if score < 0 else "neutral"

        return SentimentResult(score=float(score), confidence=float(confidence), label=label)



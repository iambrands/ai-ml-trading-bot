"""Text processing utilities."""

import re
from typing import List


class TextProcessor:
    """Text preprocessing utilities."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r"http\S+|www.\S+", "", text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s.,!?;:-]", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Strip
        text = text.strip()

        return text

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Simple tokenization.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        text = TextProcessor.clean_text(text)
        return text.lower().split()

    @staticmethod
    def truncate(text: str, max_length: int = 512) -> str:
        """
        Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length in characters

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    @staticmethod
    def extract_key_phrases(text: str, max_phrases: int = 5) -> List[str]:
        """
        Extract key phrases from text (simple implementation).

        Args:
            text: Text to extract phrases from
            max_phrases: Maximum number of phrases

        Returns:
            List of key phrases
        """
        # Simple phrase extraction based on word frequency
        tokens = TextProcessor.tokenize(text)
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
        }

        # Filter stopwords and short words
        filtered = [t for t in tokens if t not in stopwords and len(t) > 3]

        # Count frequencies
        from collections import Counter

        freq = Counter(filtered)
        phrases = [phrase for phrase, _ in freq.most_common(max_phrases)]

        return phrases




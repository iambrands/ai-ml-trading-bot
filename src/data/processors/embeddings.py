"""Text embeddings using sentence transformers."""

from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from ...utils.logging import get_logger

logger = get_logger(__name__)


class TextEmbedder:
    """Generate text embeddings using sentence transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize text embedder.

        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        try:
            self.model = SentenceTransformer(model_name)
            logger.info("Initialized text embedder", model=model_name)
        except Exception as e:
            logger.warning("Failed to load embedding model", error=str(e), model=model_name)
            self.model = None

    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array
        """
        if not self.model:
            # Return zero vector as fallback
            return np.zeros(384)  # Default dimension for MiniLM

        if not text or len(text.strip()) == 0:
            return np.zeros(self.model.get_sentence_embedding_dimension())

        try:
            # Truncate if too long
            if len(text) > 512:
                text = text[:512]

            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding

        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e), text=text[:100])
            return np.zeros(self.model.get_sentence_embedding_dimension() if self.model else 384)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            Array of embeddings
        """
        if not self.model:
            return np.zeros((len(texts), 384))

        if not texts:
            return np.array([])

        try:
            # Filter empty texts
            valid_texts = [t if t and len(t.strip()) > 0 else " " for t in texts]
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
            return embeddings

        except Exception as e:
            logger.error("Failed to generate batch embeddings", error=str(e))
            return np.zeros((len(texts), self.model.get_sentence_embedding_dimension() if self.model else 384))

    def embed_aggregate(self, texts: List[str], method: str = "mean") -> np.ndarray:
        """
        Generate aggregated embedding from multiple texts.

        Args:
            texts: List of texts to aggregate
            method: Aggregation method ('mean', 'max', 'sum')

        Returns:
            Aggregated embedding vector
        """
        if not texts:
            return self.embed("")

        embeddings = self.embed_batch(texts)

        if method == "mean":
            return np.mean(embeddings, axis=0)
        elif method == "max":
            return np.max(embeddings, axis=0)
        elif method == "sum":
            return np.sum(embeddings, axis=0)
        else:
            return np.mean(embeddings, axis=0)


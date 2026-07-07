"""
Sentence-transformers embedding wrapper with caching and batch support.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Union

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailEmbedder:
    """
    Singleton embedder using sentence-transformers all-MiniLM-L6-v2.

    Produces 384-dimensional L2-normalised embeddings suitable for
    cosine similarity search via FAISS inner-product index.
    """

    def __init__(self, model_name: str = settings.embedding_model) -> None:
        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        self._dim = settings.embedding_dim
        logger.info("Embedding model loaded. Dim=%d", self._dim)

    @property
    def dim(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single string → shape (dim,), float32, L2-normalised."""
        vec = self._model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vec.astype(np.float32)

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """
        Embed a list of strings → shape (N, dim), float32, L2-normalised.
        Uses batching to avoid OOM on large datasets.
        """
        vecs = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
        )
        return vecs.astype(np.float32)

    def email_to_text(self, subject: str, body: str) -> str:
        """Canonical text representation for embedding an email."""
        return f"Subject: {subject}\n\n{body}"


@lru_cache(maxsize=1)
def get_embedder() -> EmailEmbedder:
    """Application-scoped singleton — constructed once."""
    return EmailEmbedder()

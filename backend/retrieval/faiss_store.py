"""
FAISS index management — build, persist, load, and query.

Design decisions:
- IndexFlatIP (inner-product) on L2-normalised vectors gives exact cosine similarity.
- For production scale (>100k), swap to IndexIVFFlat with nlist≈sqrt(N).
- Metadata (email IDs, subjects) stored in a companion JSON to keep FAISS pure-numeric.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from backend.config import get_settings
from backend.retrieval.embedder import get_embedder

logger = logging.getLogger(__name__)
settings = get_settings()


class FAISSStore:
    """
    Thread-safe FAISS vector store.

    Index type: IndexFlatIP (exact cosine similarity on normalised vectors).
    Companion metadata file maps FAISS integer indices → email metadata dicts.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._embedder = get_embedder()
        self._index: faiss.Index | None = None
        self._metadata: list[dict[str, Any]] = []
        self._index_path = Path(settings.faiss_index_path)
        self._meta_path = Path(settings.faiss_metadata_path)

        if self._index_path.exists() and self._meta_path.exists():
            self._load()
        else:
            self._init_empty()

    # ── Private ──────────────────────────────────────────────────────────────

    def _init_empty(self) -> None:
        dim = self._embedder.dim
        self._index = faiss.IndexFlatIP(dim)
        self._metadata = []
        logger.info("Initialised empty FAISS IndexFlatIP(dim=%d)", dim)

    def _load(self) -> None:
        logger.info("Loading FAISS index from %s", self._index_path)
        self._index = faiss.read_index(str(self._index_path))
        with self._meta_path.open("r", encoding="utf-8") as f:
            self._metadata = json.load(f)
        logger.info("FAISS index loaded: %d vectors", self._index.ntotal)

    def _save(self) -> None:
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self._index_path))
        with self._meta_path.open("w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False)
        logger.debug("FAISS index saved: %d vectors", self._index.ntotal)

    # ── Public ───────────────────────────────────────────────────────────────

    @property
    def size(self) -> int:
        with self._lock:
            return self._index.ntotal if self._index else 0

    def add(self, vectors: np.ndarray, metadata: list[dict[str, Any]]) -> None:
        """Add pre-computed embeddings and their metadata dicts."""
        assert len(vectors) == len(metadata), "vectors / metadata length mismatch"
        vectors = vectors.astype(np.float32)
        with self._lock:
            self._index.add(vectors)  # type: ignore[union-attr]
            self._metadata.extend(metadata)
            self._save()
        logger.info("Added %d vectors → FAISS total=%d", len(vectors), self.size)

    def add_texts(
        self, subjects: list[str], bodies: list[str], metadata: list[dict[str, Any]]
    ) -> None:
        """Embed texts then add to the index."""
        texts = [
            self._embedder.email_to_text(s, b) for s, b in zip(subjects, bodies, strict=True)
        ]
        vecs = self._embedder.embed_batch(texts)
        self.add(vecs, metadata)

    def search(
        self, query: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search for the top_k most similar emails.
        Returns list of metadata dicts enriched with 'similarity_score'.
        """
        if self.size == 0:
            return []
        vec = self._embedder.embed_text(query).reshape(1, -1)
        with self._lock:
            scores, indices = self._index.search(vec, min(top_k, self.size))  # type: ignore[union-attr]

        results: list[dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            meta = dict(self._metadata[idx])
            meta["similarity_score"] = float(score)
            results.append(meta)
        return results

    def rebuild(self, subjects: list[str], bodies: list[str], metadata: list[dict[str, Any]]) -> None:
        """Full rebuild — wipe and re-add all vectors."""
        with self._lock:
            self._init_empty()
            self._metadata = []
        self.add_texts(subjects, bodies, metadata)
        logger.info("FAISS index rebuilt from %d emails", len(metadata))

    def delete_index(self) -> None:
        """Remove persisted index files and reset in-memory state."""
        with self._lock:
            self._init_empty()
            if self._index_path.exists():
                self._index_path.unlink()
            if self._meta_path.exists():
                self._meta_path.unlink()


_store_instance: FAISSStore | None = None
_store_lock = threading.Lock()


def get_faiss_store() -> FAISSStore:
    """Application-scoped singleton FAISS store."""
    global _store_instance
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                _store_instance = FAISSStore()
    return _store_instance

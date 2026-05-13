from __future__ import annotations

from typing import Iterable

from fastembed import TextEmbedding

from .config import EMBEDDING_MODEL

# Model MUST match scripts/sync_obsidian.py; different models produce incompatible vectors.
_embedder: TextEmbedding | None = None


def get_embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _embedder


def embed(text: str) -> list[float]:
    vectors = list(get_embedder().embed([text]))
    return [float(x) for x in vectors[0]]


def embed_batch(texts: Iterable[str]) -> list[list[float]]:
    return [[float(x) for x in v] for v in get_embedder().embed(list(texts))]

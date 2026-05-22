from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.models import Distance, VectorParams

from . import config
from .embedding import embed

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY,
            timeout=20,
        )
    return _client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Qdrant requires payload indexes before filtered scroll/search works.
# Without these, filter queries return HTTP 400.
_INDEXES: dict[str, tuple[str, ...]] = {
    config.COLL_TASKS: ("status", "priority", "user_id"),
    config.COLL_KNOWLEDGE: ("source", "type"),
    config.COLL_MEMORY: ("type", "user_id"),
    config.COLL_CODE: ("repo_id", "commit", "path", "language"),
}


def ensure_collection(collection: str, vector_size: int = config.EMBEDDING_DIM) -> None:
    client = get_client()
    existing = {c.name for c in client.get_collections().collections}
    if collection in existing:
        return
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def ensure_payload_indexes() -> None:
    client = get_client()
    for collection in _INDEXES:
        try:
            ensure_collection(collection)
        except Exception:
            pass
    for collection, fields in _INDEXES.items():
        for field in fields:
            try:
                client.create_payload_index(
                    collection_name=collection,
                    field_name=field,
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                    wait=True,
                )
            except Exception:
                pass
    # Text index for keyword substring search on code chunks
    try:
        client.create_payload_index(
            collection_name=config.COLL_CODE,
            field_name="text",
            field_schema=qmodels.TextIndexParams(
                type=qmodels.TextIndexType.TEXT,
                tokenizer=qmodels.TokenizerType.WORD,
                min_token_len=2,
                max_token_len=30,
                lowercase=True,
            ),
            wait=True,
        )
    except Exception:
        pass
    # Text index on path field for path-based search
    try:
        client.create_payload_index(
            collection_name=config.COLL_CODE,
            field_name="path",
            field_schema=qmodels.TextIndexParams(
                type=qmodels.TextIndexType.TEXT,
                tokenizer=qmodels.TokenizerType.WORD,
                min_token_len=2,
                max_token_len=60,
                lowercase=True,
            ),
            wait=True,
        )
    except Exception:
        pass


def search(
    collection: str,
    query: str,
    limit: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    vector = embed(query)
    qfilter = None
    if filters:
        must = [
            qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
            for k, v in filters.items()
        ]
        qfilter = qmodels.Filter(must=must)

    hits = get_client().query_points(
        collection_name=collection,
        query=vector,
        limit=limit,
        query_filter=qfilter,
        with_payload=True,
    ).points
    return [
        {"id": str(h.id), "score": float(h.score), "payload": h.payload or {}}
        for h in hits
    ]


def upsert(
    collection: str,
    text: str,
    payload: dict[str, Any],
    point_id: str | None = None,
) -> str:
    pid = point_id or str(uuid.uuid4())
    vector = embed(text)
    full_payload = {**payload, "created_at": payload.get("created_at") or _now()}
    get_client().upsert(
        collection_name=collection,
        points=[qmodels.PointStruct(id=pid, vector=vector, payload=full_payload)],
        wait=True,
    )
    return pid


def scroll(
    collection: str,
    filters: dict[str, Any] | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    qfilter = None
    if filters:
        must = [
            qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
            for k, v in filters.items()
        ]
        qfilter = qmodels.Filter(must=must)

    points, _ = get_client().scroll(
        collection_name=collection,
        scroll_filter=qfilter,
        limit=limit,
        with_payload=True,
    )
    return [{"id": str(p.id), "payload": p.payload or {}} for p in points]


def set_payload(collection: str, point_id: str, updates: dict[str, Any]) -> None:
    get_client().set_payload(
        collection_name=collection,
        payload=updates,
        points=[point_id],
        wait=True,
    )


def delete_points(collection: str, point_ids: list[str]) -> int:
    if not point_ids:
        return 0
    get_client().delete(
        collection_name=collection,
        points_selector=qmodels.PointIdsList(points=point_ids),
        wait=True,
    )
    return len(point_ids)


def delete_by_filter(collection: str, filters: dict[str, Any]) -> None:
    must = [
        qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
        for k, v in filters.items()
    ]
    get_client().delete(
        collection_name=collection,
        points_selector=qmodels.FilterSelector(filter=qmodels.Filter(must=must)),
        wait=True,
    )


def keyword_search(
    collection: str,
    keywords: list[str],
    limit: int = 10,
    filters: dict[str, Any] | None = None,
    text_field: str = "text",
) -> list[dict[str, Any]]:
    """Search by keyword substring match on a text payload field.

    Uses Qdrant MatchText (substring) on each keyword with AND logic,
    combined with any additional filters (e.g. repo_id).
    Returns results without score (scroll-based).
    """
    must: list[qmodels.FieldCondition] = [
        qmodels.FieldCondition(key=text_field, match=qmodels.MatchText(text=kw))
        for kw in keywords
    ]
    if filters:
        must.extend(
            qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
            for k, v in filters.items()
        )
    qfilter = qmodels.Filter(must=must)
    points, _ = get_client().scroll(
        collection_name=collection,
        scroll_filter=qfilter,
        limit=limit,
        with_payload=True,
    )
    return [{"id": str(p.id), "score": 0.0, "payload": p.payload or {}} for p in points]


def path_search(
    collection: str,
    path_terms: list[str],
    limit: int = 10,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Find chunks whose file path contains any of the given terms (OR logic, substring)."""
    must: list[qmodels.FieldCondition] = []
    if filters:
        must.extend(
            qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
            for k, v in filters.items()
        )
    qfilter = qmodels.Filter(must=must) if must else None
    points, _ = get_client().scroll(
        collection_name=collection,
        scroll_filter=qfilter,
        limit=3000,
        with_payload=["path", "text", "repo_id", "commit", "start_line", "end_line", "repo_name", "language"],
    )
    lower_terms = [t.lower() for t in path_terms]
    matched = []
    for p in points:
        path = (p.payload or {}).get("path", "").lower()
        if any(term in path for term in lower_terms):
            matched.append({"id": str(p.id), "score": 0.0, "payload": p.payload or {}})
            if len(matched) >= limit:
                break
    return matched


def count(collection: str, filters: dict[str, Any] | None = None) -> int:
    qfilter = None
    if filters:
        must = [
            qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v))
            for k, v in filters.items()
        ]
        qfilter = qmodels.Filter(must=must)
    result = get_client().count(collection_name=collection, count_filter=qfilter, exact=True)
    return int(result.count)

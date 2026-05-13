from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

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
}


def ensure_payload_indexes() -> None:
    client = get_client()
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

    hits = get_client().search(
        collection_name=collection,
        query_vector=vector,
        limit=limit,
        query_filter=qfilter,
        with_payload=True,
    )
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

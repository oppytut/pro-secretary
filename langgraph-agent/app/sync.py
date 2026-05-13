from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from qdrant_client.http import models as qmodels

from . import config
from .embedding import embed_batch
from .qdrant_helper import get_client

VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/vault")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BATCH = 64

# Deterministic UUIDv5 namespace for vault chunks.
# Changing this invalidates every previously-synced point. Do not change.
_VAULT_NAMESPACE = uuid.UUID("3f2b1c50-1b0f-4d4b-9b9e-ecb1a7a5e5b1")


def _point_id(relative_path: str, chunk_index: int) -> str:
    return str(uuid.uuid5(_VAULT_NAMESPACE, f"{relative_path}::{chunk_index}"))


def _chunk_text(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= CHUNK_SIZE:
        return [text]

    separators = ["\n## ", "\n### ", "\n\n", "\n- ", "\n", " "]
    chunks: list[str] = []
    remaining = text

    while len(remaining) > CHUNK_SIZE:
        split_at = -1
        window = remaining[: CHUNK_SIZE + 100]
        for sep in separators:
            idx = window.rfind(sep, CHUNK_SIZE // 2, CHUNK_SIZE)
            if idx > 0:
                split_at = idx
                break
        if split_at < 0:
            split_at = CHUNK_SIZE

        chunks.append(remaining[:split_at].strip())
        overlap_start = max(0, split_at - CHUNK_OVERLAP)
        remaining = remaining[overlap_start:].lstrip()

    if remaining:
        chunks.append(remaining)

    return [c for c in chunks if c]


def _hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def sync_vault(vault_path: str | None = None) -> dict[str, int]:
    root = Path(vault_path or VAULT_PATH)
    if not root.exists():
        return {"status_code": 404, "files": 0, "chunks_upserted": 0, "chunks_deleted": 0}

    client = get_client()
    now = datetime.now(timezone.utc).isoformat()

    seen_ids: set[str] = set()
    points_buffer: list[tuple[str, list[float], dict]] = []
    pending_texts: list[str] = []
    pending_meta: list[tuple[str, dict]] = []

    files_count = 0
    for md_file in root.rglob("*.md"):
        if "Templates" in md_file.parts or md_file.name.startswith("."):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        files_count += 1
        relative = str(md_file.relative_to(root))
        file_hash = _hash(content)
        folder = relative.split("/")[0] if "/" in relative else ""

        for i, chunk in enumerate(_chunk_text(content)):
            pid = _point_id(relative, i)
            seen_ids.add(pid)
            pending_texts.append(chunk)
            pending_meta.append(
                (
                    pid,
                    {
                        "content": chunk,
                        "source_file": relative,
                        "source": "obsidian",
                        "chunk_index": i,
                        "file_hash": file_hash,
                        "folder": folder,
                        "type": "knowledge",
                        "synced_at": now,
                    },
                )
            )

            if len(pending_texts) >= BATCH:
                _flush(client, pending_texts, pending_meta, points_buffer)
                pending_texts.clear()
                pending_meta.clear()

    if pending_texts:
        _flush(client, pending_texts, pending_meta, points_buffer)

    deleted = _sweep_orphans(client, seen_ids)

    return {
        "status_code": 200,
        "files": files_count,
        "chunks_upserted": len(seen_ids),
        "chunks_deleted": deleted,
    }


def _flush(
    client,
    texts: list[str],
    meta: list[tuple[str, dict]],
    _buffer: list,
) -> None:
    vectors = embed_batch(texts)
    points = [
        qmodels.PointStruct(id=pid, vector=vec, payload=payload)
        for vec, (pid, payload) in zip(vectors, meta)
    ]
    client.upsert(collection_name=config.COLL_KNOWLEDGE, points=points, wait=True)


def _sweep_orphans(client, seen_ids: set[str]) -> int:
    deleted = 0
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=config.COLL_KNOWLEDGE,
            scroll_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="source", match=qmodels.MatchValue(value="obsidian")
                    )
                ]
            ),
            limit=256,
            offset=offset,
            with_payload=False,
        )
        orphan_ids = [str(p.id) for p in points if str(p.id) not in seen_ids]
        if orphan_ids:
            client.delete(
                collection_name=config.COLL_KNOWLEDGE,
                points_selector=qmodels.PointIdsList(points=orphan_ids),
                wait=True,
            )
            deleted += len(orphan_ids)
        if offset is None:
            break
    return deleted

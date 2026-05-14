#!/usr/bin/env python3

# DEPRECATED: Vault sync now runs inside the LangGraph agent container.
# Use POST /api/sync_vault (or scripts/trigger_sync_vault.sh) instead.
# Kept here as standalone reference only; not wired to cron anymore.

import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/opt/ai-secretary/vault")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 100

if not QDRANT_URL or not QDRANT_API_KEY:
    raise RuntimeError("QDRANT_URL and QDRANT_API_KEY must be set")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedder = SentenceTransformer(EMBEDDING_MODEL)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n## ", "\n### ", "\n- ", "\n\n", "\n", " "],
)


def ensure_collection():
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Collection '{COLLECTION_NAME}' created.")


def get_file_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


def sync_vault():
    vault = Path(VAULT_PATH)
    if not vault.exists():
        print(f"Vault path not found: {VAULT_PATH}")
        return

    md_files = [f for f in vault.rglob("*.md") if "Templates" not in str(f)]
    print(f"Found {len(md_files)} markdown files")

    points = []
    point_id = 0

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        relative_path = str(md_file.relative_to(vault))
        file_hash = get_file_hash(content)
        chunks = splitter.split_text(content)

        for i, chunk in enumerate(chunks):
            embedding = embedder.encode(chunk).tolist()
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "content": chunk,
                        "source_file": relative_path,
                        "chunk_index": i,
                        "file_hash": file_hash,
                        "synced_at": datetime.now(timezone.utc).isoformat(),
                        "folder": relative_path.split("/")[0],
                    },
                )
            )
            point_id += 1

    if not points:
        print("No content to sync.")
        return

    client.delete_collection(COLLECTION_NAME)
    ensure_collection()

    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)

    print(f"Synced {len(points)} chunks from {len(md_files)} files.")


if __name__ == "__main__":
    print("WARNING: scripts/sync_obsidian.py is DEPRECATED.")
    print("Use POST /api/sync_vault (or scripts/trigger_sync_vault.sh) instead.")
    print(f"Syncing Obsidian vault: {VAULT_PATH}")
    ensure_collection()
    sync_vault()

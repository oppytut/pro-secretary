#!/usr/bin/env python3

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise RuntimeError("QDRANT_URL and QDRANT_API_KEY must be set")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

COLLECTIONS = {
    "knowledge": 384,
    "agent_memory": 384,
    "tasks": 384,
    "people": 384,
    "decisions": 384,
}


def init_collections():
    existing = [c.name for c in client.get_collections().collections]

    for name, vector_size in COLLECTIONS.items():
        if name in existing:
            print(f"  [skip] '{name}' already exists")
            continue

        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        print(f"  [created] '{name}' (dim={vector_size}, cosine)")

    print(f"\nDone. {len(COLLECTIONS)} collections ready.")


if __name__ == "__main__":
    print(f"Connecting to Qdrant: {QDRANT_URL}")
    init_collections()

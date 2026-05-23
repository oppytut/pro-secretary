"""Self-improving skills — passive logging and semantic recall."""
from __future__ import annotations

import logging
from typing import Any

from . import config
from .qdrant_helper import ensure_collection, search, upsert

logger = logging.getLogger(__name__)


def log_skill(
    name: str,
    description: str,
    steps: list[str] | None = None,
    tags: list[str] | None = None,
    trigger: str = "",
    user_id: str | int | None = None,
) -> str:
    """Store a skill (procedure/pattern) in the skills collection."""
    ensure_collection(config.COLL_SKILLS)
    text_parts = [name, description]
    if steps:
        text_parts.append(" ".join(steps))
    embed_text = " | ".join(text_parts)

    payload = {
        "name": name,
        "description": description,
        "steps": steps or [],
        "tags": tags or [],
        "trigger": trigger,
        "user_id": str(user_id) if user_id else "",
    }
    point_id = upsert(config.COLL_SKILLS, embed_text, payload)
    logger.info("Skill logged: %s (id=%s)", name, point_id)
    return point_id


def search_skills(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Semantic search for skills matching a query or name."""
    ensure_collection(config.COLL_SKILLS)
    hits = search(config.COLL_SKILLS, query, limit=limit)
    return hits

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from . import config, qdrant_helper


def search_knowledge(query: str, limit: int = 5) -> list[dict[str, Any]]:
    return qdrant_helper.search(config.COLL_KNOWLEDGE, query, limit=limit)


def search_memory(query: str, limit: int = 5) -> list[dict[str, Any]]:
    return qdrant_helper.search(config.COLL_MEMORY, query, limit=limit)


def store_memory(text: str, meta: dict[str, Any] | None = None) -> str:
    payload = {"content": text, "type": "conversation", **(meta or {})}
    return qdrant_helper.upsert(config.COLL_MEMORY, text, payload)


def create_task(
    title: str,
    priority: str = "medium",
    due_date: str | None = None,
    user_id: str | int | None = None,
) -> str:
    payload = {
        "title": title,
        "status": "pending",
        "priority": priority,
        "due_date": due_date,
        "user_id": str(user_id) if user_id is not None else None,
    }
    return qdrant_helper.upsert(config.COLL_TASKS, title, payload)


def list_pending_tasks(limit: int = 20) -> list[dict[str, Any]]:
    return qdrant_helper.scroll(
        config.COLL_TASKS, filters={"status": "pending"}, limit=limit
    )


def complete_task(task_id: str) -> None:
    qdrant_helper.set_payload(
        config.COLL_TASKS,
        task_id,
        {"status": "done", "completed_at": datetime.now(timezone.utc).isoformat()},
    )


def store_note(content: str, source: str = "telegram", user_id: str | int | None = None) -> str:
    payload = {
        "content": content,
        "type": "note",
        "source": source,
        "user_id": str(user_id) if user_id is not None else None,
    }
    return qdrant_helper.upsert(config.COLL_KNOWLEDGE, content, payload)


async def get_today_schedule() -> list[dict[str, Any]]:
    if not config.CALCOM_API_KEY:
        return []
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=1)
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            r = await client.get(
                f"{config.CALCOM_BASE_URL}/api/v1/bookings",
                headers={"Authorization": f"Bearer {config.CALCOM_API_KEY}"},
                params={
                    "afterStart": now.isoformat(),
                    "beforeEnd": end.isoformat(),
                },
            )
            if r.status_code >= 400:
                return []
            data = r.json()
        except (httpx.RequestError, ValueError):
            return []
    bookings = data.get("bookings") or data.get("data") or []
    return [
        {
            "title": b.get("title") or b.get("eventType", {}).get("title"),
            "start": b.get("startTime") or b.get("start"),
            "end": b.get("endTime") or b.get("end"),
            "status": b.get("status"),
        }
        for b in bookings
    ]

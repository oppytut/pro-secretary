from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

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


def delete_tasks(task_ids: list[str]) -> int:
    return qdrant_helper.delete_points(config.COLL_TASKS, task_ids)


def find_pending_tasks_by_title(title_query: str) -> list[dict[str, Any]]:
    needle = title_query.strip().lower()
    if not needle:
        return []
    matches: list[dict[str, Any]] = []
    for point in qdrant_helper.scroll(
        config.COLL_TASKS, filters={"status": "pending"}, limit=100
    ):
        title = (point.get("payload", {}).get("title") or "").lower()
        if needle in title:
            matches.append(point)
    return matches


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
    tz = ZoneInfo(config.TIMEZONE)
    start_local = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            r = await client.get(
                f"{config.CALCOM_BASE_URL}/api/v1/bookings",
                headers={"Authorization": f"Bearer {config.CALCOM_API_KEY}"},
                params={
                    "afterStart": start_local.isoformat(),
                    "beforeEnd": end_local.isoformat(),
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

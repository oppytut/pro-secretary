from __future__ import annotations

import os
from typing import Any

import httpx

AGENT_URL = os.getenv("AGENT_URL", "http://langgraph-agent:8090").rstrip("/")
AGENT_SECRET = os.getenv("AGENT_SECRET", "")


def agent_headers() -> dict[str, str]:
    if AGENT_SECRET:
        return {"x-agent-secret": AGENT_SECRET}
    return {}


async def agent_post(path: str, payload: dict[str, Any], timeout: float = 60.0) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.post(
            f"{AGENT_URL}{path}",
            headers=agent_headers(),
            json=payload,
        )

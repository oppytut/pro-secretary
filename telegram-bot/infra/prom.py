from __future__ import annotations

import os
from typing import Any

import httpx

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090").rstrip("/")


async def prom_query(query: str) -> list[Any] | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query},
            )
        if r.status_code == 200:
            results: list[Any] = r.json().get("data", {}).get("result", [])
            return results
    except httpx.RequestError:
        pass
    return None

from __future__ import annotations

import os
from typing import Any

import httpx

GH_PAT = os.getenv("GH_PAT", "")


async def gh_api(path: str) -> dict[str, Any] | list[Any] | None:
    if not GH_PAT:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"https://api.github.com{path}",
                headers={
                    "Authorization": f"Bearer {GH_PAT}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
        if r.status_code == 200:
            data: dict[str, Any] | list[Any] = r.json()
            return data
    except httpx.RequestError:
        pass
    return None

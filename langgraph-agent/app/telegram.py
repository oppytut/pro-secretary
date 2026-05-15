from __future__ import annotations

from typing import Any

import httpx

from . import config

_TELEGRAM_API = "https://api.telegram.org"


async def send_message(
    text: str,
    chat_id: str | int | None = None,
    reply_markup: dict[str, Any] | None = None,
) -> dict:
    if not config.TELEGRAM_BOT_TOKEN:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"}

    targets: list[str]
    if chat_id is not None:
        targets = [str(chat_id)]
    else:
        targets = config.TELEGRAM_ALLOWED_USERS

    if not targets:
        return {"ok": False, "error": "no recipients"}

    results = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for recipient in targets:
            payload: dict[str, Any] = {
                "chat_id": recipient,
                "text": text,
                "disable_web_page_preview": True,
            }
            if reply_markup is not None:
                payload["reply_markup"] = reply_markup
            r = await client.post(
                f"{_TELEGRAM_API}/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                json=payload,
            )
            results.append({"chat_id": recipient, "status_code": r.status_code})

    ok = all(x["status_code"] == 200 for x in results)
    return {"ok": ok, "delivered": len(targets), "results": results}

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from infra.auth import ALLOWED_USERS, authorized

logger = logging.getLogger(__name__)

DEPS_CHECK_ENABLED = os.getenv("DEPS_CHECK_ENABLED", "true").lower() in ("1", "true", "yes")
DEPS_CHECK_HOUR = int(os.getenv("DEPS_CHECK_HOUR", "3"))
DEPS_CHECK_MINUTE = int(os.getenv("DEPS_CHECK_MINUTE", "0"))


async def run_deps_check(repo_id: str | None = None) -> str:
    from bot import _agent_post

    payload: dict[str, Any] = {}
    if repo_id:
        payload["repo_id"] = repo_id
    try:
        r = await _agent_post("/api/deps/scan", payload, timeout=300.0)
    except httpx.RequestError as exc:
        return f"⚠️ Gagal menghubungi agent: {exc}"
    if r.status_code != 200:
        return f"⚠️ Deps scan failed (HTTP {r.status_code})."
    data = r.json()
    return data.get("report") or "ℹ️ No report."


async def deps_check_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id:
        return
    try:
        report = await run_deps_check()
        has_vulns = "🔴" in report or "🟠" in report or "🟡" in report
        if has_vulns:
            await context.bot.send_message(
                chat_id=chat_id,
                text=report[:4000],
                parse_mode="HTML",
            )
            logger.info("Deps check: vulnerabilities reported")
        else:
            logger.info("Deps check: no vulnerabilities, no notification sent")
    except Exception as e:
        logger.error(f"Deps check job failed: {e}")


@authorized
async def cmd_deps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo_id = context.args[0] if context.args else None
    target = repo_id or "semua repo"
    await update.message.reply_text(
        f"🛡️ Scanning dependencies untuk {target}... (bisa 1-3 menit)"
    )
    try:
        report = await run_deps_check(repo_id)
        await update.message.reply_text(report[:4000], parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"⚠️ Deps check failed: {exc}")

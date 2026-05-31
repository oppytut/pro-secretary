from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from infra.agent import agent_post
from infra.auth import ALLOWED_USERS, authorized

logger = logging.getLogger(__name__)

COVERAGE_AGENT_ENABLED = os.getenv("COVERAGE_AGENT_ENABLED", "true").lower() in ("1", "true", "yes")
COVERAGE_AGENT_HOUR = int(os.getenv("COVERAGE_AGENT_HOUR", "4"))
COVERAGE_AGENT_MINUTE = int(os.getenv("COVERAGE_AGENT_MINUTE", "0"))
COVERAGE_SCAN_TIMEOUT_SEC = float(os.getenv("COVERAGE_SCAN_TIMEOUT_SEC", "600"))


async def _list_repos() -> list[str]:
    try:
        r = await agent_post("/api/coverage/repos", {}, timeout=10.0)
        if r.status_code == 200:
            data = r.json()
            repos = data.get("repos", [])
            return [str(x) for x in repos]
    except httpx.RequestError as exc:
        logger.warning("coverage list repos: %s", exc)
    return []


async def _set_repos(repos: list[str]) -> bool:
    try:
        r = await agent_post("/api/coverage/repos", {"repos": repos}, timeout=10.0)
        return r.status_code == 200
    except httpx.RequestError:
        return False


async def _scan_repo(repo: str, branch: str = "main") -> dict[str, Any]:
    try:
        r = await agent_post(
            "/api/coverage/scan",
            {"repo": repo, "branch": branch},
            timeout=COVERAGE_SCAN_TIMEOUT_SEC,
        )
        if r.status_code == 200:
            data: dict[str, Any] = r.json()
            return data
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except httpx.RequestError as exc:
        return {"ok": False, "error": f"request error: {exc}"}


def _format_scan_result(repo: str, result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"⚠️ <b>{repo}</b> — {result.get('error', 'unknown error')}"
    if result.get("skipped"):
        return f"ℹ️ <b>{repo}</b> — {result.get('reason', 'skipped')}"
    target = result.get("lowest", "?")
    pct = result.get("coverage", 0.0)
    pr_url = result.get("pr_url", "")
    pr_num = result.get("pr_number", "?")
    return (
        f"✅ <b>{repo}</b>\n"
        f"   📉 {target} ({pct:.1f}%)\n"
        f"   🔧 PR #{pr_num}: {pr_url}"
    )


async def coverage_scan_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id:
        return
    repos = await _list_repos()
    if not repos:
        logger.info("Coverage scan: no whitelist configured, skipping")
        return

    sections: list[str] = ["📊 <b>Coverage Agent — daily scan</b>", ""]
    any_pr = False
    for repo in repos:
        try:
            result = await _scan_repo(repo)
        except Exception as exc:
            logger.error("Coverage scan %s failed: %s", repo, exc)
            sections.append(f"❌ <b>{repo}</b> — exception: {exc}")
            continue
        sections.append(_format_scan_result(repo, result))
        if result.get("ok") and result.get("pr_url"):
            any_pr = True

    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    sections.append("")
    sections.append(f"<i>{now.strftime('%A, %d %B %Y %H:%M')} WIB</i>")

    if any_pr:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="\n".join(sections)[:4000],
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.error("Coverage scan send failed: %s", exc)
    else:
        logger.info("Coverage scan: no new PRs, silent")


@authorized
async def cmd_coverage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args:
        repos = await _list_repos()
        if not repos:
            await update.message.reply_text(
                "📊 No coverage repos configured.\nUse <code>/coverage add owner/name</code> to add.",
                parse_mode="HTML",
            )
            return
        await update.message.reply_text(
            f"📊 Scanning {len(repos)} repo(s)... (this may take several minutes)"
        )
        sections: list[str] = ["📊 <b>Coverage Scan</b>", ""]
        for repo in repos:
            result = await _scan_repo(repo)
            sections.append(_format_scan_result(repo, result))
        await update.message.reply_text("\n".join(sections)[:4000], parse_mode="HTML")
        return

    action = args[0].lower()
    if action == "list":
        repos = await _list_repos()
        if not repos:
            await update.message.reply_text("📋 No coverage repos configured.")
            return
        lines = ["📊 <b>Coverage Repos</b>", ""]
        for repo in repos:
            lines.append(f"• <code>{repo}</code>")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return

    if action == "add" and len(args) >= 2:
        repo = args[1]
        repos = await _list_repos()
        if repo in repos:
            await update.message.reply_text(
                f"ℹ️ <code>{repo}</code> already in coverage whitelist.", parse_mode="HTML"
            )
            return
        repos.append(repo)
        if await _set_repos(repos):
            await update.message.reply_text(
                f"✅ Added <code>{repo}</code> to coverage whitelist.", parse_mode="HTML"
            )
        else:
            await update.message.reply_text("⚠️ Failed to update whitelist.")
        return

    if action in ("del", "remove") and len(args) >= 2:
        repo = args[1]
        repos = await _list_repos()
        if repo not in repos:
            await update.message.reply_text(
                f"ℹ️ <code>{repo}</code> not in coverage whitelist.", parse_mode="HTML"
            )
            return
        repos.remove(repo)
        if await _set_repos(repos):
            await update.message.reply_text(
                f"✅ Removed <code>{repo}</code> from coverage whitelist.", parse_mode="HTML"
            )
        else:
            await update.message.reply_text("⚠️ Failed to update whitelist.")
        return

    if action == "scan" and len(args) >= 2:
        repo = args[1]
        branch = args[2] if len(args) >= 3 else "main"
        await update.message.reply_text(
            f"📊 Scanning <code>{repo}</code> on <code>{branch}</code>...", parse_mode="HTML"
        )
        result = await _scan_repo(repo, branch=branch)
        await update.message.reply_text(_format_scan_result(repo, result), parse_mode="HTML")
        return

    await update.message.reply_text(
        "Usage:\n/coverage — scan all whitelisted repos\n"
        "/coverage list — show whitelist\n"
        "/coverage add owner/name — add repo\n"
        "/coverage del owner/name — remove repo\n"
        "/coverage scan owner/name [branch] — scan single repo"
    )

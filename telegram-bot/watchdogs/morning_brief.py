from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from infra.agent import agent_post
from infra.auth import ALLOWED_USERS, authorized
from infra.gh import gh_api
from infra.prom import prom_query

logger = logging.getLogger(__name__)

GH_PAT = os.getenv("GH_PAT", "")
MORNING_BRIEF_ENABLED = os.getenv("MORNING_BRIEF_ENABLED", "true").lower() in ("1", "true", "yes")
MORNING_BRIEF_HOUR = int(os.getenv("MORNING_BRIEF_HOUR", "7"))
MORNING_BRIEF_MINUTE = int(os.getenv("MORNING_BRIEF_MINUTE", "0"))

_GH_REPOS: list[str] = ["gmedia/erp"]


async def collect_github_summary() -> list[str]:
    lines: list[str] = []
    if not GH_PAT:
        return lines

    for repo in _GH_REPOS:
        prs = await gh_api(f"/repos/{repo}/pulls?state=open&per_page=10&sort=updated")
        if isinstance(prs, list) and prs:
            lines.append(f"📌 <b>{repo}</b> — {len(prs)} open PR(s):")
            for pr in prs[:5]:
                draft = " [draft]" if pr.get("draft") else ""
                lines.append(f"  • #{pr['number']} {pr['title']}{draft}")

        since = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        commits = await gh_api(f"/repos/{repo}/commits?per_page=10&since={since}")
        if isinstance(commits, list) and commits:
            lines.append(f"  📝 {len(commits)} commit(s) last 12h:")
            for c in commits[:3]:
                msg = (c.get("commit", {}).get("message") or "").split("\n")[0][:60]
                author = c.get("commit", {}).get("author", {}).get("name", "?")
                lines.append(f"  • {msg} ({author})")

        checks = await gh_api(f"/repos/{repo}/commits/HEAD/check-runs?per_page=10")
        if isinstance(checks, dict) and checks.get("check_runs"):
            failed = [cr for cr in checks["check_runs"] if cr.get("conclusion") == "failure"]
            if failed:
                lines.append(f"  ❌ {len(failed)} failing CI check(s):")
                for cr in failed[:3]:
                    lines.append(f"  • {cr['name']}")

    return lines


async def collect_prom_summary() -> list[str]:
    lines: list[str] = []

    up_results = await prom_query('up{job="node"}')
    if not up_results:
        return ["⚠️ Prometheus tidak tersedia"]

    all_up = True
    for target in up_results:
        name = target["metric"].get("instance_name", target["metric"].get("instance", "?"))
        is_up = target["value"][1] == "1"
        if not is_up:
            all_up = False
            lines.append(f"❌ VPS <b>{name}</b> DOWN")

    if all_up:
        lines.append(f"✅ Semua VPS UP ({len(up_results)} target)")

    alerts = await prom_query('ALERTS{alertstate="firing"}')
    if alerts:
        lines.append(f"🚨 {len(alerts)} active alert(s):")
        for a in alerts[:5]:
            m = a["metric"]
            lines.append(f"  • [{m.get('severity', '?')}] {m.get('alertname', '?')} — {m.get('instance_name', '?')}")
    else:
        lines.append("✅ No active alerts")

    return lines


async def collect_agent_briefing() -> str:
    try:
        r = await agent_post("/api/briefing", {}, timeout=60.0)
        if r.status_code == 200:
            response: str = r.json().get("response", "")
            return response
    except httpx.RequestError:
        pass
    return ""


async def build_morning_brief() -> str:
    sections: list[str] = []
    sections.append("☀️ <b>Morning Standup Brief</b>")
    sections.append("")

    agent_brief = await collect_agent_briefing()
    if agent_brief:
        sections.append(agent_brief)
        sections.append("")

    prom_lines = await collect_prom_summary()
    if prom_lines:
        sections.append("🖥️ <b>Infra Status</b>")
        sections.extend(prom_lines)
        sections.append("")

    gh_lines = await collect_github_summary()
    if gh_lines:
        sections.append("🐙 <b>Code Activity</b>")
        sections.extend(gh_lines)
        sections.append("")

    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    sections.append(f"<i>{now.strftime('%A, %d %B %Y %H:%M')} WIB</i>")

    return "\n".join(sections)


async def morning_brief_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id:
        return

    try:
        text = await build_morning_brief()
        await context.bot.send_message(
            chat_id=chat_id,
            text=text[:4000],
            parse_mode="HTML",
        )
        logger.info("Morning brief sent to %s", chat_id)
    except Exception as e:
        logger.error("Morning brief job failed: %s", e)


@authorized
async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⏳ Menyiapkan briefing...")
    try:
        text = await build_morning_brief()
        await update.message.reply_text(text[:4000], parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"⚠️ Gagal membuat briefing: {exc}")

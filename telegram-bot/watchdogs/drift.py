from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from infra.auth import ALLOWED_USERS, authorized
from infra.ssh import get_ssh_targets

logger = logging.getLogger(__name__)

DRIFT_CHECK_ENABLED = os.getenv("DRIFT_CHECK_ENABLED", "true").lower() in ("1", "true", "yes")
DRIFT_CHECK_HOUR = int(os.getenv("DRIFT_CHECK_HOUR", "2"))
DRIFT_CHECK_MINUTE = int(os.getenv("DRIFT_CHECK_MINUTE", "0"))

_EXPECTED_CONTAINERS: dict[str, str | None] = {
    "n8n": "n8nio/n8n:2.20.7",
    "langgraph-agent": None,
    "calcom": "calcom/cal.com:latest",
    "telegram-bot": None,
    "prometheus": "prom/prometheus:v3.4.0",
    "alertmanager": "prom/alertmanager:v0.28.1",
    "caddy": "caddy:2-alpine",
}

_EXPECTED_CRON_PATTERNS = [
    "health_check",
    "backup",
    "sync_vault",
]


async def check_docker_drift() -> list[str]:
    findings: list[str] = []
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
    except Exception:
        return ["❌ Cannot run docker ps locally"]

    running: dict[str, str] = {}
    for line in stdout.decode().strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            running[parts[0]] = parts[1]

    for name, expected_image in _EXPECTED_CONTAINERS.items():
        if name not in running:
            findings.append(f"🔴 <b>{name}</b> NOT RUNNING (expected)")
            continue
        if expected_image:
            actual = running[name].split("@")[0]
            if not actual.startswith(expected_image):
                findings.append(
                    f"⚠️ <b>{name}</b> image drift: expected <code>{expected_image}</code>, "
                    f"actual <code>{actual}</code>"
                )

    for name in running:
        if name not in _EXPECTED_CONTAINERS:
            findings.append(f"❓ <b>{name}</b> unexpected container running")

    return findings


async def check_cron_drift() -> list[str]:
    findings: list[str] = []
    try:
        proc = await asyncio.create_subprocess_exec(
            "bash", "-c", "crontab -l 2>/dev/null || echo ''",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
    except Exception:
        return ["⚠️ Cannot read crontab"]

    cron_content = stdout.decode()
    for pattern in _EXPECTED_CRON_PATTERNS:
        if pattern not in cron_content:
            findings.append(f"⚠️ Cron entry missing: <code>{pattern}</code>")

    return findings


async def check_remote_docker_drift(vps_name: str) -> list[str]:
    from bot import _ssh_docker_ps

    containers = await _ssh_docker_ps(vps_name)
    if containers is None:
        return [f"❌ SSH to <b>{vps_name}</b> failed — cannot check drift"]
    if not containers:
        return [f"⚠️ <b>{vps_name}</b> has 0 containers running"]
    down = [c for c in containers if "Up" not in c.get("status", "")]
    findings: list[str] = []
    for c in down:
        findings.append(f"🔴 <b>{vps_name}/{c['name']}</b> not running ({c.get('status', '?')})")
    return findings


async def run_drift_check() -> str:
    sections: list[str] = []
    sections.append("🔍 <b>Config Drift Report</b>")
    sections.append("")

    docker_findings = await check_docker_drift()
    cron_findings = await check_cron_drift()

    remote_findings: list[str] = []
    for vps_name in get_ssh_targets():
        remote_findings.extend(await check_remote_docker_drift(vps_name))

    all_findings = docker_findings + cron_findings + remote_findings

    if not all_findings:
        sections.append("✅ No drift detected — all configs match expected state.")
    else:
        sections.append(f"⚠️ {len(all_findings)} finding(s):")
        sections.append("")
        sections.extend(all_findings)

    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    sections.append(f"\n<i>{now.strftime('%A, %d %B %Y %H:%M')} WIB</i>")
    return "\n".join(sections)


async def drift_check_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id:
        return

    try:
        report = await run_drift_check()
        if "No drift detected" not in report:
            await context.bot.send_message(
                chat_id=chat_id,
                text=report[:4000],
                parse_mode="HTML",
            )
            logger.info("Drift check: findings reported")
        else:
            logger.info("Drift check: clean, no notification sent")
    except Exception as e:
        logger.error(f"Drift check job failed: {e}")


@authorized
async def cmd_drift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔍 Running drift check...")
    try:
        report = await run_drift_check()
        await update.message.reply_text(report[:4000], parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"⚠️ Drift check failed: {exc}")

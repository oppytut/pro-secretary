from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from infra.auth import ALLOWED_USERS, authorized
from infra.ssh import get_ssh_targets, ssh_exec

logger = logging.getLogger(__name__)

DOCKER_HYGIENE_ENABLED = os.getenv("DOCKER_HYGIENE_ENABLED", "true").lower() in ("1", "true", "yes")
DOCKER_HYGIENE_HOUR = int(os.getenv("DOCKER_HYGIENE_HOUR", "2"))
DOCKER_HYGIENE_MINUTE = int(os.getenv("DOCKER_HYGIENE_MINUTE", "15"))
DOCKER_HYGIENE_RECLAIMABLE_WARN_GB = float(os.getenv("DOCKER_HYGIENE_RECLAIMABLE_WARN_GB", "5"))
DOCKER_HYGIENE_AUTO_PRUNE = os.getenv("DOCKER_HYGIENE_AUTO_PRUNE", "true").lower() in ("1", "true", "yes")


def _docker_size_to_gb(size_str: str) -> float:
    if not size_str:
        return 0.0
    s = size_str.strip().upper().replace("B", "").strip()
    try:
        if s.endswith("K"):
            return float(s[:-1]) / (1024 * 1024)
        if s.endswith("M"):
            return float(s[:-1]) / 1024
        if s.endswith("G"):
            return float(s[:-1])
        if s.endswith("T"):
            return float(s[:-1]) * 1024
        return float(s) / (1024 * 1024 * 1024)
    except ValueError:
        return 0.0


def parse_docker_df(output: str) -> dict[str, dict[str, float]]:
    parsed: dict[str, dict[str, float]] = {}
    for line in output.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("TYPE"):
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        type_name = parts[0].strip()
        try:
            total = int(parts[1].strip())
        except ValueError:
            total = 0
        size_str = parts[3].strip()
        reclaim_str = parts[4].split("(")[0].strip()
        parsed[type_name] = {
            "total": total,
            "size_gb": _docker_size_to_gb(size_str),
            "reclaimable_gb": _docker_size_to_gb(reclaim_str),
        }
    return parsed


async def docker_df_local() -> dict[str, dict[str, float]] | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "system", "df", "--format",
            "{{.Type}}\t{{.TotalCount}}\t{{.Active}}\t{{.Size}}\t{{.Reclaimable}}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return parse_docker_df(stdout.decode())


async def docker_df_remote(vps_name: str) -> dict[str, dict[str, float]] | None:
    ok, output = await ssh_exec(
        vps_name,
        "docker system df --format '{{.Type}}\t{{.TotalCount}}\t{{.Active}}\t{{.Size}}\t{{.Reclaimable}}'",
    )
    if not ok or not output:
        return None
    return parse_docker_df(output)


async def docker_prune_local() -> tuple[bool, str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "image", "prune", "-f",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
    except Exception as e:
        return False, str(e)
    if proc.returncode != 0:
        return False, (stderr or b"").decode().strip()[:200]
    return True, stdout.decode().strip().split("\n")[-1][:120]


async def docker_prune_remote(vps_name: str) -> tuple[bool, str]:
    ok, output = await ssh_exec(vps_name, "docker image prune -f")
    if not ok:
        return False, output[:200]
    last_line = output.strip().split("\n")[-1] if output else ""
    return True, last_line[:120]


def _format_hygiene_section(label: str, df: dict[str, dict[str, float]]) -> tuple[list[str], float]:
    lines: list[str] = []
    total_reclaimable = 0.0
    for type_name in ("Images", "Containers", "Local Volumes", "Build Cache"):
        info = df.get(type_name)
        if not info:
            continue
        size = info["size_gb"]
        reclaim = info["reclaimable_gb"]
        total_reclaimable += reclaim
        lines.append(
            f"   • {type_name}: {size:.2f} GB total, {reclaim:.2f} GB reclaimable ({int(info['total'])})"
        )
    return lines, total_reclaimable


async def run_docker_hygiene(auto_prune: bool = False) -> tuple[str, bool]:
    sections: list[str] = ["🧹 <b>Docker Image Hygiene</b>", ""]
    has_warning = False
    targets: list[tuple[str, str]] = [("pro-secretary", "local")]
    for vps_name in get_ssh_targets():
        targets.append((vps_name, "remote"))

    for name, kind in targets:
        df = await (docker_df_local() if kind == "local" else docker_df_remote(name))
        if df is None:
            sections.append(f"❌ <b>{name}</b> — cannot read docker system df")
            has_warning = True
            sections.append("")
            continue

        body, reclaimable = _format_hygiene_section(name, df)
        threshold_breached = reclaimable >= DOCKER_HYGIENE_RECLAIMABLE_WARN_GB
        badge = "⚠️" if threshold_breached else "✅"
        sections.append(f"{badge} <b>{name}</b> — {reclaimable:.2f} GB reclaimable")
        sections.extend(body)

        if auto_prune and threshold_breached and DOCKER_HYGIENE_AUTO_PRUNE:
            ok, msg = await (docker_prune_local() if kind == "local" else docker_prune_remote(name))
            if ok:
                sections.append(f"   🔧 Pruned dangling images: {msg}")
            else:
                sections.append(f"   ❌ Prune failed: {msg}")

        if threshold_breached:
            has_warning = True
        sections.append("")

    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    sections.append(f"<i>{now.strftime('%A, %d %B %Y %H:%M')} WIB</i>")
    return "\n".join(sections).rstrip(), has_warning


async def docker_hygiene_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id:
        return
    try:
        report, has_warning = await run_docker_hygiene(auto_prune=True)
        if has_warning:
            await context.bot.send_message(
                chat_id=chat_id,
                text=report[:4000],
                parse_mode="HTML",
            )
            logger.info("Docker hygiene: warnings reported")
        else:
            logger.info("Docker hygiene: clean")
    except Exception as e:
        logger.error(f"Docker hygiene job failed: {e}")


@authorized
async def cmd_hygiene(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🧹 Running Docker hygiene check...")
    try:
        report, _ = await run_docker_hygiene(auto_prune=False)
        await update.message.reply_text(report[:4000], parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"⚠️ Hygiene check failed: {exc}")

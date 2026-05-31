from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from infra.auth import ALLOWED_USERS, authorized
from infra.prom import prom_query

logger = logging.getLogger(__name__)

CAPACITY_CHECK_ENABLED = os.getenv("CAPACITY_CHECK_ENABLED", "true").lower() in ("1", "true", "yes")
CAPACITY_CHECK_HOUR = int(os.getenv("CAPACITY_CHECK_HOUR", "2"))
CAPACITY_CHECK_MINUTE = int(os.getenv("CAPACITY_CHECK_MINUTE", "10"))
CAPACITY_WARN_DAYS = int(os.getenv("CAPACITY_WARN_DAYS", "14"))


async def run_capacity_check() -> str:
    sections: list[str] = ["📈 <b>Capacity Planning Report</b>", ""]
    warnings: list[str] = []
    ok_list: list[str] = []
    horizon_sec = CAPACITY_WARN_DAYS * 86400

    disk_query = (
        f'predict_linear(node_filesystem_avail_bytes{{fstype=~"ext4|xfs",mountpoint="/"}}[7d], {horizon_sec})'
    )
    disk_results = await prom_query(disk_query)
    if disk_results:
        for r in disk_results:
            name = r.get("metric", {}).get("instance_name", r.get("metric", {}).get("instance", "?"))
            predicted_avail = float(r["value"][1])
            if predicted_avail < 0:
                current_q = f'node_filesystem_avail_bytes{{fstype=~"ext4|xfs",mountpoint="/",instance_name="{name}"}}'
                current_res = await prom_query(current_q)
                current_avail_gb = 0.0
                if current_res:
                    current_avail_gb = float(current_res[0]["value"][1]) / (1024**3)
                rate_q = f'rate(node_filesystem_avail_bytes{{fstype=~"ext4|xfs",mountpoint="/",instance_name="{name}"}}[7d])'
                rate_res = await prom_query(rate_q)
                days_left = "?"
                if rate_res:
                    rate_per_sec = float(rate_res[0]["value"][1])
                    if rate_per_sec < 0 and current_res:
                        secs_left = abs(float(current_res[0]["value"][1]) / rate_per_sec)
                        days_left = f"{secs_left / 86400:.0f}"
                warnings.append(
                    f"🔴 <b>{name}</b> disk exhaustion ~{days_left} hari "
                    f"(sisa {current_avail_gb:.1f} GB)"
                )
            else:
                predicted_gb = predicted_avail / (1024**3)
                ok_list.append(f"✅ <b>{name}</b> disk OK — predicted {predicted_gb:.1f} GB free in {CAPACITY_WARN_DAYS}d")

    ram_query = (
        f'predict_linear(node_memory_MemAvailable_bytes[7d], {horizon_sec})'
    )
    ram_results = await prom_query(ram_query)
    if ram_results:
        for r in ram_results:
            name = r.get("metric", {}).get("instance_name", r.get("metric", {}).get("instance", "?"))
            predicted_avail = float(r["value"][1])
            if predicted_avail < 0:
                current_q = f'node_memory_MemAvailable_bytes{{instance_name="{name}"}}'
                current_res = await prom_query(current_q)
                current_avail_gb = 0.0
                if current_res:
                    current_avail_gb = float(current_res[0]["value"][1]) / (1024**3)
                total_q = f'node_memory_MemTotal_bytes{{instance_name="{name}"}}'
                total_res = await prom_query(total_q)
                total_gb = 0.0
                if total_res:
                    total_gb = float(total_res[0]["value"][1]) / (1024**3)
                rate_q = f'rate(node_memory_MemAvailable_bytes{{instance_name="{name}"}}[7d])'
                rate_res = await prom_query(rate_q)
                days_left = "?"
                if rate_res:
                    rate_per_sec = float(rate_res[0]["value"][1])
                    if rate_per_sec < 0 and current_res:
                        secs_left = abs(float(current_res[0]["value"][1]) / rate_per_sec)
                        days_left = f"{secs_left / 86400:.0f}"
                warnings.append(
                    f"⚠️ <b>{name}</b> RAM exhaustion ~{days_left} hari "
                    f"(sisa {current_avail_gb:.1f}/{total_gb:.1f} GB)"
                )
            else:
                predicted_gb = predicted_avail / (1024**3)
                ok_list.append(f"✅ <b>{name}</b> RAM OK — predicted {predicted_gb:.1f} GB free in {CAPACITY_WARN_DAYS}d")

    usage_q = '(1 - node_filesystem_avail_bytes{fstype=~"ext4|xfs",mountpoint="/"} / node_filesystem_size_bytes{fstype=~"ext4|xfs",mountpoint="/"}) * 100'
    usage_res = await prom_query(usage_q)
    ram_usage_q = '(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100'
    ram_usage_res = await prom_query(ram_usage_q)

    if not disk_results and not ram_results:
        sections.append("⚠️ No Prometheus data available — ensure targets are scraped with 7+ days of history.")
    else:
        if warnings:
            sections.append(f"🚨 <b>{len(warnings)} warning(s):</b>")
            sections.append("")
            sections.extend(warnings)
            sections.append("")
        if ok_list:
            sections.extend(ok_list)
            sections.append("")

        if usage_res or ram_usage_res:
            sections.append("<b>Current Usage:</b>")
            if usage_res:
                for r in usage_res:
                    name = r.get("metric", {}).get("instance_name", r.get("metric", {}).get("instance", "?"))
                    pct = float(r["value"][1])
                    sections.append(f"  💾 {name} disk: {pct:.1f}%")
            if ram_usage_res:
                for r in ram_usage_res:
                    name = r.get("metric", {}).get("instance_name", r.get("metric", {}).get("instance", "?"))
                    pct = float(r["value"][1])
                    sections.append(f"  🧠 {name} RAM: {pct:.1f}%")

    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    sections.append(f"\n<i>Forecast window: {CAPACITY_WARN_DAYS} days | {now.strftime('%A, %d %B %Y %H:%M')} WIB</i>")
    return "\n".join(sections)


async def capacity_check_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id:
        return

    try:
        report = await run_capacity_check()
        has_warning = "🔴" in report or "⚠️" in report
        if has_warning:
            await context.bot.send_message(
                chat_id=chat_id,
                text=report[:4000],
                parse_mode="HTML",
            )
            logger.info("Capacity check: warnings reported")
        else:
            logger.info("Capacity check: all OK, no notification sent")
    except Exception as e:
        logger.error(f"Capacity check job failed: {e}")


@authorized
async def cmd_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📈 Running capacity forecast...")
    try:
        report = await run_capacity_check()
        await update.message.reply_text(report[:4000], parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"⚠️ Capacity check failed: {exc}")

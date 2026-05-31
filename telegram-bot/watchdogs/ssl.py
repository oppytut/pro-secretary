from __future__ import annotations

import asyncio
import logging
import os
import socket
import ssl
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from infra.auth import ALLOWED_USERS, authorized
from infra.config_store import config_get, config_set

logger = logging.getLogger(__name__)

_SSL_ENV_DOMAINS = [d.strip() for d in os.getenv("SSL_CHECK_DOMAINS", "").split(",") if d.strip()]
SSL_WARN_DAYS = int(os.getenv("SSL_WARN_DAYS", "30"))
SSL_CHECK_ENABLED = os.getenv("SSL_CHECK_ENABLED", "true").lower() in ("1", "true", "yes")


def get_ssl_domains() -> list[str]:
    stored = config_get("ssl_domains", [])
    merged = list(dict.fromkeys(stored + _SSL_ENV_DOMAINS))
    return merged


def add_ssl_domain(domain: str) -> bool:
    domains = config_get("ssl_domains", [])
    if domain in domains:
        return False
    domains.append(domain)
    config_set("ssl_domains", domains)
    return True


def del_ssl_domain(domain: str) -> bool:
    domains = config_get("ssl_domains", [])
    if domain not in domains:
        return False
    domains.remove(domain)
    config_set("ssl_domains", domains)
    return True


async def check_ssl_expiry(domain: str) -> dict:
    def _get_cert_expiry(host: str) -> tuple[int, str]:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
            s.settimeout(10)
            s.connect((host, 443))
            cert = s.getpeercert()
        expiry_str = cert["notAfter"]
        expiry_dt = parsedate_to_datetime(str(expiry_str))
        days_left = (expiry_dt - datetime.now(timezone.utc)).days
        return days_left, expiry_dt.strftime("%Y-%m-%d")

    try:
        days_left, expiry = await asyncio.to_thread(_get_cert_expiry, domain)
        return {"domain": domain, "days_left": days_left, "expiry": expiry, "error": None}
    except Exception as e:
        return {"domain": domain, "days_left": -1, "expiry": None, "error": str(e)}


async def run_ssl_check() -> str:
    domains = get_ssl_domains()
    if not domains:
        return "⚠️ No domains configured. Use <code>/ssl add domain.com</code> or set <code>SSL_CHECK_DOMAINS</code> env var."

    sections: list[str] = []
    sections.append("🔒 <b>SSL/Domain Watchdog</b>")
    sections.append("")

    warnings: list[str] = []
    ok_list: list[str] = []

    for domain in domains:
        result = await check_ssl_expiry(domain)
        if result["error"]:
            warnings.append(f"❌ <b>{domain}</b> — cannot check: {result['error']}")
        elif result["days_left"] <= 0:
            warnings.append(f"🔴 <b>{domain}</b> — EXPIRED ({result['expiry']})")
        elif result["days_left"] <= SSL_WARN_DAYS:
            warnings.append(f"⚠️ <b>{domain}</b> — expires in {result['days_left']}d ({result['expiry']})")
        else:
            ok_list.append(f"✅ <b>{domain}</b> — {result['days_left']}d left ({result['expiry']})")

    if warnings:
        sections.extend(warnings)
        sections.append("")
    sections.extend(ok_list)

    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    sections.append(f"\n<i>{now.strftime('%A, %d %B %Y %H:%M')} WIB</i>")
    return "\n".join(sections)


async def ssl_check_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id or not get_ssl_domains():
        return

    try:
        report = await run_ssl_check()
        has_warning = "⚠️" in report or "🔴" in report or "❌" in report
        if has_warning:
            await context.bot.send_message(
                chat_id=chat_id,
                text=report[:4000],
                parse_mode="HTML",
            )
            logger.info("SSL check: warnings reported")
        else:
            logger.info("SSL check: all certs OK")
    except Exception as e:
        logger.error(f"SSL check job failed: {e}")


@authorized
async def cmd_ssl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []

    if not args:
        await update.message.reply_text("🔒 Checking SSL certificates...")
        try:
            report = await run_ssl_check()
            await update.message.reply_text(report[:4000], parse_mode="HTML")
        except Exception as exc:
            await update.message.reply_text(f"⚠️ SSL check failed: {exc}")
        return

    action = args[0].lower()

    if action == "list":
        domains = get_ssl_domains()
        if not domains:
            await update.message.reply_text("📋 No SSL domains configured.")
        else:
            lines = ["🔒 <b>SSL Domains</b>", ""]
            for d in domains:
                lines.append(f"• <code>{d}</code>")
            await update.message.reply_text("\n".join(lines), parse_mode="HTML")

    elif action == "add" and len(args) >= 2:
        domain = args[1].lower().strip()
        if add_ssl_domain(domain):
            await update.message.reply_text(f"✅ Added <code>{domain}</code> to SSL watchlist.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"ℹ️ <code>{domain}</code> already in watchlist.", parse_mode="HTML")

    elif action in ("del", "remove") and len(args) >= 2:
        domain = args[1].lower().strip()
        if del_ssl_domain(domain):
            await update.message.reply_text(f"✅ Removed <code>{domain}</code> from SSL watchlist.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"ℹ️ <code>{domain}</code> not in watchlist.", parse_mode="HTML")

    else:
        await update.message.reply_text(
            "Usage:\n/ssl — check all certs\n/ssl list — show domains\n"
            "/ssl add domain.com — add domain\n/ssl del domain.com — remove domain"
        )

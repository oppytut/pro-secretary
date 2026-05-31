from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from infra.auth import ALLOWED_USERS, authorized
from infra.config_store import config_get, config_set
from watchdogs.ssl import get_ssl_domains

logger = logging.getLogger(__name__)

DNS_CHECK_ENABLED = os.getenv("DNS_CHECK_ENABLED", "true").lower() in ("1", "true", "yes")
DNS_CHECK_INTERVAL_SEC = int(os.getenv("DNS_CHECK_INTERVAL_SEC", "14400"))
_DNS_RESOLVERS: list[tuple[str, str]] = [
    ("Cloudflare", "1.1.1.1"),
    ("Google", "8.8.8.8"),
    ("Quad9", "9.9.9.9"),
]


def get_dns_domains() -> list[str]:
    stored = config_get("dns_domains", None)
    if stored is not None:
        return list(stored)
    return list(get_ssl_domains())


def add_dns_domain(domain: str) -> bool:
    domains = config_get("dns_domains", None)
    domains = list(domains) if domains is not None else list(get_ssl_domains())
    if domain in domains:
        return False
    domains.append(domain)
    config_set("dns_domains", domains)
    return True


def del_dns_domain(domain: str) -> bool:
    domains = config_get("dns_domains", None)
    domains = list(domains) if domains is not None else list(get_ssl_domains())
    if domain not in domains:
        return False
    domains.remove(domain)
    config_set("dns_domains", domains)
    return True


async def dig_record(
    domain: str, resolver: str, rtype: str = "A"
) -> tuple[list[str], str | None]:
    cmd = [
        "dig", f"@{resolver}", "+short", "+time=5", "+tries=1", "+retry=0",
        domain, rtype,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=12)
    except asyncio.TimeoutError:
        return [], "timeout"
    except FileNotFoundError:
        return [], "dig binary not installed"
    except Exception as e:
        return [], type(e).__name__
    if proc.returncode != 0:
        err = (stderr or b"").decode().strip()
        return [], err.split("\n")[0][:80] or f"exit {proc.returncode}"
    records = [
        r.strip() for r in stdout.decode().splitlines()
        if r.strip() and not r.startswith(";")
    ]
    return sorted(records), None


async def check_domain_consistency(domain: str) -> dict[str, Any]:
    results: dict[str, dict[str, Any]] = {}
    for label, resolver in _DNS_RESOLVERS:
        records, err = await dig_record(domain, resolver, "A")
        results[label] = {"records": records, "error": err}
    record_sets = {tuple(r["records"]) for r in results.values() if not r["error"] and r["records"]}
    return {
        "domain": domain,
        "consistent": len(record_sets) <= 1,
        "results": results,
        "any_error": any(r["error"] for r in results.values()),
        "any_empty": any(not r["records"] and not r["error"] for r in results.values()),
        "record_sets": [list(rs) for rs in record_sets],
    }


async def run_dns_check() -> str:
    domains = get_dns_domains()
    if not domains:
        return (
            "⚠️ No DNS domains configured. Use <code>/dns add domain.com</code> "
            "or set <code>SSL_CHECK_DOMAINS</code> (DNS reuses SSL list as seed)."
        )
    sections: list[str] = ["🌐 <b>DNS Health Monitor</b>", ""]
    warnings: list[str] = []
    ok_list: list[str] = []

    for domain in domains:
        result = await check_domain_consistency(domain)
        if result["any_error"]:
            errs = [f"{label}={r['error']}" for label, r in result["results"].items() if r["error"]]
            warnings.append(f"❌ <b>{domain}</b> — resolver error: {', '.join(errs)}")
        elif result["any_empty"]:
            empties = [label for label, r in result["results"].items() if not r["records"]]
            warnings.append(f"⚠️ <b>{domain}</b> — empty response from: {', '.join(empties)}")
        elif not result["consistent"]:
            div_lines = []
            for label, r in result["results"].items():
                div_lines.append(f"      {label}: {', '.join(r['records']) or '(empty)'}")
            warnings.append(
                f"🔴 <b>{domain}</b> — divergent across resolvers:\n" + "\n".join(div_lines)
            )
        else:
            sample = next(iter(result["results"].values()))
            ips = ", ".join(sample["records"])
            ok_list.append(f"✅ <b>{domain}</b> → <code>{ips}</code>")

    if warnings:
        sections.extend(warnings)
        sections.append("")
    sections.extend(ok_list)
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    sections.append(f"\n<i>{now.strftime('%A, %d %B %Y %H:%M')} WIB</i>")
    return "\n".join(sections)


async def dns_check_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id or not get_dns_domains():
        return
    try:
        report = await run_dns_check()
        if "🔴" in report or "❌" in report or "⚠️" in report:
            await context.bot.send_message(
                chat_id=chat_id,
                text=report[:4000],
                parse_mode="HTML",
            )
            logger.info("DNS check: warnings reported")
        else:
            logger.info("DNS check: all consistent")
    except Exception as e:
        logger.error(f"DNS check job failed: {e}")


@authorized
async def cmd_dns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args:
        await update.message.reply_text("🌐 Checking DNS health...")
        try:
            report = await run_dns_check()
            await update.message.reply_text(report[:4000], parse_mode="HTML")
        except Exception as exc:
            await update.message.reply_text(f"⚠️ DNS check failed: {exc}")
        return

    action = args[0].lower()
    if action == "list":
        domains = get_dns_domains()
        if not domains:
            await update.message.reply_text("📋 No DNS domains configured.")
        else:
            lines = ["🌐 <b>DNS Domains</b>", ""]
            for d in domains:
                lines.append(f"• <code>{d}</code>")
            await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    elif action == "add" and len(args) >= 2:
        domain = args[1].lower().strip()
        if add_dns_domain(domain):
            await update.message.reply_text(f"✅ Added <code>{domain}</code> to DNS watchlist.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"ℹ️ <code>{domain}</code> already in watchlist.", parse_mode="HTML")
    elif action in ("del", "remove") and len(args) >= 2:
        domain = args[1].lower().strip()
        if del_dns_domain(domain):
            await update.message.reply_text(f"✅ Removed <code>{domain}</code> from DNS watchlist.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"ℹ️ <code>{domain}</code> not in watchlist.", parse_mode="HTML")
    else:
        await update.message.reply_text(
            "Usage:\n/dns — check all domains\n/dns list — show domains\n"
            "/dns add domain.com — add domain\n/dns del domain.com — remove domain"
        )

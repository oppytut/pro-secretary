from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from infra.auth import ALLOWED_USERS, authorized
from infra.config_store import config_get, config_set
from infra.ssh import get_ssh_targets, ssh_exec

logger = logging.getLogger(__name__)

FIREWALL_AUDIT_ENABLED = os.getenv("FIREWALL_AUDIT_ENABLED", "true").lower() in ("1", "true", "yes")
FIREWALL_AUDIT_HOUR = int(os.getenv("FIREWALL_AUDIT_HOUR", "3"))
FIREWALL_AUDIT_MINUTE = int(os.getenv("FIREWALL_AUDIT_MINUTE", "30"))

_FIREWALL_DEFAULT_WHITELIST = {22, 80, 443}
_FIREWALL_PROBE_CMD = (
    "ss -H -tlnp 2>/dev/null || ss -H -tln 2>/dev/null || "
    "netstat -tln 2>/dev/null | tail -n +3"
)


def get_firewall_whitelist(vps_name: str) -> set[int]:
    raw = config_get("firewall_whitelist", {}) or {}
    ports = raw.get(vps_name)
    if ports is None:
        return set(_FIREWALL_DEFAULT_WHITELIST)
    return {int(p) for p in ports}


def set_firewall_whitelist(vps_name: str, ports: set[int]) -> None:
    raw = config_get("firewall_whitelist", {}) or {}
    raw[vps_name] = sorted(ports)
    config_set("firewall_whitelist", raw)


def add_firewall_port(vps_name: str, port: int) -> bool:
    ports = get_firewall_whitelist(vps_name)
    if port in ports:
        return False
    ports.add(port)
    set_firewall_whitelist(vps_name, ports)
    return True


def del_firewall_port(vps_name: str, port: int) -> bool:
    ports = get_firewall_whitelist(vps_name)
    if port not in ports:
        return False
    ports.discard(port)
    set_firewall_whitelist(vps_name, ports)
    return True


def parse_listening_ports(ss_output: str) -> list[dict[str, str]]:
    listeners: list[dict[str, str]] = []
    for raw in ss_output.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        local = parts[3] if "tcp" not in parts[0].lower() else parts[3]
        if ":" not in local:
            continue
        addr, _, port_str = local.rpartition(":")
        try:
            port = int(port_str)
        except ValueError:
            continue
        bind = addr.strip("[]") or "0.0.0.0"
        public = bind in ("0.0.0.0", "::", "*")
        proc_info = ""
        for tok in parts[4:]:
            if tok.startswith("users:"):
                proc_info = tok
                break
        listeners.append({
            "port": str(port),
            "bind": bind,
            "public": "yes" if public else "no",
            "process": proc_info,
        })
    return listeners


async def audit_vps_firewall(vps_name: str) -> dict[str, Any]:
    ok, output = await ssh_exec(vps_name, _FIREWALL_PROBE_CMD)
    if not ok:
        return {"vps": vps_name, "error": output or "ssh failed", "findings": []}
    listeners = parse_listening_ports(output)
    whitelist = get_firewall_whitelist(vps_name)
    findings: list[dict[str, str]] = []
    for entry in listeners:
        if entry["public"] != "yes":
            continue
        port_int = int(entry["port"])
        if port_int in whitelist:
            continue
        findings.append(entry)
    return {
        "vps": vps_name,
        "error": None,
        "listeners": listeners,
        "findings": findings,
        "whitelist": sorted(whitelist),
    }


async def run_firewall_audit() -> tuple[str, bool]:
    targets = get_ssh_targets()
    if not targets:
        return ("ℹ️ No VPS targets configured. Use <code>/monitor add ...</code>", False)

    sections: list[str] = ["🛡️ <b>Firewall Audit</b>", ""]
    has_warning = False
    for vps_name in targets:
        result = await audit_vps_firewall(vps_name)
        if result["error"]:
            sections.append(f"❌ <b>{vps_name}</b> — {result['error']}")
            has_warning = True
            sections.append("")
            continue

        wl = ", ".join(str(p) for p in result["whitelist"]) or "(empty)"
        if not result["findings"]:
            sections.append(f"✅ <b>{vps_name}</b> — no unauthorized public ports (whitelist: {wl})")
        else:
            has_warning = True
            sections.append(
                f"🔴 <b>{vps_name}</b> — {len(result['findings'])} unauthorized public port(s)"
            )
            sections.append(f"   whitelist: {wl}")
            for entry in result["findings"][:10]:
                proc = f" {entry['process']}" if entry["process"] else ""
                sections.append(
                    f"   • port <code>{entry['port']}</code> bound to <code>{entry['bind']}</code>{proc}"
                )
        sections.append("")

    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    sections.append(f"<i>{now.strftime('%A, %d %B %Y %H:%M')} WIB</i>")
    return "\n".join(sections).rstrip(), has_warning


async def firewall_audit_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = ALLOWED_USERS[0] if ALLOWED_USERS else None
    if not chat_id or not get_ssh_targets():
        return
    try:
        report, has_warning = await run_firewall_audit()
        if has_warning:
            await context.bot.send_message(
                chat_id=chat_id,
                text=report[:4000],
                parse_mode="HTML",
            )
            logger.info("Firewall audit: findings reported")
        else:
            logger.info("Firewall audit: clean")
    except Exception as e:
        logger.error(f"Firewall audit job failed: {e}")


@authorized
async def cmd_firewall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args:
        await update.message.reply_text("🛡️ Running firewall audit...")
        try:
            report, _ = await run_firewall_audit()
            await update.message.reply_text(report[:4000], parse_mode="HTML")
        except Exception as exc:
            await update.message.reply_text(f"⚠️ Firewall audit failed: {exc}")
        return

    action = args[0].lower()
    if action == "list":
        targets = get_ssh_targets()
        if not targets:
            await update.message.reply_text("📋 No VPS targets configured.")
            return
        lines = ["🛡️ <b>Firewall Whitelist</b>", ""]
        for vps_name in targets:
            ports = sorted(get_firewall_whitelist(vps_name))
            lines.append(f"• <b>{vps_name}</b>: {', '.join(str(p) for p in ports) or '(empty)'}")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return

    if action == "add" and len(args) >= 3:
        vps_name = args[1]
        try:
            port = int(args[2])
        except ValueError:
            await update.message.reply_text("⚠️ Port must be a number.")
            return
        if vps_name not in get_ssh_targets():
            await update.message.reply_text(f"⚠️ Unknown VPS <code>{vps_name}</code>.", parse_mode="HTML")
            return
        if add_firewall_port(vps_name, port):
            await update.message.reply_text(
                f"✅ Added port <code>{port}</code> to <b>{vps_name}</b> whitelist.",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(
                f"ℹ️ Port <code>{port}</code> already in <b>{vps_name}</b> whitelist.",
                parse_mode="HTML",
            )
        return

    if action in ("del", "remove") and len(args) >= 3:
        vps_name = args[1]
        try:
            port = int(args[2])
        except ValueError:
            await update.message.reply_text("⚠️ Port must be a number.")
            return
        if del_firewall_port(vps_name, port):
            await update.message.reply_text(
                f"✅ Removed port <code>{port}</code> from <b>{vps_name}</b> whitelist.",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(
                f"ℹ️ Port <code>{port}</code> not in <b>{vps_name}</b> whitelist.",
                parse_mode="HTML",
            )
        return

    await update.message.reply_text(
        "Usage:\n/firewall — audit all VPS\n/firewall list — show whitelist per VPS\n"
        "/firewall add <vps> <port> — allow public port\n"
        "/firewall del <vps> <port> — remove from whitelist"
    )

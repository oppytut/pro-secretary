from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config, qdrant_helper, telegram, vps_status


def _level(value: float | None, warn: float, crit: float) -> str:
    if value is None:
        return "unknown"
    if value >= crit:
        return "critical"
    if value >= warn:
        return "warning"
    return "ok"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


async def run_check() -> dict[str, Any]:
    previous = _load_state(config.RESOURCE_ALERT_STATE_FILE)
    host_payload = await vps_status.collect_all()
    states: dict[str, dict[str, Any]] = {}

    mem_pct = host_payload.get("host", {}).get("mem_pct")
    states["memory"] = _evaluate_memory(mem_pct, previous.get("memory") or {})

    states["swap"] = _evaluate_swap(host_payload.get("host", {}))

    for disk in host_payload.get("disks", []):
        if not disk.get("ok"):
            continue
        path = disk.get("path", "disk")
        pct = disk.get("pct")
        states[f"disk:{path}"] = {
            "level": _level(pct, config.RESOURCE_DISK_WARN_PCT, config.RESOURCE_DISK_CRIT_PCT),
            "value": pct,
            "detail": f"Disk {path} {pct}%" if pct is not None else f"Disk {path} unknown",
        }

    states["qdrant_connectivity"] = await _check_qdrant_connectivity()
    states["qdrant_code_chunks"] = await _check_qdrant_capacity()
    states["postgres"] = await _check_postgres()

    alerts = _transition_alerts(previous, states)
    if alerts:
        await telegram.send_message("\n".join(alerts))
    _save_state(config.RESOURCE_ALERT_STATE_FILE, states)
    return {"ok": True, "alerts_sent": len(alerts), "states": states}


def _evaluate_memory(mem_pct: float | None, prev: dict[str, Any]) -> dict[str, Any]:
    """RAM alert with sustained window: only fires after the breach lasts
    RESOURCE_MEM_SUSTAINED_MINUTES. Spikes shorter than the window are ignored."""
    if mem_pct is None:
        return {"level": "unknown", "value": None, "detail": "RAM unknown"}

    raw_level = _level(mem_pct, config.RESOURCE_MEM_WARN_PCT, config.RESOURCE_MEM_CRIT_PCT)
    sustained_seconds = max(0, config.RESOURCE_MEM_SUSTAINED_MINUTES) * 60
    breach_started = _parse_iso(prev.get("breach_started_at"))
    now = datetime.now(timezone.utc)

    if raw_level == "ok":
        return {
            "level": "ok",
            "value": mem_pct,
            "detail": f"RAM {mem_pct}%",
            "breach_started_at": None,
        }

    if breach_started is None:
        breach_started = now

    elapsed = (now - breach_started).total_seconds()
    if elapsed < sustained_seconds:
        return {
            "level": "ok",
            "value": mem_pct,
            "detail": (
                f"RAM {mem_pct}% (sustaining {int(elapsed / 60)}/"
                f"{config.RESOURCE_MEM_SUSTAINED_MINUTES} min)"
            ),
            "breach_started_at": breach_started.isoformat(),
        }

    return {
        "level": raw_level,
        "value": mem_pct,
        "detail": f"RAM {mem_pct}% sustained {int(elapsed / 60)} min",
        "breach_started_at": breach_started.isoformat(),
    }


def _evaluate_swap(host_metrics: dict[str, Any]) -> dict[str, Any]:
    swap_total = host_metrics.get("swap_total_bytes") or 0
    swap_used = host_metrics.get("swap_used_bytes") or 0
    if not swap_total:
        return {"level": "ok", "value": None, "detail": "Swap disabled"}
    pct = round(swap_used / swap_total * 100, 1)
    return {
        "level": _level(pct, config.RESOURCE_SWAP_WARN_PCT, config.RESOURCE_SWAP_CRIT_PCT),
        "value": pct,
        "detail": f"Swap {pct}%",
    }


async def _check_qdrant_connectivity() -> dict[str, Any]:
    if not config.QDRANT_URL or not config.QDRANT_API_KEY:
        return {"level": "unknown", "value": None, "detail": "Qdrant not configured"}
    try:
        client = qdrant_helper.get_client()
        collections = await asyncio.to_thread(lambda: client.get_collections().collections)
        return {
            "level": "ok",
            "value": len(collections),
            "detail": f"Qdrant reachable ({len(collections)} collections)",
        }
    except Exception as exc:
        return {
            "level": "critical",
            "value": None,
            "detail": f"Qdrant unreachable: {type(exc).__name__}",
        }


async def _check_qdrant_capacity() -> dict[str, Any]:
    try:
        code_points = await asyncio.to_thread(qdrant_helper.count, config.COLL_CODE)
        level = _level(
            float(code_points),
            float(config.RESOURCE_QDRANT_WARN_POINTS),
            float(config.RESOURCE_QDRANT_CRIT_POINTS),
        )
        return {
            "level": level,
            "value": code_points,
            "detail": f"Qdrant code_chunks {code_points} points",
        }
    except Exception as exc:
        return {
            "level": "unknown",
            "value": None,
            "detail": f"Qdrant count failed: {type(exc).__name__}",
        }


async def _check_postgres() -> dict[str, Any]:
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        return {"level": "unknown", "value": None, "detail": "DATABASE_URL not set"}

    timeout = max(1, int(config.RESOURCE_POSTGRES_CONNECT_TIMEOUT_SEC))

    def _probe() -> tuple[bool, str]:
        try:
            psycopg = __import__("psycopg")

            with psycopg.connect(db_url, connect_timeout=timeout) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True, "ok"
        except Exception as exc:
            return False, type(exc).__name__

    ok, detail = await asyncio.to_thread(_probe)
    if ok:
        return {"level": "ok", "value": None, "detail": "PostgreSQL reachable"}
    return {
        "level": "critical",
        "value": None,
        "detail": f"PostgreSQL unreachable: {detail}",
    }


def _transition_alerts(
    previous: dict[str, Any], current: dict[str, dict[str, Any]]
) -> list[str]:
    messages: list[str] = []
    for key, state in current.items():
        old_level = (previous.get(key) or {}).get("level", "ok")
        new_level = state.get("level", "unknown")
        if new_level == old_level or new_level == "unknown":
            continue
        detail = state.get("detail", key)
        if new_level == "ok":
            messages.append(f"✅ RESOURCE RECOVERED: {detail}")
        elif new_level == "warning":
            messages.append(f"⚠️ RESOURCE WARNING: {detail}")
        elif new_level == "critical":
            messages.append(f"🚨 RESOURCE CRITICAL: {detail}")
    return messages


def _load_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(path: Path, state: dict[str, dict[str, Any]]) -> None:
    timestamp = _now_iso()
    payload = {
        key: {**value, "checked_at": timestamp} for key, value in state.items()
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

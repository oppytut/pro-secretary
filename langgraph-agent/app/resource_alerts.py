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


def _format_bytes(b: int | float) -> str:
    """Human-readable byte size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}PB"


_RECOMMENDATIONS: dict[str, dict[str, str]] = {
    "memory": {
        "warning": "Consider upgrading VPS RAM or reducing container memory limits.",
        "critical": "VPS RAM critically low. Upgrade RAM or stop non-essential containers.",
    },
    "swap": {
        "warning": "High swap = RAM pressure. Monitor for sustained usage.",
        "critical": "Swap critically high. Upgrade VPS RAM to avoid OOM kills.",
    },
    "disk": {
        "warning": "Disk filling up. Clean old logs/backups or expand storage.",
        "critical": "Disk nearly full. Immediate cleanup or expansion needed.",
    },
    "qdrant_connectivity": {
        "critical": "Check Qdrant Cloud status: https://cloud.qdrant.io",
    },
    "qdrant_code_chunks": {
        "warning": "Approaching Qdrant free tier limit (1M vectors). Consider Starter plan ($25/mo).",
        "critical": "Near Qdrant free tier cap. Upgrade to Starter or prune old collections.",
    },
    "postgres": {
        "critical": "Check PostgreSQL provider status page. Verify DATABASE_URL and network.",
    },
    "postgres_storage": {
        "warning": "Database storage growing. Monitor growth rate.",
        "critical": "Database near storage limit. Upgrade plan or clean old data.",
    },
    "container": {
        "warning": "Container near memory limit. Risk of OOM kill.",
        "critical": "Container at memory limit. Increase limit or optimize usage.",
    },
}


def _get_recommendation(resource_key: str, level: str) -> str:
    """Get actionable recommendation for a resource alert."""
    # Normalize key: disk:/path → disk, container:name → container
    base_key = resource_key
    if resource_key.startswith("disk:"):
        base_key = "disk"
    elif resource_key.startswith("container:"):
        base_key = "container"
    recs = _RECOMMENDATIONS.get(base_key, {})
    return recs.get(level, "")


async def run_check() -> dict[str, Any]:
    previous = _load_state(config.RESOURCE_ALERT_STATE_FILE)
    host_payload = await vps_status.collect_all()
    states: dict[str, dict[str, Any]] = {}

    mem_pct = host_payload.get("host", {}).get("mem_pct")
    mem_total = host_payload.get("host", {}).get("mem_total_bytes", 0)
    states["memory"] = _evaluate_memory(mem_pct, previous.get("memory") or {})
    if mem_total:
        states["memory"]["total_bytes"] = mem_total

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

    for container in host_payload.get("containers", []):
        if not container.get("ok"):
            continue
        name = container.get("name", "unknown")
        c_mem_pct = container.get("mem_pct")
        if c_mem_pct is not None:
            c_level = _level(
                c_mem_pct,
                config.RESOURCE_CONTAINER_MEM_WARN_PCT,
                config.RESOURCE_CONTAINER_MEM_CRIT_PCT,
            )
            c_used = container.get("mem_used_bytes", 0)
            c_limit = container.get("mem_limit_bytes", 0)
            states[f"container:{name}"] = {
                "level": c_level,
                "value": c_mem_pct,
                "detail": (
                    f"Container {name} {c_mem_pct}% mem "
                    f"({_format_bytes(c_used)}/{_format_bytes(c_limit)})"
                ),
            }

    states["qdrant_connectivity"] = await _check_qdrant_connectivity()
    states["qdrant_code_chunks"] = await _check_qdrant_capacity()
    states["postgres"] = await _check_postgres()
    states["postgres_storage"] = await _check_postgres_storage()

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


async def _check_postgres_storage() -> dict[str, Any]:
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        return {"level": "unknown", "value": None, "detail": "DATABASE_URL not set"}
    if not config.RESOURCE_POSTGRES_STORAGE_WARN_MB:
        return {"level": "ok", "value": None, "detail": "PostgreSQL storage check disabled"}

    timeout = max(1, int(config.RESOURCE_POSTGRES_CONNECT_TIMEOUT_SEC))

    def _probe_size() -> tuple[int | None, str]:
        try:
            psycopg = __import__("psycopg")
            with psycopg.connect(db_url, connect_timeout=timeout) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_database_size(current_database())")
                    row = cur.fetchone()
                    return row[0] if row else None, "ok"
        except Exception as exc:
            return None, type(exc).__name__

    size_bytes, err = await asyncio.to_thread(_probe_size)
    if size_bytes is None:
        return {"level": "unknown", "value": None, "detail": f"pg_database_size failed: {err}"}

    size_mb = size_bytes / (1024 * 1024)
    level = _level(
        size_mb,
        float(config.RESOURCE_POSTGRES_STORAGE_WARN_MB),
        float(config.RESOURCE_POSTGRES_STORAGE_CRIT_MB),
    )
    return {
        "level": level,
        "value": round(size_mb, 1),
        "detail": f"PostgreSQL {_format_bytes(size_bytes)}",
    }


def _transition_alerts(
    previous: dict[str, Any], current: dict[str, dict[str, Any]]
) -> list[str]:
    messages: list[str] = []
    now = datetime.now(timezone.utc)
    for key, state in current.items():
        prev_state = previous.get(key) or {}
        old_level = prev_state.get("level", "ok")
        new_level = state.get("level", "unknown")
        if new_level == old_level or new_level == "unknown":
            continue
        detail = state.get("detail", key)
        if new_level == "ok":
            duration_str = _recovery_duration(prev_state, now)
            messages.append(f"✅ RESOURCE RECOVERED: {detail}{duration_str}")
        elif new_level == "warning":
            rec = _get_recommendation(key, "warning")
            suffix = f"\n   💡 {rec}" if rec else ""
            messages.append(f"⚠️ RESOURCE WARNING: {detail}{suffix}")
        elif new_level == "critical":
            rec = _get_recommendation(key, "critical")
            suffix = f"\n   💡 {rec}" if rec else ""
            messages.append(f"🚨 RESOURCE CRITICAL: {detail}{suffix}")
    return messages


def _recovery_duration(prev_state: dict[str, Any], now: datetime) -> str:
    alert_at = _parse_iso(prev_state.get("alerted_at") or prev_state.get("checked_at"))
    if not alert_at:
        return ""
    elapsed = (now - alert_at).total_seconds()
    if elapsed < 60:
        return ""
    minutes = int(elapsed / 60)
    if minutes < 60:
        return f" (was alerting for {minutes} min)"
    hours = minutes // 60
    remaining_min = minutes % 60
    return f" (was alerting for {hours}h{remaining_min}m)"


def _load_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(path: Path, state: dict[str, dict[str, Any]]) -> None:
    timestamp = _now_iso()
    payload: dict[str, Any] = {}
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    for key, value in state.items():
        entry = {**value, "checked_at": timestamp}
        old_entry = old.get(key) or {}
        if value.get("level") in ("warning", "critical"):
            entry["alerted_at"] = old_entry.get("alerted_at") or timestamp
        else:
            entry.pop("alerted_at", None)
        payload[key] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

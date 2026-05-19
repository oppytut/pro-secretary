from __future__ import annotations

import json
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


async def run_check() -> dict[str, Any]:
    host = await vps_status.collect_all()
    states: dict[str, dict[str, Any]] = {}

    mem_pct = host.get("host", {}).get("mem_pct")
    states["memory"] = {
        "level": _level(mem_pct, config.RESOURCE_MEM_WARN_PCT, config.RESOURCE_MEM_CRIT_PCT),
        "value": mem_pct,
        "detail": f"RAM {mem_pct}%" if mem_pct is not None else "RAM unknown",
    }

    disk_levels: list[tuple[str, str, float | None]] = []
    for disk in host.get("disks", []):
        if not disk.get("ok"):
            continue
        pct = disk.get("pct")
        disk_levels.append((disk.get("path", "disk"), _level(pct, config.RESOURCE_DISK_WARN_PCT, config.RESOURCE_DISK_CRIT_PCT), pct))
    worst_disk = _worst(disk_levels)
    if worst_disk:
        path, level, pct = worst_disk
        states["disk"] = {"level": level, "value": pct, "detail": f"Disk {path} {pct}%"}

    try:
        code_points = qdrant_helper.count(config.COLL_CODE)
        q_level = _level(
            float(code_points),
            float(config.RESOURCE_QDRANT_WARN_POINTS),
            float(config.RESOURCE_QDRANT_CRIT_POINTS),
        )
        states["qdrant_code_chunks"] = {
            "level": q_level,
            "value": code_points,
            "detail": f"Qdrant code_chunks {code_points} points",
        }
    except Exception as exc:
        states["qdrant_code_chunks"] = {
            "level": "unknown",
            "value": None,
            "detail": f"Qdrant count failed: {type(exc).__name__}",
        }

    previous = _load_state(config.RESOURCE_ALERT_STATE_FILE)
    alerts = _transition_alerts(previous, states)
    if alerts:
        await telegram.send_message("\n".join(alerts))
    _save_state(config.RESOURCE_ALERT_STATE_FILE, states)
    return {"ok": True, "alerts_sent": len(alerts), "states": states}


def _worst(items: list[tuple[str, str, float | None]]) -> tuple[str, str, float | None] | None:
    order = {"unknown": 0, "ok": 1, "warning": 2, "critical": 3}
    if not items:
        return None
    return max(items, key=lambda item: order[item[1]])


def _transition_alerts(previous: dict[str, Any], current: dict[str, dict[str, Any]]) -> list[str]:
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


def _save_state(path: Path, state: dict[str, Any]) -> None:
    payload = {
        key: {**value, "checked_at": datetime.now(timezone.utc).isoformat()}
        for key, value in state.items()
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

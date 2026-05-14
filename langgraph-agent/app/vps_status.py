from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import httpx

HOST_PROC = Path("/host/proc")
DOCKER_SOCK = "/var/run/docker.sock"


def _read_proc(name: str) -> str:
    path = HOST_PROC / name
    if not path.exists():
        path = Path("/proc") / name
    return path.read_text()


def _parse_meminfo() -> dict[str, int]:
    data: dict[str, int] = {}
    try:
        for line in _read_proc("meminfo").splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].endswith(":"):
                data[parts[0][:-1]] = int(parts[1]) * 1024
    except (OSError, ValueError):
        pass
    return data


def _read_loadavg() -> tuple[float, float, float] | None:
    try:
        parts = _read_proc("loadavg").split()
        return float(parts[0]), float(parts[1]), float(parts[2])
    except (OSError, ValueError, IndexError):
        return None


def _read_uptime_seconds() -> float | None:
    try:
        return float(_read_proc("uptime").split()[0])
    except (OSError, ValueError, IndexError):
        return None


def _read_cpu_snapshot() -> tuple[int, int] | None:
    try:
        line = _read_proc("stat").splitlines()[0]
        fields = [int(x) for x in line.split()[1:]]
        idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
        total = sum(fields)
        return total, idle
    except (OSError, ValueError, IndexError):
        return None


def host_metrics() -> dict[str, Any]:
    mem = _parse_meminfo()
    mem_total = mem.get("MemTotal", 0)
    mem_avail = mem.get("MemAvailable", mem.get("MemFree", 0))
    mem_used = max(0, mem_total - mem_avail)
    swap_total = mem.get("SwapTotal", 0)
    swap_free = mem.get("SwapFree", 0)
    swap_used = max(0, swap_total - swap_free)

    snap1 = _read_cpu_snapshot()
    if snap1:
        time.sleep(0.5)
        snap2 = _read_cpu_snapshot()
    else:
        snap2 = None

    cpu_pct = None
    if snap1 and snap2:
        total_diff = snap2[0] - snap1[0]
        idle_diff = snap2[1] - snap1[1]
        if total_diff > 0:
            cpu_pct = round((1 - idle_diff / total_diff) * 100, 1)

    load = _read_loadavg()
    uptime = _read_uptime_seconds()

    return {
        "cpu_pct": cpu_pct,
        "load": list(load) if load else None,
        "mem_total_bytes": mem_total,
        "mem_used_bytes": mem_used,
        "mem_pct": round(mem_used / mem_total * 100, 1) if mem_total else None,
        "swap_total_bytes": swap_total,
        "swap_used_bytes": swap_used,
        "uptime_seconds": uptime,
    }


def disk_usage(paths: list[str]) -> list[dict[str, Any]]:
    import shutil

    out: list[dict[str, Any]] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            out.append({"path": p, "ok": False, "detail": "missing"})
            continue
        try:
            usage = shutil.disk_usage(p)
            out.append(
                {
                    "path": p,
                    "ok": True,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "pct": round(usage.used / usage.total * 100, 1),
                }
            )
        except OSError as exc:
            out.append({"path": p, "ok": False, "detail": type(exc).__name__})
    return out


async def container_stats() -> list[dict[str, Any]]:
    if not Path(DOCKER_SOCK).exists():
        return []

    transport = httpx.AsyncHTTPTransport(uds=DOCKER_SOCK)
    results: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://docker", timeout=10.0) as client:
            r = await client.get("/v1.41/containers/json", params={"all": "false"})
            if r.status_code != 200:
                return []
            containers = r.json()

            async def _stats_one(c: dict) -> dict[str, Any]:
                cid = c["Id"]
                name = c["Names"][0].lstrip("/") if c.get("Names") else cid[:12]
                try:
                    rs = await client.get(f"/v1.41/containers/{cid}/stats", params={"stream": "false"})
                    if rs.status_code != 200:
                        return {"name": name, "ok": False, "detail": f"HTTP {rs.status_code}"}
                    s = rs.json()
                except (httpx.RequestError, ValueError) as exc:
                    return {"name": name, "ok": False, "detail": type(exc).__name__}

                cpu_pct = None
                try:
                    cpu_total = s["cpu_stats"]["cpu_usage"]["total_usage"]
                    cpu_pre = s["precpu_stats"]["cpu_usage"]["total_usage"]
                    sys_total = s["cpu_stats"]["system_cpu_usage"]
                    sys_pre = s["precpu_stats"]["system_cpu_usage"]
                    online_cpus = s["cpu_stats"].get("online_cpus") or len(
                        s["cpu_stats"]["cpu_usage"].get("percpu_usage") or [1]
                    )
                    cpu_diff = cpu_total - cpu_pre
                    sys_diff = sys_total - sys_pre
                    if sys_diff > 0 and cpu_diff > 0:
                        cpu_pct = round(cpu_diff / sys_diff * online_cpus * 100, 1)
                except (KeyError, TypeError):
                    pass

                mem_used = s.get("memory_stats", {}).get("usage", 0)
                mem_limit = s.get("memory_stats", {}).get("limit", 0)
                cache = (s.get("memory_stats", {}).get("stats") or {}).get("cache", 0)
                mem_used_no_cache = max(0, mem_used - cache)

                return {
                    "name": name,
                    "ok": True,
                    "cpu_pct": cpu_pct,
                    "mem_used_bytes": mem_used_no_cache,
                    "mem_limit_bytes": mem_limit,
                    "mem_pct": round(mem_used_no_cache / mem_limit * 100, 1) if mem_limit else None,
                }

            results = await asyncio.gather(*[_stats_one(c) for c in containers])
    except (httpx.RequestError, OSError):
        return []

    results.sort(key=lambda x: x.get("mem_used_bytes", 0), reverse=True)
    return results


async def collect_all() -> dict[str, Any]:
    host = await asyncio.to_thread(host_metrics)
    disks = await asyncio.to_thread(disk_usage, ["/", "/var/backups", "/host/var/backups"])
    containers = await container_stats()
    return {
        "host": host,
        "disks": disks,
        "containers": containers,
    }

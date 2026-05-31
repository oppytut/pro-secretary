from __future__ import annotations

import asyncio
import json
import logging
import os

from infra.config_store import config_get, config_set

logger = logging.getLogger(__name__)

_env_targets: dict[str, dict[str, str]] = {}
_raw_ssh = os.getenv("MONITOR_SSH_TARGETS", "")
if _raw_ssh:
    try:
        _env_targets = json.loads(_raw_ssh)
    except Exception:
        pass


def get_ssh_targets() -> dict[str, dict[str, str]]:
    merged = dict(_env_targets)
    stored = config_get("ssh_targets", {})
    merged.update(stored)
    return merged


def add_ssh_target(name: str, host: str, port: str = "22", user: str = "root") -> bool:
    targets = config_get("ssh_targets", {})
    targets[name] = {"host": host, "port": port, "user": user}
    config_set("ssh_targets", targets)
    return True


def del_ssh_target(name: str) -> bool:
    targets = config_get("ssh_targets", {})
    if name not in targets:
        return False
    del targets[name]
    config_set("ssh_targets", targets)
    return True


async def ssh_exec(vps_name: str, command: str) -> tuple[bool, str]:
    target = get_ssh_targets().get(vps_name)
    if not target:
        return False, f"No SSH target for {vps_name}"
    host = target.get("host", "")
    port = str(target.get("port", 22))
    user = target.get("user", "root")
    cmd = [
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
        "-o", "StrictHostKeyChecking=accept-new", "-p", port,
        f"{user}@{host}", command,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = (stdout or stderr).decode().strip()
        return proc.returncode == 0, output
    except asyncio.TimeoutError:
        return False, "SSH command timed out"
    except Exception as e:
        return False, str(e)

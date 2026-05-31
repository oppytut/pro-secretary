from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import config

logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", "/vault"))
JOURNAL_SUBDIR = "journal"
MAX_ENTRY_LEN = 5000


def _journal_dir() -> Path:
    return VAULT_PATH / JOURNAL_SUBDIR


def _entry_path(now_local: datetime) -> Path:
    return _journal_dir() / f"{now_local.strftime('%Y-%m')}.md"


def _ensure_header(path: Path, now_local: datetime) -> None:
    if path.exists():
        return
    title = now_local.strftime("# Journal %B %Y\n\n")
    path.write_text(title, encoding="utf-8")


def append_entry(text: str, now: datetime | None = None) -> dict:
    text = (text or "").strip()
    if not text:
        return {"status_code": 400, "error": "empty entry"}
    if len(text) > MAX_ENTRY_LEN:
        return {
            "status_code": 400,
            "error": f"entry too long ({len(text)} chars, max {MAX_ENTRY_LEN})",
        }

    if not VAULT_PATH.exists():
        return {"status_code": 404, "error": f"vault path {VAULT_PATH} not found"}

    tz = ZoneInfo(config.TIMEZONE)
    now_local = (now or datetime.now(tz)).astimezone(tz)

    _journal_dir().mkdir(parents=True, exist_ok=True)
    path = _entry_path(now_local)
    _ensure_header(path, now_local)

    header = now_local.strftime("\n## %Y-%m-%d %H:%M %Z\n\n")
    block = header + text.rstrip() + "\n"

    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(block)
    except OSError as exc:
        logger.exception("journal append failed")
        return {"status_code": 500, "error": f"write failed: {exc}"}

    relative = str(path.relative_to(VAULT_PATH))
    return {
        "status_code": 200,
        "file": relative,
        "chars": len(text),
        "timestamp": now_local.isoformat(),
    }

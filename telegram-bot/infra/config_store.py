from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path("/app/data")
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_config(cfg: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def config_get(key: str, default: Any = None) -> Any:
    return _load_config().get(key, default)


def config_set(key: str, value: Any) -> None:
    cfg = _load_config()
    cfg[key] = value
    _save_config(cfg)

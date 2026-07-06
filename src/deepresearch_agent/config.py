from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_config(path: str | Path = "configs/default.toml") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    return tomllib.loads(config_path.read_text(encoding="utf-8"))


def config_get(config: dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    current: Any = config
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current

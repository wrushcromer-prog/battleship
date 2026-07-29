"""Persistent win/loss tally per opponent.

Streamlit Community Cloud has an ephemeral filesystem, so this tally resets when
the app is redeployed or the container is recycled.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_PATH = Path(os.environ.get("BATTLESHIP_RECORD_PATH", "data/records.json"))


def _read(path: Path) -> dict[str, dict[str, int]]:
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    records: dict[str, dict[str, int]] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            records[key] = {
                "wins": int(value.get("wins", 0)),
                "losses": int(value.get("losses", 0)),
            }
    return records


def load(path: Path = DEFAULT_PATH) -> dict[str, dict[str, int]]:
    return _read(path)


def record_for(key: str, path: Path = DEFAULT_PATH) -> dict[str, int]:
    return load(path).get(key, {"wins": 0, "losses": 0})


def add_result(key: str, won: bool, path: Path = DEFAULT_PATH) -> dict[str, int]:
    records = _read(path)
    entry = records.setdefault(key, {"wins": 0, "losses": 0})
    entry["wins" if won else "losses"] += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, sort_keys=True))
    return entry

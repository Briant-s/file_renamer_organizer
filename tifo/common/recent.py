"""Persistent store of recently used directories.

Plain logic, no UI dependency, so any frontend can reuse it. State lives in a
small JSON file under the user's config dir (XDG-aware on Linux), matching
TiFo's local-first design — nothing leaves the machine.

File shape::

    {"version": 1, "recent": [{"path": "/abs/path", "last_used": "<iso8601>"}]}

Entries are most-recent-first, de-duplicated by resolved path, and capped.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

MAX_RECENT = 10
_SCHEMA_VERSION = 1


def _config_dir() -> Path:
    """Return the TiFo config directory, honoring XDG_CONFIG_HOME."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "tifo"


def _store_path() -> Path:
    return _config_dir() / "recent.json"


def _read_raw() -> list[dict]:
    path = _store_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError, OSError):
        return []
    recent = data.get("recent") if isinstance(data, dict) else None
    if not isinstance(recent, list):
        return []
    # Keep only well-formed entries.
    return [e for e in recent if isinstance(e, dict) and e.get("path")]


def _write_raw(recent: list[dict]) -> None:
    path = _store_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": _SCHEMA_VERSION, "recent": recent[:MAX_RECENT]}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        # Persistence is best-effort; never crash the app over the recent list.
        pass


def load_recent(*, prune_missing: bool = True) -> list[str]:
    """Return recent directory paths, most-recent-first.

    With ``prune_missing`` (default), directories that no longer exist are
    dropped from both the returned list and the persisted file.
    """
    entries = _read_raw()
    if not prune_missing:
        return [e["path"] for e in entries]

    kept = [e for e in entries if Path(e["path"]).is_dir()]
    if len(kept) != len(entries):
        _write_raw(kept)
    return [e["path"] for e in kept]


def add_recent(path: str) -> list[str]:
    """Record ``path`` as most-recently-used and return the updated path list.

    Paths are resolved and de-duplicated case-sensitively by resolved string.
    Invalid / non-directory paths are ignored.
    """
    try:
        resolved = str(Path(path).expanduser().resolve())
    except (OSError, RuntimeError):
        return load_recent()

    if not Path(resolved).is_dir():
        return load_recent()

    entries = [e for e in _read_raw() if e.get("path") != resolved]
    entries.insert(0, {"path": resolved, "last_used": datetime.now().isoformat()})
    entries = entries[:MAX_RECENT]
    _write_raw(entries)
    return [e["path"] for e in entries]

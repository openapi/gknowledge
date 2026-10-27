"""Application-level state that lives outside any single project.

Currently just the list of recently opened projects, stored as JSON under the
XDG config dir so it works cleanly under Flatpak sandboxing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import APP_NAME


def _config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    d = Path(base) / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _state_path() -> Path:
    return _config_dir() / "state.json"


def load_state() -> dict:
    p = _state_path()
    if p.exists():
        try:
            return json.loads(p.read_text("utf-8"))
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    _state_path().write_text(json.dumps(state, indent=2), "utf-8")


def recent_projects() -> list[str]:
    return [p for p in load_state().get("recent", []) if Path(p).exists()]


def add_recent_project(path: str) -> None:
    state = load_state()
    recent = [p for p in state.get("recent", []) if p != path]
    recent.insert(0, path)
    state["recent"] = recent[:10]
    save_state(state)


def replace_recent_project(old: str, new: str) -> None:
    """A draft was saved elsewhere: its recent entry follows it."""
    state = load_state()
    state["recent"] = [p for p in state.get("recent", []) if p not in (old, new)]
    save_state(state)
    add_recent_project(new)

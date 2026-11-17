"""Project layer: the on-disk dossier format (see docs/dossier/SPEC.md).

A dossier is a folder whose visible content a person can read at a glance:
a launcher file that opens it, the evidence, the compiled knowledge and their
own notes. Everything that can be rebuilt, or belongs to one machine, is kept
out of sight in ``.dossier/``.

    <Name>/
      <Name>.dossier           # manifest; double-click opens the dossier
      sources/                 # imported raw files (immutable copies)
      knowledge/
        index.md               # catalog of pages
        log.md                 # human-readable operation log
        overview.md            # global summary (regenerated on ingest)
        sources/  entities/  concepts/  topics/  answers/  synthesis/
      notes/                   # user-authored notes
      .dossier/                # derived and local state, never shared
        index/knowledge.db     # SQLite store
        cache/                 # transient parse/analysis cache
        settings.json          # provider + app settings

Dossiers created before 0.4 use the legacy layout (``gknowledge.json``,
``index/``, ``cache/``, ``settings/`` at the root); they open unchanged.

A new dossier starts as a *draft*: it has a name and is fully usable, but it
lives in the user's data dir until it is saved to a real folder
(:meth:`Project.materialize`).
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .models import PageKind, new_id, now
from .store import Store

MANIFEST_SUFFIX = ".dossier"
LEGACY_MANIFEST = "gknowledge.json"
FORMAT_VERSION = "0.1"
STATE_DIR = ".dossier"
DEFAULT_HOME_NAME = "Dossiers"

KNOWLEDGE_SUBDIRS = {
    PageKind.SOURCE: "sources",
    PageKind.ENTITY: "entities",
    PageKind.CONCEPT: "concepts",
    PageKind.TOPIC: "topics",
    PageKind.ANSWER: "answers",
    PageKind.SYNTHESIS: "synthesis",
}


def find_manifest(root: str | Path) -> Path | None:
    """The manifest of the dossier at ``root``: ``*.dossier``, else legacy."""
    root = Path(root)
    if not root.is_dir():
        return None
    launchers = sorted(p for p in root.glob(f"*{MANIFEST_SUFFIX}") if p.is_file())
    if launchers:
        return launchers[0]
    legacy = root / LEGACY_MANIFEST
    return legacy if legacy.is_file() else None


def dossier_root(path: str | Path) -> Path:
    """Accept either the dossier folder or its launcher file."""
    path = Path(path)
    if path.is_file() and path.name.endswith((MANIFEST_SUFFIX, LEGACY_MANIFEST)):
        return path.parent
    return path


def safe_filename(name: str) -> str:
    """A folder/file name for ``name``: keeps spaces and accents, drops separators."""
    cleaned = re.sub(r'[/\\\x00-\x1f:*?"<>|]+', " ", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().strip(".")
    return cleaned[:120].strip() or "Untitled dossier"


def _xdg_documents_dir() -> Path:
    """The user's Documents folder, localised ("Documenti", "Dokumente", …)."""
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    try:
        for line in (config / "user-dirs.dirs").read_text("utf-8").splitlines():
            m = re.match(r'\s*XDG_DOCUMENTS_DIR\s*=\s*"(.*)"\s*$', line)
            if m:
                value = m.group(1).replace("$HOME", str(home))
                if value and Path(value) != home:
                    return Path(value)
    except OSError:
        pass
    return home / "Documents"


def default_home() -> Path:
    """Where new dossiers are saved by default: ``~/Documents/Dossiers``.

    ``GKNOWLEDGE_DOSSIER_HOME`` overrides it (tests, sandboxes).
    """
    override = os.environ.get("GKNOWLEDGE_DOSSIER_HOME")
    if override:
        return Path(override)
    return _xdg_documents_dir() / DEFAULT_HOME_NAME


def drafts_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "gknowledge" / "drafts"


def unique_path(path: Path) -> Path:
    """``path``, or ``path (2)``, ``path (3)``… if it already exists."""
    if not path.exists():
        return path
    n = 2
    while True:
        candidate = path.with_name(f"{path.name} ({n})")
        if not candidate.exists():
            return candidate
        n += 1


@dataclass
class Settings:
    provider: str = "offline"          # offline | chatgpt | openai | custom | ollama
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    embed_model: str = ""
    language: str = "English"

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Settings":
        known = {k: d[k] for k in cls().as_dict() if k in d}
        return cls(**known)


class Project:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        manifest = find_manifest(self.root)
        self.legacy = manifest is not None and manifest.name == LEGACY_MANIFEST
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.store = Store(self.index_dir / "knowledge.db")
        self._settings = self._load_settings()

    # -- lifecycle -----------------------------------------------------------
    @classmethod
    def create(cls, root: str | Path, name: str = "") -> "Project":
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        name = name or root.name
        for sub in ("sources", "knowledge", "notes",
                    f"{STATE_DIR}/index", f"{STATE_DIR}/cache"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        for sub in KNOWLEDGE_SUBDIRS.values():
            (root / "knowledge" / sub).mkdir(exist_ok=True)
        manifest = {
            "dossier": FORMAT_VERSION,
            "id": new_id(),
            "name": name,
            "created": _rfc3339(now()),
        }
        (root / f"{safe_filename(name)}{MANIFEST_SUFFIX}").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", "utf-8")
        gitignore = root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(f"{STATE_DIR}/\n", "utf-8")
        proj = cls(root)
        # Seed the three navigation entry-point files.
        for fname, header in (
            ("index.md", f"# {name} — Knowledge Index\n\n_No pages yet._\n"),
            ("log.md", f"# Operation Log\n\n"),
            ("overview.md", f"# Overview\n\n_The overview is generated as sources are ingested._\n"),
        ):
            fp = root / "knowledge" / fname
            if not fp.exists():
                fp.write_text(header, "utf-8")
        proj.store.log("project.create", name)
        return proj

    @classmethod
    def create_draft(cls, name: str) -> "Project":
        """A named, usable dossier that has no folder of its own yet."""
        return cls.create(drafts_dir() / new_id(), name=name)

    @classmethod
    def open(cls, root: str | Path) -> "Project":
        root = dossier_root(root)
        if find_manifest(root) is None:
            raise FileNotFoundError(f"Not a dossier: {root}")
        return cls(root)

    @staticmethod
    def is_project(root: str | Path) -> bool:
        return find_manifest(dossier_root(root)) is not None

    def close(self) -> None:
        self.store.close()

    # -- drafts --------------------------------------------------------------
    @property
    def is_draft(self) -> bool:
        return self.root.resolve().parent == drafts_dir().resolve()

    def suggested_folder(self, parent: str | Path | None = None) -> Path:
        """Where :meth:`materialize` would put this dossier inside ``parent``."""
        parent = Path(parent) if parent else default_home()
        return unique_path(parent / safe_filename(self.name))

    def materialize(self, dest: str | Path) -> "Project":
        """Move a draft to ``dest`` (which must not exist) and reopen it there.

        The draft is moved, not copied, so nothing is left behind; this
        object is closed and the reopened dossier is returned.
        """
        dest = Path(dest)
        if dest.exists():
            raise FileExistsError(f"{dest} already exists")
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.store.log("project.save", str(dest))
        self.close()
        shutil.move(str(self.root), str(dest))
        return type(self).open(dest)

    # -- paths ---------------------------------------------------------------
    @property
    def manifest_path(self) -> Path:
        return find_manifest(self.root) or self.root / LEGACY_MANIFEST

    @property
    def sources_dir(self) -> Path:
        return self.root / "sources"

    @property
    def knowledge_dir(self) -> Path:
        return self.root / "knowledge"

    @property
    def state_dir(self) -> Path:
        return self.root if self.legacy else self.root / STATE_DIR

    @property
    def index_dir(self) -> Path:
        return self.state_dir / "index"

    @property
    def cache_dir(self) -> Path:
        return self.state_dir / "cache"

    def knowledge_subdir(self, kind: PageKind) -> Path:
        return self.knowledge_dir / KNOWLEDGE_SUBDIRS.get(kind, "concepts")

    # -- manifest / settings -------------------------------------------------
    @property
    def name(self) -> str:
        try:
            return json.loads(self.manifest_path.read_text("utf-8")).get(
                "name", self.root.name
            )
        except Exception:
            return self.root.name

    @property
    def settings(self) -> Settings:
        return self._settings

    def _settings_path(self) -> Path:
        if self.legacy:
            return self.root / "settings" / "settings.json"
        return self.state_dir / "settings.json"

    def _load_settings(self) -> Settings:
        p = self._settings_path()
        if p.exists():
            try:
                return Settings.from_dict(json.loads(p.read_text("utf-8")))
            except Exception:
                pass
        return Settings()

    def save_settings(self, settings: Settings) -> None:
        self._settings = settings
        self._settings_path().parent.mkdir(exist_ok=True)
        self._settings_path().write_text(
            json.dumps(settings.as_dict(), indent=2), "utf-8"
        )
        self.store.log("settings.save", settings.provider)


def _rfc3339(ts: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

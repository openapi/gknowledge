"""Wiki lint: find knowledge that no longer matches its sources.

A generated wiki rarely goes wrong because the model invented something; it
goes wrong because the source moved on and the page did not. Every source
keeps the SHA-256 of the file it was ingested from and every page keeps the
ids of the sources behind it, so drift is a hash comparison, not a guess.

Only the stale-source check lives here for now; orphan pages, broken
``[[links]]`` and duplicate titles belong in this module too.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .hashing import hash_file
from .models import Page, Source, SourceStatus
from .project import Project


@dataclass
class StaleSource:
    source: Source
    pages: list[Page] = field(default_factory=list)  # pages that cite it


class ChangeDetector:
    """Compare each source's original file with the content that was ingested.

    Hashes are memoised by (path, size, mtime), so calling :meth:`stale_sources`
    on every refresh only re-reads files that were touched since the last call.
    """

    def __init__(self, project: Project):
        self.project = project
        self._memo: dict[tuple[str, int, int], str] = {}

    def current_hash(self, source: Source) -> str | None:
        """Hash of the original file now, or None if it is gone or unreadable."""
        if not source.origin_path:
            return None
        try:
            st = os.stat(source.origin_path)
        except OSError:
            return None
        key = (source.origin_path, st.st_size, st.st_mtime_ns)
        if key not in self._memo:
            try:
                self._memo[key] = hash_file(source.origin_path)
            except OSError:
                return None
        return self._memo[key]

    def is_stale(self, source: Source) -> bool:
        if source.status != SourceStatus.INGESTED:
            return False  # nothing generated from it yet
        digest = self.current_hash(source)
        return digest is not None and digest != source.sha256

    def stale_sources(self) -> list[StaleSource]:
        store = self.project.store
        return [StaleSource(s, store.pages_for_source(s.id))
                for s in store.list_sources() if self.is_stale(s)]


def stale_sources(project: Project) -> list[StaleSource]:
    return ChangeDetector(project).stale_sources()


def origin_of(source: Source) -> Path | None:
    path = Path(source.origin_path) if source.origin_path else None
    return path if path and path.is_file() else None

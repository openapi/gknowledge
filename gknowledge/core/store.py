"""SQLite-backed knowledge store.

The store is the durable index for a project. Generated *content* lives on
disk as Markdown (readable, exportable, Obsidian-friendly); the store keeps the
metadata, provenance, links, jobs, reviews and an operation log so the app can
query, resume, and recover without re-reading every file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .models import (
    Job,
    JobState,
    Link,
    Page,
    ReviewItem,
    ReviewStatus,
    Source,
    now,
)

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    title TEXT,
    rel_path TEXT,
    origin_path TEXT,
    sha256 TEXT,
    size INTEGER,
    mime TEXT,
    status TEXT,
    added_at REAL
);
CREATE TABLE IF NOT EXISTS pages (
    id TEXT PRIMARY KEY,
    kind TEXT,
    title TEXT,
    slug TEXT UNIQUE,
    rel_path TEXT,
    summary TEXT,
    sources TEXT,
    links TEXT,
    generated INTEGER,
    confidence REAL,
    created_at REAL,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS links (
    from_slug TEXT,
    to_slug TEXT,
    kind TEXT,
    weight REAL,
    PRIMARY KEY (from_slug, to_slug, kind)
);
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    title TEXT,
    detail TEXT,
    action TEXT,
    status TEXT,
    queries TEXT,
    source_id TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source_id TEXT,
    state TEXT,
    attempts INTEGER,
    error TEXT,
    created_at REAL,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL,
    op TEXT,
    detail TEXT
);
"""


class _Rows:
    """Materialised query result, safe to read after the lock is released."""

    def __init__(self, rows: list):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list:
        return list(self._rows)

    def __iter__(self):
        return iter(self._rows)


class _SharedConnection:
    """One SQLite connection usable from the UI thread and worker threads.

    Ingestion and queries run in background threads; every statement is
    serialised with a lock and results are fetched while holding it.
    """

    def __init__(self, path: str):
        import threading
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def execute(self, sql: str, params=()) -> _Rows:
        with self._lock:
            return _Rows(self._conn.execute(sql, params).fetchall())

    def executemany(self, sql: str, seq) -> None:
        with self._lock:
            self._conn.executemany(sql, seq)

    def executescript(self, sql: str) -> None:
        with self._lock:
            self._conn.executescript(sql)

    def commit(self) -> None:
        with self._lock:
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()


class Store:
    def __init__(self, db_path: str | Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = _SharedConnection(str(self.path))
        # No WAL: its shared-memory index needs mmap, which the Flatpak
        # document portal (projects picked with the file chooser) does not
        # support, so a WAL database there fails with "disk I/O error" even
        # to open. Exclusive locking lets SQLite read an older WAL database
        # without that index long enough to convert it.
        self._conn.execute("PRAGMA locking_mode=EXCLUSIVE")
        self._conn.execute("PRAGMA journal_mode=DELETE")
        self._conn.execute("PRAGMA locking_mode=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self) -> None:
        self._conn.executescript(_SCHEMA)
        cur = self._conn.execute("SELECT value FROM meta WHERE key='schema_version'")
        row = cur.fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO meta(key, value) VALUES('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- log -----------------------------------------------------------------
    def log(self, op: str, detail: str = "") -> None:
        self._conn.execute(
            "INSERT INTO log(ts, op, detail) VALUES(?,?,?)", (now(), op, detail)
        )
        self._conn.commit()

    def recent_log(self, limit: int = 100) -> list[sqlite3.Row]:
        cur = self._conn.execute(
            "SELECT ts, op, detail FROM log ORDER BY id DESC LIMIT ?", (limit,)
        )
        return cur.fetchall()

    # -- sources -------------------------------------------------------------
    def upsert_source(self, s: Source) -> None:
        r = s.to_row()
        self._conn.execute(
            """INSERT INTO sources(id,title,rel_path,origin_path,sha256,size,mime,status,added_at)
                 VALUES(:id,:title,:rel_path,:origin_path,:sha256,:size,:mime,:status,:added_at)
                 ON CONFLICT(id) DO UPDATE SET
                   title=:title, rel_path=:rel_path, origin_path=:origin_path,
                   sha256=:sha256, size=:size, mime=:mime, status=:status""",
            r,
        )
        self._conn.commit()

    def get_source(self, source_id: str) -> Source | None:
        cur = self._conn.execute("SELECT * FROM sources WHERE id=?", (source_id,))
        row = cur.fetchone()
        return Source.from_row(dict(row)) if row else None

    def source_by_hash(self, sha256: str) -> Source | None:
        cur = self._conn.execute("SELECT * FROM sources WHERE sha256=?", (sha256,))
        row = cur.fetchone()
        return Source.from_row(dict(row)) if row else None

    def list_sources(self) -> list[Source]:
        cur = self._conn.execute("SELECT * FROM sources ORDER BY added_at DESC")
        return [Source.from_row(dict(r)) for r in cur.fetchall()]

    def delete_source(self, source_id: str) -> None:
        self.delete_jobs_for_source(source_id)
        self.delete_reviews_for_source(source_id)
        self._conn.execute("DELETE FROM sources WHERE id=?", (source_id,))
        self._conn.commit()

    # -- pages ---------------------------------------------------------------
    def upsert_page(self, p: Page) -> None:
        r = p.to_row()
        self._conn.execute(
            """INSERT INTO pages(id,kind,title,slug,rel_path,summary,sources,links,
                                 generated,confidence,created_at,updated_at)
                 VALUES(:id,:kind,:title,:slug,:rel_path,:summary,:sources,:links,
                        :generated,:confidence,:created_at,:updated_at)
                 ON CONFLICT(slug) DO UPDATE SET
                   kind=:kind, title=:title, rel_path=:rel_path, summary=:summary,
                   sources=:sources, links=:links, generated=:generated,
                   confidence=:confidence, updated_at=:updated_at""",
            r,
        )
        self._conn.commit()

    def get_page(self, slug: str) -> Page | None:
        cur = self._conn.execute("SELECT * FROM pages WHERE slug=?", (slug,))
        row = cur.fetchone()
        return Page.from_row(dict(row)) if row else None

    def list_pages(self, kind: str | None = None) -> list[Page]:
        if kind:
            cur = self._conn.execute(
                "SELECT * FROM pages WHERE kind=? ORDER BY title", (kind,)
            )
        else:
            cur = self._conn.execute("SELECT * FROM pages ORDER BY kind, title")
        return [Page.from_row(dict(r)) for r in cur.fetchall()]

    def pages_for_source(self, source_id: str) -> list[Page]:
        return [p for p in self.list_pages() if source_id in p.sources]

    def delete_page(self, slug: str) -> None:
        self._conn.execute("DELETE FROM pages WHERE slug=?", (slug,))
        self._conn.execute(
            "DELETE FROM links WHERE from_slug=? OR to_slug=?", (slug, slug)
        )
        self._conn.commit()

    # -- links ---------------------------------------------------------------
    def set_links(self, from_slug: str, links: Iterable[Link]) -> None:
        self._conn.execute("DELETE FROM links WHERE from_slug=?", (from_slug,))
        self._conn.executemany(
            "INSERT OR REPLACE INTO links(from_slug,to_slug,kind,weight) VALUES(?,?,?,?)",
            [(l.from_slug, l.to_slug, l.kind, l.weight) for l in links],
        )
        self._conn.commit()

    def all_links(self) -> list[Link]:
        cur = self._conn.execute("SELECT from_slug,to_slug,kind,weight FROM links")
        return [Link(r["from_slug"], r["to_slug"], r["kind"], r["weight"]) for r in cur]

    def neighbours(self, slug: str) -> list[str]:
        cur = self._conn.execute(
            "SELECT to_slug AS s FROM links WHERE from_slug=? "
            "UNION SELECT from_slug AS s FROM links WHERE to_slug=?",
            (slug, slug),
        )
        return [r["s"] for r in cur.fetchall()]

    # -- reviews -------------------------------------------------------------
    def upsert_review(self, item: ReviewItem) -> None:
        r = item.to_row()
        self._conn.execute(
            """INSERT INTO reviews(id,title,detail,action,status,queries,source_id,created_at)
                 VALUES(:id,:title,:detail,:action,:status,:queries,:source_id,:created_at)
                 ON CONFLICT(id) DO UPDATE SET status=:status, detail=:detail""",
            r,
        )
        self._conn.commit()

    def delete_reviews_for_source(self, source_id: str) -> None:
        self._conn.execute("DELETE FROM reviews WHERE source_id=?", (source_id,))
        self._conn.commit()

    def list_reviews(self, status: str | None = None) -> list[ReviewItem]:
        if status:
            cur = self._conn.execute(
                "SELECT * FROM reviews WHERE status=? ORDER BY created_at DESC", (status,)
            )
        else:
            cur = self._conn.execute("SELECT * FROM reviews ORDER BY created_at DESC")
        return [ReviewItem.from_row(dict(r)) for r in cur.fetchall()]

    def resolve_review(self, review_id: str) -> None:
        self._conn.execute(
            "UPDATE reviews SET status=? WHERE id=?",
            (ReviewStatus.RESOLVED.value, review_id),
        )
        self._conn.commit()

    # -- jobs ----------------------------------------------------------------
    def upsert_job(self, j: Job) -> None:
        r = j.to_row()
        self._conn.execute(
            """INSERT INTO jobs(id,source_id,state,attempts,error,created_at,updated_at)
                 VALUES(:id,:source_id,:state,:attempts,:error,:created_at,:updated_at)
                 ON CONFLICT(id) DO UPDATE SET state=:state, attempts=:attempts,
                   error=:error, updated_at=:updated_at""",
            r,
        )
        self._conn.commit()

    def delete_jobs_for_source(self, source_id: str) -> None:
        self._conn.execute("DELETE FROM jobs WHERE source_id=?", (source_id,))
        self._conn.commit()

    def pending_jobs(self) -> list[Job]:
        cur = self._conn.execute(
            "SELECT * FROM jobs WHERE state IN (?,?) ORDER BY created_at",
            (JobState.QUEUED.value, JobState.RUNNING.value),
        )
        return [Job.from_row(dict(r)) for r in cur.fetchall()]

    def list_jobs(self) -> list[Job]:
        cur = self._conn.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        return [Job.from_row(dict(r)) for r in cur.fetchall()]

    def counts(self) -> dict[str, int]:
        c = {}
        for tbl in ("sources", "pages", "reviews"):
            c[tbl] = self._conn.execute(f"SELECT COUNT(*) AS n FROM {tbl}").fetchone()["n"]
        c["open_reviews"] = self._conn.execute(
            "SELECT COUNT(*) AS n FROM reviews WHERE status=?", (ReviewStatus.OPEN.value,)
        ).fetchone()["n"]
        return c

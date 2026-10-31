"""Domain models.

These dataclasses mirror the persisted records in the knowledge store and the
on-disk project layout. They intentionally separate the different kinds of
knowledge the README calls out: raw sources, extracted structure, generated
artifacts, and review tasks.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


def new_id() -> str:
    return uuid.uuid4().hex


def now() -> float:
    return time.time()


class SourceStatus(str, Enum):
    PENDING = "pending"      # imported, not yet processed
    PARSED = "parsed"        # text extracted
    INGESTED = "ingested"    # knowledge generated
    FAILED = "failed"


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"      # unchanged content, cache hit


class PageKind(str, Enum):
    SOURCE = "source"        # per-source summary
    ENTITY = "entity"        # people, orgs, products
    CONCEPT = "concept"      # theories, methods, techniques
    TOPIC = "topic"          # themes
    ANSWER = "answer"        # saved query answers
    SYNTHESIS = "synthesis"  # cross-source analysis


class ReviewAction(str, Enum):
    CREATE_PAGE = "create_page"
    DEEP_RESEARCH = "deep_research"
    SKIP = "skip"


class ReviewStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"


@dataclass
class Source:
    id: str = field(default_factory=new_id)
    title: str = ""
    rel_path: str = ""          # path inside <project>/sources
    origin_path: str = ""       # where it was imported from
    sha256: str = ""
    size: int = 0
    mime: str = "text/plain"
    status: SourceStatus = SourceStatus.PENDING
    added_at: float = field(default_factory=now)

    def to_row(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Source":
        row = dict(row)
        row["status"] = SourceStatus(row["status"])
        return cls(**row)


@dataclass
class Page:
    id: str = field(default_factory=new_id)
    kind: PageKind = PageKind.CONCEPT
    title: str = ""
    slug: str = ""
    rel_path: str = ""          # path inside <project>/knowledge
    summary: str = ""
    body: str = ""              # markdown body (not persisted to db, lives on disk)
    sources: list[str] = field(default_factory=list)   # source ids (provenance)
    links: list[str] = field(default_factory=list)      # slugs of linked pages
    generated: bool = True      # generated vs user-authored
    confidence: float = 1.0
    created_at: float = field(default_factory=now)
    updated_at: float = field(default_factory=now)

    def to_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "title": self.title,
            "slug": self.slug,
            "rel_path": self.rel_path,
            "summary": self.summary,
            "sources": ",".join(self.sources),
            "links": ",".join(self.links),
            "generated": 1 if self.generated else 0,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Page":
        return cls(
            id=row["id"],
            kind=PageKind(row["kind"]),
            title=row["title"],
            slug=row["slug"],
            rel_path=row["rel_path"],
            summary=row["summary"] or "",
            sources=[s for s in (row["sources"] or "").split(",") if s],
            links=[s for s in (row["links"] or "").split(",") if s],
            generated=bool(row["generated"]),
            confidence=row["confidence"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class Link:
    from_slug: str
    to_slug: str
    kind: str = "wikilink"
    weight: float = 1.0


@dataclass
class ReviewItem:
    id: str = field(default_factory=new_id)
    title: str = ""
    detail: str = ""
    action: ReviewAction = ReviewAction.CREATE_PAGE
    status: ReviewStatus = ReviewStatus.OPEN
    queries: list[str] = field(default_factory=list)
    source_id: str = ""
    created_at: float = field(default_factory=now)

    @property
    def is_question(self) -> bool:
        return self.action == ReviewAction.DEEP_RESEARCH

    def to_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "detail": self.detail,
            "action": self.action.value,
            "status": self.status.value,
            "queries": "\n".join(self.queries),
            "source_id": self.source_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ReviewItem":
        return cls(
            id=row["id"],
            title=row["title"],
            detail=row["detail"] or "",
            action=ReviewAction(row["action"]),
            status=ReviewStatus(row["status"]),
            queries=[q for q in (row["queries"] or "").split("\n") if q],
            source_id=row["source_id"] or "",
            created_at=row["created_at"],
        )


@dataclass
class Job:
    id: str = field(default_factory=new_id)
    source_id: str = ""
    state: JobState = JobState.QUEUED
    attempts: int = 0
    error: str = ""
    created_at: float = field(default_factory=now)
    updated_at: float = field(default_factory=now)

    def to_row(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Job":
        row = dict(row)
        row["state"] = JobState(row["state"])
        return cls(**row)

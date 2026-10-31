"""End-to-end tests for the headless core (no GTK, no network)."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gknowledge.core.ingestion import IngestionManager
from gknowledge.core.knowledge import KnowledgeWriter
from gknowledge.core.lint import ChangeDetector, stale_sources
from gknowledge.core.models import (
    Page, PageKind, ReviewAction, ReviewItem, Source, SourceStatus,
)
from gknowledge.core.project import Project, Settings
from gknowledge.core.query import QueryEngine
from gknowledge.providers import build_provider

SAMPLE = """# Solar Energy Basics

Photovoltaic cells convert sunlight into electricity. The efficiency of a
silicon solar panel depends on temperature and irradiance. Tesla and First
Solar manufacture large-scale installations. Grid integration remains a key
challenge for renewable energy adoption. Battery storage systems such as those
built by Tesla help balance intermittent generation across the electrical grid.
"""


def make_project(tmp: Path) -> Project:
    proj = Project.create(tmp / "proj", name="Test KB")
    proj.save_settings(Settings(provider="offline"))
    return proj


def test_review_items_separate_questions_from_review_tasks():
    question = ReviewItem(
        title="What caused the change?",
        action=ReviewAction.DEEP_RESEARCH,
        queries=["What caused the change?"],
    )
    review_task = ReviewItem(
        title="Check the proposed page",
        action=ReviewAction.CREATE_PAGE,
    )

    assert question.is_question
    assert not review_task.is_question


def _write_minimal_epub(path: Path, chapter: str) -> None:
    """Build the smallest epub a real reader would accept: no binary fixture."""
    container = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<container version="1.0" '
        'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    opf = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>Smoke Test</dc:title></metadata>'
        '<manifest><item id="c1" href="chapter1.xhtml" '
        'media-type="application/xhtml+xml"/></manifest>'
        '<spine><itemref idref="c1"/></spine></package>'
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip",
                    compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/chapter1.xhtml", chapter)


def test_project_layout(tmp_path):
    proj = make_project(tmp_path)
    assert Project.is_project(proj.root)
    assert (proj.root / "gknowledge.json").exists()
    assert (proj.knowledge_dir / "index.md").exists()
    assert (proj.knowledge_dir / "overview.md").exists()
    assert proj.name == "Test KB"
    # Reopen round-trips.
    proj.close()
    reopened = Project.open(proj.root)
    assert reopened.name == "Test KB"
    reopened.close()


def test_import_ingest_and_dedup(tmp_path):
    proj = make_project(tmp_path)
    src_file = tmp_path / "solar.md"
    src_file.write_text(SAMPLE, "utf-8")

    mgr = IngestionManager(proj, build_provider(proj.settings.as_dict()))
    source = mgr.import_file(src_file)
    assert source is not None
    # Duplicate content is skipped (cache-aware).
    assert mgr.import_file(src_file) is None

    done = mgr.process_pending()
    assert done == 1

    source = proj.store.get_source(source.id)
    assert source.status == SourceStatus.INGESTED

    pages = proj.store.list_pages()
    assert any(p.kind == PageKind.SOURCE for p in pages)
    assert any(p.kind == PageKind.ENTITY for p in pages)
    # Provenance: every generated page links back to a source id.
    assert all(p.sources for p in pages)

    # A source summary markdown file exists on disk with frontmatter.
    source_page = next(p for p in pages if p.kind == PageKind.SOURCE)
    md = (proj.knowledge_dir / source_page.rel_path).read_text("utf-8")
    assert md.startswith("---")
    assert "generated: true" in md
    proj.close()


def test_reingest_clears_stale_pages_and_rebuilds_source(tmp_path):
    proj = make_project(tmp_path)
    src_file = tmp_path / "solar.md"
    src_file.write_text(SAMPLE, "utf-8")
    mgr = IngestionManager(proj, build_provider(proj.settings.as_dict()))
    source = mgr.import_file(src_file)
    assert source is not None
    assert mgr.process_pending() == 1

    source = proj.store.get_source(source.id)
    source_page = next(
        p for p in proj.store.pages_for_source(source.id)
        if p.kind == PageKind.SOURCE
    )
    other = Source(title="Second source", rel_path="second.md",
                   status=SourceStatus.INGESTED)
    proj.store.upsert_source(other)
    writer = KnowledgeWriter(proj)
    stale = writer.write_page(Page(
        kind=PageKind.CONCEPT,
        title="Stale only source",
        slug="stale-only-source",
        summary="Only supported by the selected source.",
        body="# Stale only source\n\nOnly supported by the selected source.",
        sources=[source.id],
    ))
    shared = writer.write_page(Page(
        kind=PageKind.CONCEPT,
        title="Shared lifecycle concept",
        slug="shared-lifecycle-concept",
        summary="Supported by two sources.",
        body=(f"# Shared lifecycle concept\n\n## Sources\n\n"
              f"- [[{source_page.slug}]]\n- [[second-source]]"),
        sources=[source.id, other.id],
    ))

    queued = mgr.reingest_source(source.id)
    assert queued is not None
    assert queued.status == SourceStatus.PENDING
    assert proj.store.get_page(source_page.slug) is None
    assert proj.store.get_page(stale.slug) is None
    detached = proj.store.get_page(shared.slug)
    assert detached is not None
    assert detached.sources == [other.id]
    shared_md = (proj.knowledge_dir / detached.rel_path).read_text("utf-8")
    assert f"[[{source_page.slug}]]" not in shared_md
    assert "[[second-source]]" in shared_md

    assert mgr.process_pending() == 1
    refreshed = proj.store.get_source(source.id)
    assert refreshed is not None
    assert refreshed.status == SourceStatus.INGESTED
    assert any(
        p.kind == PageKind.SOURCE and source.id in p.sources
        for p in proj.store.list_pages()
    )
    assert proj.store.get_page(stale.slug) is None
    proj.close()


def test_remove_source_detaches_shared_pages_and_deletes_orphans(tmp_path):
    proj = make_project(tmp_path)
    src_file = tmp_path / "solar.md"
    src_file.write_text(SAMPLE, "utf-8")
    mgr = IngestionManager(proj, build_provider(proj.settings.as_dict()))
    source = mgr.import_file(src_file)
    assert source is not None
    assert mgr.process_pending() == 1

    source_page = next(
        p for p in proj.store.pages_for_source(source.id)
        if p.kind == PageKind.SOURCE
    )
    source_file = proj.sources_dir / source.rel_path
    other = Source(title="Second source", rel_path="second.md",
                   status=SourceStatus.INGESTED)
    proj.store.upsert_source(other)
    writer = KnowledgeWriter(proj)
    orphan = writer.write_page(Page(
        kind=PageKind.ENTITY,
        title="Orphan entity",
        slug="orphan-entity",
        summary="Supported only by the selected source.",
        body="# Orphan entity\n\n## Sources\n\n"
             f"- [[{source_page.slug}]]",
        sources=[source.id],
    ))
    shared = writer.write_page(Page(
        kind=PageKind.CONCEPT,
        title="Shared lifecycle concept",
        slug="shared-lifecycle-concept",
        summary="Supported by two sources.",
        body=(f"# Shared lifecycle concept\n\n## Sources\n\n"
              f"- [[{source_page.slug}]]\n- [[second-source]]"),
        sources=[source.id, other.id],
    ))

    removed = mgr.remove_source(source.id)
    assert removed is not None
    assert not source_file.exists()
    assert proj.store.get_source(source.id) is None
    assert proj.store.get_page(source_page.slug) is None
    assert proj.store.get_page(orphan.slug) is None
    remaining = proj.store.get_page(shared.slug)
    assert remaining is not None
    assert remaining.sources == [other.id]
    shared_md = (proj.knowledge_dir / remaining.rel_path).read_text("utf-8")
    assert source_page.slug not in shared_md
    assert "[[second-source]]" in shared_md
    assert mgr.remove_source(source.id) is None
    proj.close()


def test_query_returns_citations(tmp_path):
    proj = make_project(tmp_path)
    src_file = tmp_path / "solar.md"
    src_file.write_text(SAMPLE, "utf-8")
    mgr = IngestionManager(proj)
    mgr.import_file(src_file)
    mgr.process_pending()

    engine = QueryEngine(proj, build_provider(proj.settings.as_dict()))
    result = engine.query("How does solar energy work?")
    assert result.pages
    assert result.citations
    assert "[1]" in result.answer

    saved = engine.save_answer("How does solar energy work?", result)
    assert saved.kind == PageKind.ANSWER
    assert (proj.knowledge_dir / saved.rel_path).exists()
    proj.close()


def test_import_and_ingest_epub(tmp_path):
    proj = make_project(tmp_path)
    epub = tmp_path / "smoke.epub"
    _write_minimal_epub(epub, """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1</title></head>
<body><h1>Chapter One</h1>
<p>EPUB smoke test content for the gknowledge test suite. The offline
extractor only needs a sentence or two of real text to summarize.</p>
</body></html>""")

    mgr = IngestionManager(proj, build_provider(proj.settings.as_dict()))
    source = mgr.import_file(epub)
    assert source is not None

    done = mgr.process_pending()
    assert done == 1

    source = proj.store.get_source(source.id)
    assert source.status == SourceStatus.INGESTED

    pages = proj.store.list_pages()
    source_page = next(p for p in pages if p.kind == PageKind.SOURCE)
    md = (proj.knowledge_dir / source_page.rel_path).read_text("utf-8")
    assert "EPUB smoke test content" in md
    proj.close()


def test_lint_flags_and_refreshes_sources_whose_original_changed(tmp_path):
    proj = make_project(tmp_path)
    src_file = tmp_path / "solar.md"
    src_file.write_text(SAMPLE, "utf-8")
    mgr = IngestionManager(proj, build_provider(proj.settings.as_dict()))
    source = mgr.import_file(src_file)
    assert source is not None
    assert stale_sources(proj) == []          # not ingested yet: nothing to drift
    assert mgr.process_pending() == 1
    assert stale_sources(proj) == []

    src_file.write_text(SAMPLE + "\nGeothermal plants run around the clock.\n", "utf-8")
    stale = stale_sources(proj)
    assert [s.source.id for s in stale] == [source.id]
    assert any(p.kind == PageKind.SOURCE for p in stale[0].pages)

    old_rel = proj.store.get_source(source.id).rel_path
    refreshed = mgr.refresh_source(source.id)
    assert refreshed is not None and refreshed.status == SourceStatus.PENDING
    assert refreshed.rel_path != old_rel
    assert not (proj.sources_dir / old_rel).exists()
    assert mgr.process_pending() == 1
    assert stale_sources(proj) == []
    current = proj.store.get_source(source.id)
    assert "Geothermal" in (proj.sources_dir / current.rel_path).read_text("utf-8")
    assert current.status == SourceStatus.INGESTED

    # A deleted original is not drift: the ingested copy is still the truth.
    detector = ChangeDetector(proj)
    src_file.unlink()
    assert detector.stale_sources() == []
    proj.close()


def test_store_converts_a_wal_database(tmp_path):
    """Older projects used WAL, which the Flatpak document portal cannot open."""
    import sqlite3
    proj = make_project(tmp_path)
    db = proj.store.path
    proj.close()
    conn = sqlite3.connect(db)
    assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    conn.close()

    proj = Project.open(tmp_path / "proj")
    mode = proj.store._conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "delete"
    other = sqlite3.connect(db)  # the MCP server opens the same file
    assert other.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 0
    other.close()
    proj.close()


if __name__ == "__main__":  # allow running without pytest
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    for name, fn in (("a", test_project_layout),
                     ("b", test_import_ingest_and_dedup),
                     ("c", test_query_returns_citations),
                     ("d", test_import_and_ingest_epub),
                     ("e", test_reingest_clears_stale_pages_and_rebuilds_source),
                     ("f", test_remove_source_detaches_shared_pages_and_deletes_orphans),
                     ("g", test_lint_flags_and_refreshes_sources_whose_original_changed),
                     ("h", test_store_converts_a_wal_database)):
        d = tmp / name
        d.mkdir(parents=True, exist_ok=True)
        fn(d)
    print("All core tests passed.")

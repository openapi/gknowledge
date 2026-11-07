"""MCP server: let coding agents read and grow a gknowledge wiki.

Claude Code, Codex, Cursor and any Model Context Protocol client can search
the wiki, read pages, ask cited questions and add new sources. Stdlib only,
JSON-RPC 2.0 over stdio (newline-delimited).

    gknowledge-mcp /path/to/project
    gknowledge-mcp --init /path/to/project   # create the project if missing
    python3 -m gknowledge.mcp /path/to/project

Register with Claude Code:

    claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from . import __version__
from .core import lint
from .core.ingestion import IngestionManager
from .core.knowledge import KnowledgeWriter
from .core.project import Project
from .core.query import QueryEngine
from .providers import build_provider

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")

TOOLS = [
    {
        "name": "search_wiki",
        "description": "Search the gknowledge wiki. Returns matching pages with "
                       "slug, type and a one-line summary. Use read_page for details.",
        "inputSchema": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Words to look for"},
            "limit": {"type": "integer", "default": 8}},
            "required": ["query"]},
    },
    {
        "name": "read_page",
        "description": "Read one wiki page as Markdown, including its sources and "
                       "the pages that link to it.",
        "inputSchema": {"type": "object", "properties": {
            "slug": {"type": "string", "description": "Page slug from search_wiki"}},
            "required": ["slug"]},
    },
    {
        "name": "list_pages",
        "description": "List wiki pages, optionally filtered by type "
                       "(source, entity, concept, topic, answer).",
        "inputSchema": {"type": "object", "properties": {
            "type": {"type": "string"}}},
    },
    {
        "name": "ask",
        "description": "Answer a question from the wiki with numbered citations, "
                       "using the provider configured in the project.",
        "inputSchema": {"type": "object", "properties": {
            "question": {"type": "string"},
            "save": {"type": "boolean", "default": False,
                     "description": "Save the answer back into the wiki"}},
            "required": ["question"]},
    },
    {
        "name": "add_source",
        "description": "Import a local file (Markdown, text, PDF, HTML) into the "
                       "project and ingest it into the wiki.",
        "inputSchema": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Absolute path of the file"},
            "ingest": {"type": "boolean", "default": True}},
            "required": ["path"]},
    },
    {
        "name": "stale_sources",
        "description": "Lint the wiki for drift: sources whose original file changed "
                       "after ingestion, with the pages that still reflect the old "
                       "version. Re-import or refresh them in the app.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "recent_activity",
        "description": "Recent operations from the wiki log (ingests, saved answers).",
        "inputSchema": {"type": "object", "properties": {
            "limit": {"type": "integer", "default": 20}}},
    },
]


class WikiServer:
    def __init__(self, project: Project):
        self.project = project
        self.writer = KnowledgeWriter(project)

    def _provider(self):
        return build_provider(self.project.settings.as_dict())

    # -- tools ---------------------------------------------------------------
    def search_wiki(self, query: str, limit: int = 8) -> str:
        engine = QueryEngine(self.project, self._provider())
        hits = engine._score_pages(query)[: max(1, int(limit))]
        if not hits:
            return "No pages match."
        return "\n".join(f"- {p.slug} ({p.kind.value}): {p.title}"
                         + (f" — {p.summary[:160]}" if p.summary else "")
                         for _, p in hits)

    def read_page(self, slug: str) -> str:
        page = self.project.store.get_page(slug)
        if not page:
            raise ValueError(f"No page with slug '{slug}'.")
        body = self.writer.read_body(page)
        back = sorted({l.from_slug for l in self.project.store.all_links()
                       if l.to_slug == slug and l.from_slug != slug})
        if back:
            body += "\n\n## Linked from\n\n" + "\n".join(f"- [[{s}]]" for s in back)
        return body

    def list_pages(self, type: str | None = None) -> str:  # noqa: A002
        pages = self.project.store.list_pages(type or None)
        return "\n".join(f"- {p.slug} ({p.kind.value}): {p.title}" for p in pages) \
            or "The wiki is empty."

    def ask(self, question: str, save: bool = False) -> str:
        engine = QueryEngine(self.project, self._provider())
        result = engine.query(question)
        out = [result.answer, "", "Sources:"]
        out += [f"[{c.number}] {c.slug} — {c.title}" for c in result.citations]
        if result.warning:
            out += ["", f"Note: {result.warning}"]
        if save and result.pages:
            saved = engine.save_answer(question, result)
            out += ["", f"Saved as page '{saved.slug}'."]
        return "\n".join(out)

    def add_source(self, path: str, ingest: bool = True) -> str:
        fp = Path(path).expanduser()
        if not fp.is_file():
            raise ValueError(f"File not found: {fp}")
        mgr = IngestionManager(self.project, self._provider())
        source = mgr.import_file(fp)
        if source is None:
            return "Already imported (same content)."
        if not ingest:
            return f"Imported '{source.title}'; ingest it from the app or call add_source again."
        notes: list[str] = []
        mgr.process_pending(progress=lambda ev, _j, msg: notes.append(f"{ev}: {msg}")
                            if ev in ("done", "warning", "error") else None)
        return "\n".join(notes) or "Imported."

    def stale_sources(self) -> str:
        stale = lint.stale_sources(self.project)
        if not stale:
            return "No drift: every ingested source matches its original file."
        out = []
        for s in stale:
            out.append(f"- {s.source.title} ({s.source.origin_path}) changed since ingest; "
                       f"{len(s.pages)} page(s) may be outdated:")
            out += [f"  - {p.slug}" for p in s.pages]
        return "\n".join(out)

    def recent_activity(self, limit: int = 20) -> str:
        rows = self.project.store.recent_log(int(limit))
        return "\n".join(f"- {r['op']}: {r['detail']}" for r in rows) or "No activity yet."

    # -- JSON-RPC ------------------------------------------------------------
    def handle(self, msg: dict) -> dict | None:
        method, mid = msg.get("method"), msg.get("id")
        if mid is None:                                   # notification
            return None
        try:
            if method == "initialize":
                asked = (msg.get("params") or {}).get("protocolVersion")
                result = {
                    "protocolVersion": asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "gknowledge", "version": __version__},
                    "instructions": f"Wiki '{self.project.name}'. Search before reading; "
                                    "cite page slugs in your answers.",
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = msg.get("params") or {}
                name, args = params.get("name"), params.get("arguments") or {}
                if name not in {t["name"] for t in TOOLS}:
                    raise KeyError(name)
                try:
                    text, is_error = getattr(self, name)(**args), False
                except Exception as exc:  # noqa: BLE001 - report to the agent
                    text, is_error = f"Error: {exc}", True
                result = {"content": [{"type": "text", "text": text}], "isError": is_error}
            else:
                return {"jsonrpc": "2.0", "id": mid,
                        "error": {"code": -32601, "message": f"Unknown method {method}"}}
        except KeyError as exc:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32602, "message": f"Unknown tool {exc}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    init = "--init" in argv
    argv = [a for a in argv if a != "--init"]
    path = argv[0] if argv else os.environ.get("GKNOWLEDGE_PROJECT", "")
    if path and init and not Project.is_project(path):
        Project.create(path).close()
    if not path or not Project.is_project(path):
        print("usage: gknowledge-mcp [--init] /path/to/gknowledge/project",
              file=sys.stderr)
        return 2
    server = WikiServer(Project.open(path))
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            reply = {"jsonrpc": "2.0", "id": None,
                     "error": {"code": -32700, "message": "Parse error"}}
        else:
            reply = server.handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

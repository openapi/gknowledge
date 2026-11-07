"""The MCP server speaks JSON-RPC over stdio and serves the wiki."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gknowledge.core.ingestion import IngestionManager  # noqa: E402
from gknowledge.core.project import Project, Settings  # noqa: E402


def _project(tmp_path):
    proj = Project.create(tmp_path / "wiki", name="Papers")
    proj.save_settings(Settings(provider="offline"))
    mgr = IngestionManager(proj)
    for f in sorted((ROOT / "data" / "demo" / "papers").glob("*.md")):
        mgr.import_file(f)
    mgr.process_pending()
    proj.close()
    return tmp_path / "wiki"


def _session(path, messages):
    return _session_args([str(path)], messages)


def _session_args(args, messages):
    proc = subprocess.run([sys.executable, "-m", "gknowledge.mcp", *args],
                          input="\n".join(json.dumps(m) for m in messages) + "\n",
                          capture_output=True, text=True, cwd=ROOT, timeout=60)
    return [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]


def test_mcp_round_trip(tmp_path):
    path = _project(tmp_path)
    extra = tmp_path / "note.md"
    extra.write_text("# Mixture of Experts\n\nMixture of Experts models route each "
                     "token to a few expert networks. Google Brain used them in 2017.\n")
    out = _session(path, [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "search_wiki", "arguments": {"query": "retrieval augmented"}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "read_page", "arguments": {"slug": "bert"}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "ask", "arguments": {"question": "What is BERT?"}}},
        {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
         "params": {"name": "add_source", "arguments": {"path": str(extra)}}},
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
         "params": {"name": "read_page", "arguments": {"slug": "missing"}}},
    ])
    by_id = {m["id"]: m for m in out}
    assert by_id[1]["result"]["serverInfo"]["name"] == "gknowledge"
    assert {t["name"] for t in by_id[2]["result"]["tools"]} >= {"search_wiki", "ask", "add_source"}
    assert "retrieval-augmented-generation" in by_id[3]["result"]["content"][0]["text"]
    assert "Bidirectional" in by_id[4]["result"]["content"][0]["text"]
    assert "[1]" in by_id[5]["result"]["content"][0]["text"]
    assert "Mixture of Experts" in by_id[6]["result"]["content"][0]["text"]
    assert by_id[7]["result"]["isError"] is True


def test_mcp_init_creates_project(tmp_path):
    path = tmp_path / "new-wiki"
    out = _session_args(["--init", str(path)], [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": "list_pages", "arguments": {}}},
    ])
    assert Project.is_project(path)
    assert out[0]["id"] == 1 and "result" in out[0]


def test_mcp_without_init_refuses_missing_project(tmp_path):
    proc = subprocess.run([sys.executable, "-m", "gknowledge.mcp", str(tmp_path / "nope")],
                          input="", capture_output=True, text=True, cwd=ROOT, timeout=60)
    assert proc.returncode == 2
    assert not (tmp_path / "nope").exists()


def test_mcp_stale_sources_reports_drift(tmp_path):
    proj = Project.create(tmp_path / "wiki", name="Drift")
    proj.save_settings(Settings(provider="offline"))
    note = tmp_path / "note.md"
    note.write_text("# Mixture of Experts\n\nMixture of Experts models route each "
                    "token to a few expert networks.\n")
    mgr = IngestionManager(proj)
    mgr.import_file(note)
    mgr.process_pending()
    proj.close()
    call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "stale_sources", "arguments": {}}}
    assert "No drift" in _session(tmp_path / "wiki", [call])[0]["result"]["content"][0]["text"]

    note.write_text(note.read_text() + "\nSwitch Transformers scaled them in 2021.\n")
    text = _session(tmp_path / "wiki", [call])[0]["result"]["content"][0]["text"]
    assert "Mixture of Experts" in text and "changed since ingest" in text

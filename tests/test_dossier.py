"""Dossier lifecycle: drafts, saving to a folder, launcher files, legacy layout."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gknowledge.core import project as dossier
from gknowledge.core.ingestion import IngestionManager
from gknowledge.core.project import Project, Settings
from gknowledge.providers import build_provider


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("GKNOWLEDGE_DOSSIER_HOME", raising=False)


def test_draft_has_a_name_and_works_before_it_has_a_folder(tmp_path):
    draft = Project.create_draft("Ponte sullo stretto, problema o occasione")
    assert draft.is_draft
    assert draft.name == "Ponte sullo stretto, problema o occasione"
    assert draft.root.parent == dossier.drafts_dir()

    note = tmp_path / "relazione.md"
    note.write_text("# Ponte\n\nIl ponte collegherebbe Messina e Reggio Calabria.\n", "utf-8")
    draft.save_settings(Settings(provider="offline"))
    mgr = IngestionManager(draft, build_provider(draft.settings.as_dict()))
    assert mgr.import_file(note) is not None
    assert mgr.process_pending() == 1
    assert draft.store.list_pages()
    draft.close()


def test_saving_moves_the_draft_into_the_default_home(tmp_path):
    draft = Project.create_draft("Ponte sullo stretto, problema o occasione")
    draft_root = draft.root
    dest = draft.suggested_folder()
    assert dest == (tmp_path / "home" / "Documents" / "Dossiers"
                    / "Ponte sullo stretto, problema o occasione")

    saved = draft.materialize(dest)
    assert not draft_root.exists()
    assert not saved.is_draft
    assert saved.root == dest
    assert saved.name == "Ponte sullo stretto, problema o occasione"
    visible = sorted(p.name for p in dest.iterdir() if not p.name.startswith("."))
    assert visible == ["Ponte sullo stretto, problema o occasione.dossier",
                       "knowledge", "notes", "sources"]
    assert (dest / ".gitignore").read_text("utf-8") == ".dossier/\n"
    saved.close()


def test_suggested_folder_never_overwrites(tmp_path):
    home = tmp_path / "elsewhere"
    (home / "Tesi").mkdir(parents=True)
    draft = Project.create_draft("Tesi")
    assert draft.suggested_folder(home) == home / "Tesi (2)"
    with pytest.raises(FileExistsError):
        draft.materialize(home / "Tesi")
    assert draft.root.exists()  # nothing lost on refusal
    draft.close()


def test_default_home_follows_localised_documents_dir(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "user-dirs.dirs").write_text(
        'XDG_DESKTOP_DIR="$HOME/Scrivania"\nXDG_DOCUMENTS_DIR="$HOME/Documenti"\n', "utf-8")
    assert dossier.default_home() == tmp_path / "home" / "Documenti" / "Dossiers"


def test_default_home_override(tmp_path, monkeypatch):
    monkeypatch.setenv("GKNOWLEDGE_DOSSIER_HOME", str(tmp_path / "custom"))
    assert dossier.default_home() == tmp_path / "custom"


def test_launcher_file_opens_the_dossier(tmp_path):
    proj = Project.create(tmp_path / "Casa", name="Casa")
    launcher = tmp_path / "Casa" / "Casa.dossier"
    manifest = json.loads(launcher.read_text("utf-8"))
    assert manifest["dossier"] == "0.1" and manifest["name"] == "Casa"
    proj.close()
    assert Project.is_project(launcher)
    reopened = Project.open(launcher)
    assert reopened.root == tmp_path / "Casa"
    reopened.close()


def test_renamed_launcher_still_opens(tmp_path):
    Project.create(tmp_path / "Casa", name="Casa").close()
    os.rename(tmp_path / "Casa" / "Casa.dossier", tmp_path / "Casa" / "Casa al mare.dossier")
    reopened = Project.open(tmp_path / "Casa")
    assert reopened.name == "Casa"
    reopened.close()


def test_legacy_project_opens_unchanged(tmp_path):
    root = tmp_path / "old"
    for sub in ("sources", "knowledge", "index", "cache", "settings"):
        (root / sub).mkdir(parents=True)
    (root / "gknowledge.json").write_text(json.dumps(
        {"format_version": 1, "id": "abc", "name": "Old KB", "created_at": 1.0}), "utf-8")
    (root / "settings" / "settings.json").write_text(
        json.dumps({"provider": "ollama", "model": "llama3.2"}), "utf-8")

    proj = Project.open(root)
    assert proj.legacy and proj.name == "Old KB"
    assert proj.settings.provider == "ollama"
    assert proj.index_dir == root / "index"
    assert not (root / ".dossier").exists()
    proj.close()
    assert sorted(p.name for p in root.iterdir()) == [
        "cache", "gknowledge.json", "index", "knowledge", "settings", "sources"]

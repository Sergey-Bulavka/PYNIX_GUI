"""Persistent Core transport: command validation, cleanup and opt-in V4 wiring."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from pynix_gui.ide_core_persistent import PersistentCoreReader
from pynix_gui.ide_core_read_bridge import CoreSnapshotError


def test_persistent_reader_reuses_one_running_process(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "main.pnx").write_text("function main()\n", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    reader._process = SimpleNamespace(poll=lambda: None, stdin=SimpleNamespace(
        write=lambda value: None, flush=lambda: None))
    reader._lines.put({"ok": True, "kind": "snapshot", "value": {"projectOpen": True}})
    assert reader.snapshot()["projectOpen"] is True
    reader._lines.put({"ok": True, "kind": "snapshot", "value": {
        "activeSourcePath": str(project / "src/main.pnx"),
    }})
    assert "main.pnx" in reader.open_source("src/main.pnx")["activeSourcePath"]


def test_persistent_reader_denies_outside_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    with pytest.raises(CoreSnapshotError):
        reader.open_source("../outside.pnx")


def test_v4_releases_persistent_core_and_does_not_delegate_saves():
    src = (Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py").read_text(
        encoding="utf-8")
    assert "PersistentCoreReader(args.ide_core, session.root, compiler_for_core)" in src
    assert "core_reader.open_source(source)" in src
    assert "core_reader.close()" in src
    assert "session.save(source)" in src

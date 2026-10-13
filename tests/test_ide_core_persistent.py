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


def test_unsaved_buffer_mirrored_without_disk_write(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    source = project / "src" / "main.pnx"
    source.write_text("original", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    written = []
    reader._process = SimpleNamespace(poll=lambda: None, stdin=SimpleNamespace(
        write=written.append, flush=lambda: None))
    content = "function main()\\n    print(\\\"updated\\\")\\n"
    reader._lines.put({"ok": True, "kind": "snapshot", "value": {
        "activeSourceContent": content, "activeSourceDirty": True,
    }})
    result = reader.update_source("src/main.pnx", content)
    assert result["activeSourceDirty"] is True
    assert '"command": "updateSource"' in written[0]
    assert source.read_text(encoding="utf-8") == "original"


def test_v4_publishes_unsaved_buffers_on_input():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert 'scheduleCoreBufferSync();' in js
    assert 'pynixCoreBuffer' in js
    assert 'core_reader.update_source(source, content)' in native
    assert '"pynixCoreBuffer"' in native

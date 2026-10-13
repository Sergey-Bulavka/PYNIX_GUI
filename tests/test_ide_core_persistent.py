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
        "activeSourceContent": content, "activeSourceDirty": True, "revision": 1,
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
    assert 'core_reader.update_source(source, content, revision)' in native
    assert '"pynixCoreBuffer"' in native


def test_core_clean_baseline_requires_confirmed_ack(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    target = project / "src" / "main.pnx"
    target.write_text("saved text", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    sent = []
    reader._process = SimpleNamespace(
        poll=lambda: None,
        stdin=SimpleNamespace(write=sent.append, flush=lambda: None))
    reader._lines.put({"ok": True, "kind": "snapshot", "value": {
        "activeSourceContent": "saved text", "activeSourceDirty": False,
    }})
    snapshot = reader.acknowledge_saved_source("src/main.pnx", "saved text")
    assert snapshot["activeSourceDirty"] is False
    assert '"command": "ackSavedSource"' in sent[0]
    assert target.read_text(encoding="utf-8") == "saved text"


def test_native_save_waits_for_v4_disk_write_before_core_ack():
    source = (Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py").read_text(
        encoding="utf-8")
    assert source.index("session.save(source)") < source.index(
        "core_reader.acknowledge_saved_source(source, content)")


def test_rejects_revision_mismatch(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.pnx").write_text("old", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    reader._process = SimpleNamespace(poll=lambda: None, stdin=SimpleNamespace(
        write=lambda value: None, flush=lambda: None))
    reader._lines.put({"ok": True, "kind": "snapshot", "value": {
        "activeSourceContent": "new", "revision": 1,
    }})
    with pytest.raises(CoreSnapshotError, match="differs|Invalid"):
        reader.update_source("src/main.pnx", "new", 2)


def test_v4_tracks_revisions_per_source():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "const coreRevisions=new Map();" in js
    assert "coreRevisions.set(source,revision)" in js
    assert "bridge.postMessage({source,text:content,revision})" in js


def test_discard_source_clears_only_core_mirror(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    original = project / "src" / "main.pnx"
    original.write_text("untouched", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    outgoing = []
    reader._process = SimpleNamespace(
        poll=lambda: None,
        stdin=SimpleNamespace(write=outgoing.append, flush=lambda: None))
    reader._lines.put({"ok": True, "kind": "snapshot", "value": {
        "activeSourceContent": "untouched", "activeSourceDirty": False,
    }})
    response = reader.discard_source("src/main.pnx")
    assert response["activeSourceDirty"] is False
    assert '"command": "discardSource"' in outgoing[0]
    assert original.read_text(encoding="utf-8") == "untouched"


def test_switch_flushes_pending_revisions_and_discard_cancels_pending():
    root = Path(__file__).resolve().parents[1]
    src = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    app = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert "function cancelCoreBufferSync(name)" in src
    assert "if(coreSyncTimers.has(source))" in src
    assert "coreRevisions.get(source)" in src
    assert "pynixCoreDiscard" in src
    assert "core_reader.discard_source(source)" in app


def test_core_revision_acknowledgment_ignores_stale_callbacks():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert "window.pynixCoreBufferResult=reply=>" in js
    assert "if(revision<(coreRevisions.get(source)||0))return;" in js
    assert "coreConfirmedRevisions.set(source,revision)" in js
    assert 'reply["ok"] = True' in native
    assert '"window.pynixCoreBufferResult(" + serialized + ");"' in native


def test_wkwebview_numeric_revision_is_normalized_at_native_boundary():
    app = (Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py").read_text(
        encoding="utf-8")
    assert 'hasattr(revision, "integerValue")' in app
    assert 'revision = whole' in app
    assert 'core_reader.update_source(source, content, revision)' in app

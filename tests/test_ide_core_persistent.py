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
    assert "closeTabNow(name,true);" in src
    assert "bridge.postMessage({source:name,discard});" in src
    assert "core_reader.discard_source(source)" in app
    assert app.index("core_reader.discard_source(source)") < app.index("core_reader.close_source(source)")


def test_core_revision_acknowledgment_ignores_stale_callbacks():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert "window.pynixCoreBufferResult=reply=>" in js
    assert "if(revision!==(coreRevisions.get(source)||0))return;" in js
    assert "coreConfirmedRevisions.set(source,revision)" in js
    assert 'reply["ok"] = True' in native
    assert '"window.pynixCoreBufferResult(" + serialized + ");"' in native


def test_wkwebview_numeric_revision_is_normalized_at_native_boundary():
    app = (Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py").read_text(
        encoding="utf-8")
    assert 'hasattr(revision, "integerValue")' in app
    assert 'revision = whole' in app
    assert 'core_reader.update_source(source, content, revision)' in app


def test_save_is_a_versioned_core_barrier_before_atomic_disk_write():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    app = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert "function prepareNativeSave(source,content)" in js
    assert "cancelCoreBufferSync(source);" in js
    assert "coreRevisions.set(source,revision);" in js
    assert "bridge.postMessage(prepareNativeSave(current,file.text));" in js
    assert "bridge.postMessage(prepareNativeSave(name,selected.text));" in js
    before_save = app[app.index("class FileSaveHandler"):app.index("class ProjectSearchHandler")]
    assert before_save.index("core_reader.update_source(source, content, revision)") < before_save.index("session.save(source)")
    assert "CoreSnapshotError" in before_save


def test_editor_keeps_caret_selection_and_scroll_per_tab():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "file.cursorStart=editorInput.selectionStart;" in js
    assert "file.cursorEnd=editorInput.selectionEnd;" in js
    assert "file.scrollTop=editorInput.scrollTop;" in js
    assert "file.scrollLeft=editorInput.scrollLeft;" in js
    assert "editorInput.addEventListener('select',()=>persistBuffer());" in js
    assert "const start=file.cursorStart??0;" in js
    assert "const end=file.cursorEnd??start;" in js
    assert "editorInput.setSelectionRange(start,end);" in js
    assert "if(restoringEditor||!editing||!current)return;" in js


def test_webkit_restoration_suppresses_deferred_selection_and_scroll_events():
    source = (Path(__file__).resolve().parents[1] / "pynix_gui" /
              "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "if(restoringEditor||!editing||!current)return;" in source
    assert "const start=file.cursorStart??0;" in source
    assert "const top=file.scrollTop??0;" in source
    assert "restoringEditor=true;" in source
    assert "editorRestoreEpoch" in source
    assert "requestAnimationFrame(()=>{" in source
    assert "if(epoch===editorRestoreEpoch&&current===source)restoringEditor=false;" in source


def test_core_authoritative_source_readback(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    target = project / "src" / "main.pnx"
    target.write_text("original", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    writes = []
    reader._process = SimpleNamespace(
        poll=lambda: None,
        stdin=SimpleNamespace(write=writes.append, flush=lambda: None))
    reader._lines.put({"ok": True, "kind": "sourceState", "value": {
        "source": "src/main.pnx", "content": "unsaved",
        "dirty": True, "revision": 4,
    }})
    state = reader.read_source("src/main.pnx")
    assert state == {
        "source": "src/main.pnx", "content": "unsaved",
        "dirty": True, "revision": 4,
    }
    assert '"command": "readSource"' in writes[0]
    assert target.read_text(encoding="utf-8") == "original"


def test_core_readback_rejects_invalid_revision(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.pnx").write_text("disk", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    reader._process = SimpleNamespace(
        poll=lambda: None, stdin=SimpleNamespace(
            write=lambda value: None, flush=lambda: None))
    reader._lines.put({"ok": True, "kind": "sourceState", "value": {
        "source": "src/main.pnx", "content": "disk",
        "dirty": False, "revision": "5",
    }})
    with pytest.raises(CoreSnapshotError, match="source state"):
        reader.read_source("src/main.pnx")


def test_save_requires_authoritative_core_readback_before_disk_write():
    app = (Path(__file__).resolve().parents[1] / "examples" /
           "ide_native_v4.py").read_text(encoding="utf-8")
    block = app.split("class FileSaveHandler(NSObject):", 1)[1].split(
        "class ProjectSearchHandler(NSObject):", 1)[0]
    assert block.index("core_reader.update_source(source, content, revision)") < (
        block.index("core_reader.read_source(source)"))
    assert block.index("core_reader.read_source(source)") < block.index("session.save(source)")
    assert "Core source diverged before save" in block


def test_editor_sync_verifies_core_readback_and_tracks_tab_dirty_state():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    handler = native.split("class CoreBufferHandler(NSObject):", 1)[1].split(
        "class CoreDiscardHandler(NSObject):", 1)[0]
    assert handler.index("core_reader.update_source(source, content, revision)") < (
        handler.index("core_reader.read_source(source)"))
    assert 'state["revision"] != revision or state["content"] != content' in handler
    assert 'reply["dirty"] = state["dirty"]' in handler
    assert "file.coreRevision=revision" in preview
    assert "file.coreDirty=reply.dirty===true" in preview
    assert "if(revision!==(coreRevisions.get(source)||0))return;" in preview


def test_core_close_clean_source_and_native_tab_lifecycle(tmp_path):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    target = project / "src" / "main.pnx"
    target.write_text("saved", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    outgoing = []
    reader._process = SimpleNamespace(
        poll=lambda: None,
        stdin=SimpleNamespace(write=outgoing.append, flush=lambda: None))
    reader._lines.put({"ok": True, "kind": "sourceClosed", "value": {
        "source": "src/main.pnx", "closed": True,
    }})
    assert reader.close_source("src/main.pnx") is True
    assert '"command": "closeSource"' in outgoing[0]
    assert target.read_text(encoding="utf-8") == "saved"
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert 'core_reader.close_source(source)' in native
    assert '"pynixCoreClose"' in native
    assert "bridge.postMessage({source:name,discard});" in preview
    assert "window.pynixCoreCloseResult=reply=>" in preview


def test_late_core_and_file_responses_cannot_resurrect_closed_tabs():
    root = Path(__file__).resolve().parents[1]
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    core = preview.split("window.pynixCoreBufferResult=reply=>{", 1)[1].split(
        "function scheduleCoreBufferSync()", 1)[0]
    load = preview.split("window.pynixReceiveFile=function(payload){", 1)[1].split(
        "document.addEventListener('pynix:navigate'", 1)[0]
    close = preview.split("function closeTabNow(name,discard=false){", 1)[1].split(
        "function requestCloseTab(name){", 1)[0]
    assert "!openTabs.includes(source)" in core
    assert "revision!==(coreRevisions.get(source)||0)" in core
    assert "file.coreSyncError=null" in core
    assert "file.coreSyncError=String(reply.error||'Unknown error')" in core
    assert "!openTabs.includes(payload.source)" in load
    assert "if(!file.unloaded||file.dirty)return;" in load
    assert "if(!openTabs.includes(name))return;" in close


def test_core_recovery_replays_all_open_buffers_without_disk_writes(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    first = project / "src" / "first.pnx"
    second = project / "src" / "second.pnx"
    first.write_text("saved 1", encoding="utf-8")
    second.write_text("saved 2", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    events = []
    monkeypatch.setattr(reader, "close", lambda: events.append("close"))
    monkeypatch.setattr(reader, "start", lambda: events.append("start"))
    monkeypatch.setattr(reader, "update_source",
                        lambda source, content, revision: events.append(
                            ("update", source, content, revision)))
    monkeypatch.setattr(reader, "read_source",
                        lambda source: {"source": source,
                                        "content": "edited 1" if source.endswith("first.pnx") else "edited 2",
                                        "revision": 4 if source.endswith("first.pnx") else 9})
    result = reader.restart_with_buffers([
        {"source": "src/first.pnx", "content": "edited 1", "revision": 4},
        {"source": "src/second.pnx", "content": "edited 2", "revision": 9},
    ])
    assert result == {"restored": 2}
    assert events == [
        "close", "start",
        ("update", "src/first.pnx", "edited 1", 4),
        ("update", "src/second.pnx", "edited 2", 9)]
    assert first.read_text(encoding="utf-8") == "saved 1"
    assert second.read_text(encoding="utf-8") == "saved 2"


def test_core_recovery_rejects_invalid_batch_before_stopping_process(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.pnx").write_text("saved", encoding="utf-8")
    reader = PersistentCoreReader(tmp_path, project, tmp_path / "python")
    stopped = []
    monkeypatch.setattr(reader, "close", lambda: stopped.append(True))
    with pytest.raises(CoreSnapshotError, match="recovery buffer"):
        reader.restart_with_buffers([
            {"source": "src/main.pnx", "content": "first", "revision": 1},
            {"source": "src/main.pnx", "content": "second", "revision": 2},
        ])
    assert stopped == []


def test_core_recovery_bridge_keeps_live_editor_text():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    adapter = (root / "pynix_gui" / "ide_core_persistent.py").read_text(encoding="utf-8")
    assert "class CoreRecoveryHandler(NSObject):" in native
    assert '"pynixCoreRecover"' in native
    assert "core_reader.restart_with_buffers(buffers)" in native
    assert "window.pynixCoreRecoveryResult=reply=>" in preview
    assert "coreIndicator.addEventListener('click',recoverCoreBuffers)" in preview
    assert "buffers.push({source,content:file.text,revision});" in preview
    assert "self._lines = queue.Queue()" in adapter


def test_recovery_ack_resyncs_inactive_tabs_edited_during_restart():
    root = Path(__file__).resolve().parents[1]
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    recovery = preview.split("window.pynixCoreRecoveryResult=reply=>{", 1)[1].split(
        "const coreIndicator=", 1)[0]
    assert "const replay=coreRecoverySnapshot||[];" in recovery
    assert "coreConfirmedRevisions.set(item.source,item.revision)" in recovery
    assert "file.text===item.content" in recovery
    assert "sendCoreRevision(item.source,file.text,revision);" in recovery
    assert "source===current" not in recovery
    assert "file.coreSyncError=error;" in recovery


def test_recovery_does_not_overwrite_unsaved_editor_buffers():
    root = Path(__file__).resolve().parents[1]
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    recovery = preview.split("window.pynixCoreRecoveryResult=reply=>{", 1)[1].split(
        "const coreIndicator=", 1)[0]
    assert "file.text===item.content" in recovery
    assert not __import__("re").search(r"file\.text\s*=(?!=)", recovery)
    assert "file.savedText=" not in recovery
    assert "file.dirty=" not in recovery


def test_core_save_failures_return_to_editor_and_keep_dirty_tab_open():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    handler = native.split("class FileSaveHandler(NSObject):", 1)[1].split(
        "class ProjectSearchHandler(NSObject):", 1)[0]
    callback = preview.split("window.pynixSaveResult=payload=>{", 1)[1].split(
        "const expanded =", 1)[0]
    assert "except (OSError, UnicodeError, ValueError, CoreSnapshotError) as error:" in handler
    assert 'response["error"] = str(error)' in handler
    error_handler = callback.split("if(payload.error){", 1)[1].split("if(payload.saved){", 1)[0]
    assert "pendingCloseAfterSave=null;" in error_handler
    assert "file.coreSyncError=String(payload.error);" in error_handler
    assert "file.dirty=false" not in error_handler
    assert "closeTabNow(" not in error_handler
    assert "file.text=" not in error_handler


def test_native_core_close_ack_is_required_before_tab_is_unloaded():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    handler = native.split("class CoreCloseHandler(NSObject):", 1)[1].split(
        "class CoreDiscardHandler(NSObject):", 1)[0]
    assert "core_reader.discard_source(source)" in handler
    assert handler.index("core_reader.discard_source(source)") < handler.index(
        "core_reader.close_source(source)")
    assert 'response["closed"] = True' in handler
    assert "window.pynixCoreCloseResult(" in handler
    close = preview.split("function closeTabNow(name,discard=false){", 1)[1].split(
        "function requestCloseTab(name){", 1)[0]
    assert "pendingCoreClose.set(name" in close
    assert "bridge.postMessage({source:name,discard});" in close
    assert "if(reply?.closed){finishTabClose(source);return;}" in close
    assert "function finishTabClose(name){" in close
    assert "if(!reply?.closed)" in close


def test_pynix_file_open_uses_core_authoritative_text_and_revision():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    handler = native.split("class FileOpenHandler(NSObject):", 1)[1].split(
        "class CoreBufferHandler(NSObject):", 1)[0]
    assert "core_reader.open_source(source)" in handler
    assert "state = core_reader.read_source(source)" in handler
    assert 'text = state["content"]' in handler
    assert 'response["revision"] = state["revision"]' in handler
    assert 'response["dirty"] = state["dirty"]' in handler
    assert 'response["savedText"] = file_path.read_text(encoding="utf-8")' in handler
    callback = preview.split("window.pynixReceiveFile=function(payload){", 1)[1].split(
        "document.addEventListener('pynix:navigate'", 1)[0]
    assert "file.text=payload.text;" in callback
    assert "file.dirty=payload.dirty===true;" in callback
    assert "coreConfirmedRevisions.set(payload.source,payload.revision)" in callback
    assert "file.coreRevision=payload.revision;" in callback


def test_save_reply_is_bound_to_exact_editor_revision_and_preserves_new_edits():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    handler = native.split("class FileSaveHandler(NSObject):", 1)[1].split(
        "class ProjectSearchHandler(NSObject):", 1)[0]
    assert 'response = {"source": source, "revision": request.get("revision")}' in handler
    assert "const pendingNativeSaves=new Map();" in preview
    assert "pendingNativeSaves.set(source,{revision,text:content});" in preview
    callback = preview.split("window.pynixSaveResult=payload=>{", 1)[1].split(
        "const expanded =", 1)[0]
    assert "if(!pending)return;" in callback
    assert "payload.revision!==pending.revision" in callback
    assert "pendingNativeSaves.delete(source);" in callback
    assert "file.savedText=typeof payload.savedText==='string'?payload.savedText:pending.text;" in callback
    assert "file.dirty=file.text!==file.savedText;" in callback
    assert "file.text===pending.text" in callback
    assert "coreConfirmedRevisions.set(source,pending.revision);" in callback

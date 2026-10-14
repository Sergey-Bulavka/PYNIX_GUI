"""Safe project file operations: no data loss or path escape."""
import pytest

from pynix_gui.ide_workspace_session import WorkspaceError, WorkspaceSession


def test_create_rename_delete_preserves_document_and_active_tab(tmp_path):
    (tmp_path / "src").mkdir()
    session = WorkspaceSession(tmp_path)
    doc = session.create_file("src/main.pnx", content="function main()\n    pass\n")
    assert doc.text.startswith("function main")
    assert session.active == "src/main.pnx"
    session.rename_file("src/main.pnx", "src/start.pnx")
    assert session.active == "src/start.pnx"
    assert session.documents["src/start.pnx"] is doc
    assert doc.path == "src/start.pnx"
    assert not (tmp_path / "src/main.pnx").exists()
    session.delete_file("src/start.pnx")
    assert not (tmp_path / "src/start.pnx").exists()
    assert session.active is None


def test_create_never_overwrites_existing_file(tmp_path):
    session = WorkspaceSession(tmp_path)
    session.create_file("hello.pnx", content="original")
    with pytest.raises(WorkspaceError, match="already exists"):
        session.create_file("hello.pnx", content="replacement")
    assert (tmp_path / "hello.pnx").read_text() == "original"


def test_dirty_document_rejects_rename_and_delete(tmp_path):
    session = WorkspaceSession(tmp_path)
    session.create_file("a.pnx", content="original")
    session.update("a.pnx", "modified")
    with pytest.raises(WorkspaceError, match="unsaved"):
        session.rename_file("a.pnx", "b.pnx")
    with pytest.raises(WorkspaceError, match="unsaved"):
        session.delete_file("a.pnx")
    assert (tmp_path / "a.pnx").read_text() == "original"
    assert not (tmp_path / "b.pnx").exists()


def test_project_file_operations_reject_escape_and_symlinks(tmp_path):
    session = WorkspaceSession(tmp_path)
    for path in ("../outside.pnx", "/tmp/unsafe.pnx", ".git/config"):
        with pytest.raises(WorkspaceError):
            session.create_file(path, content="nope")
    outside = tmp_path.parent / "pynix_workspace_test_outside.pnx"
    outside.write_text("unchanged", encoding="utf-8")
    (tmp_path / "link.pnx").symlink_to(outside)
    with pytest.raises(WorkspaceError):
        session.create_file("link.pnx", content="changed")
    with pytest.raises(WorkspaceError):
        session.rename_file("link.pnx", "renamed.pnx")
    assert outside.read_text(encoding="utf-8") == "unchanged"
    outside.unlink()


def test_rename_preserves_destination_and_refuses_collisions(tmp_path):
    session = WorkspaceSession(tmp_path)
    session.create_file("a.pnx", content="a")
    session.create_file("b.pnx", content="b")
    with pytest.raises(WorkspaceError, match="Destination exists"):
        session.rename_file("a.pnx", "b.pnx")
    assert (tmp_path / "a.pnx").read_text() == "a"
    assert (tmp_path / "b.pnx").read_text() == "b"


def test_create_directory_requires_existing_parent(tmp_path):
    session = WorkspaceSession(tmp_path)
    session.create_directory("src")
    assert (tmp_path / "src").is_dir()
    with pytest.raises(WorkspaceError):
        session.create_directory("src")
    with pytest.raises(WorkspaceError, match="parent"):
        session.create_directory("missing/nested")
    with pytest.raises(WorkspaceError):
        session.create_directory("../escaped")


def test_native_project_create_is_bound_to_workspace_and_updates_file_index():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "class ProjectCreateHandler(NSObject)" in native
    assert "doc = session.create_file(relative)" in native
    assert "available_sources.add(relative)" in native
    assert 'controller.addScriptMessageHandler_name_(project_create_handler, "pynixProjectCreate")' in native
    assert "window.pynixProjectCreateResult=result=>" in preview
    assert "window.pynixIndexedSources=files.map(entry=>entry.name)" in preview
    assert "show(name);" in preview


def test_native_project_rename_delete_guard_core_and_refresh_explorer():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "class ProjectFileActionHandler(NSObject)" in native
    assert 'core_reader.close_source(source)' in native
    assert 'state["dirty"]' in native
    assert 'session.rename_file(source, destination)' in native
    assert 'session.delete_file(source)' in native
    assert 'controller.addScriptMessageHandler_name_(project_file_action_handler, "pynixProjectFileAction")' in native
    assert "window.pynixProjectFileActionResult=result=>" in preview
    assert "if(openTabs.includes(source))" in preview
    assert "window.confirm('Permanently delete '" in preview
    assert "renameFileButton.textContent='Rename File'" in preview
    assert "deleteFileButton.textContent='Delete File'" in preview

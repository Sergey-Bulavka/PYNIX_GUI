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

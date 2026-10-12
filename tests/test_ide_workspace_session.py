from pathlib import Path
import pytest

from pynix_gui.ide_workspace_session import WorkspaceError, WorkspaceSession


def test_project_file_discovery_and_tab_switching(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.pnx").write_text("function main()\n", encoding="utf-8")
    (tmp_path / "src" / "other.pnx").write_text("function other()\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "secret").write_text("ignore", encoding="utf-8")
    session = WorkspaceSession(tmp_path)
    assert session.list_files() == ["src/main.pnx", "src/other.pnx"]
    assert session.open("src/main.pnx").text == "function main()\n"
    session.open("src/other.pnx")
    session.select("src/main.pnx")
    assert session.active == "src/main.pnx"


def test_dirty_buffer_requires_explicit_discard(tmp_path):
    (tmp_path / "main.pnx").write_text("original", encoding="utf-8")
    session = WorkspaceSession(tmp_path)
    session.open("main.pnx")
    doc = session.update("main.pnx", "changed")
    assert doc.dirty
    assert (tmp_path / "main.pnx").read_text() == "original"
    with pytest.raises(WorkspaceError, match="Unsaved"):
        session.close("main.pnx")
    session.close("main.pnx", discard=True)
    assert session.active is None


def test_project_boundary_rejects_escape_and_absolute_path(tmp_path):
    (tmp_path / "src.pnx").write_text("ok")
    session = WorkspaceSession(tmp_path)
    with pytest.raises(WorkspaceError):
        session.open("../missing.pnx")
    with pytest.raises(WorkspaceError):
        session.open(str((tmp_path / "src.pnx").resolve()))


def test_project_boundary_rejects_symlink_escape(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside.pnx")
    outside.write_text("outside")
    try:
        (tmp_path / "outside.pnx").symlink_to(outside)
        with pytest.raises(WorkspaceError):
            WorkspaceSession(tmp_path).open("outside.pnx")
    finally:
        outside.unlink(missing_ok=True)


def test_missing_project_rejected(tmp_path):
    with pytest.raises(WorkspaceError):
        WorkspaceSession(tmp_path / "nonexistent")

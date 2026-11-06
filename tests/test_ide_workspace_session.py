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


def test_atomic_save_updates_saved_snapshot(tmp_path):
    file = tmp_path / "main.pnx"
    file.write_text("old", encoding="utf-8")
    session = WorkspaceSession(tmp_path)
    session.open("main.pnx")
    session.update("main.pnx", "new content")
    assert session.documents["main.pnx"].dirty
    saved = session.save("main.pnx")
    assert file.read_text(encoding="utf-8") == "new content"
    assert not saved.dirty
    assert list(tmp_path.glob(".pynix-save-*")) == []


def test_external_disk_changes_block_save(tmp_path):
    file = tmp_path / "main.pnx"
    file.write_text("original", encoding="utf-8")
    session = WorkspaceSession(tmp_path)
    session.open("main.pnx")
    session.update("main.pnx", "editor change")
    file.write_text("external change", encoding="utf-8")
    with pytest.raises(WorkspaceError, match="changed on disk"):
        session.save("main.pnx")
    assert file.read_text(encoding="utf-8") == "external change"
    assert session.documents["main.pnx"].dirty



def test_safe_metadata_dotfiles_visible_but_secret_files_still_hidden(tmp_path):
    from pynix_gui.ide_workspace_session import WorkspaceSession
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    (tmp_path / ".gitattributes").write_text("*.pnx text\n")
    (tmp_path / ".editorconfig").write_text("root = true\n")
    (tmp_path / ".env").write_text("secret=do-not-display\n")
    (tmp_path / "main.pnx").write_text("function main()\n")
    visible=WorkspaceSession(tmp_path).list_files()
    assert ".gitignore" in visible
    assert ".gitattributes" in visible
    assert ".editorconfig" in visible
    assert "main.pnx" in visible
    assert ".env" not in visible


def test_creating_canonical_uny_file_is_indexed_and_never_overwrites(tmp_path):
    from pynix_gui.ide_file_icons import file_icon_type

    (tmp_path / "src").mkdir()
    session = WorkspaceSession(tmp_path)
    document = session.create_file("src/new_file.uny", content="function main()\n    pass\n")

    assert document.path == "src/new_file.uny"
    assert document.text == "function main()\n    pass\n"
    assert (tmp_path / "src" / "new_file.uny").read_text(encoding="utf-8") == document.text
    assert "src/new_file.uny" in session.list_files()
    assert file_icon_type("src/new_file.uny") == file_icon_type("src/legacy.pnx")

    with pytest.raises(WorkspaceError, match="already exists"):
        session.create_file("src/new_file.uny", content="overwrite")
    assert (tmp_path / "src" / "new_file.uny").read_text(encoding="utf-8") == document.text


def test_legacy_pnx_can_still_be_created_without_affecting_uny(tmp_path):
    session = WorkspaceSession(tmp_path)
    session.create_file("modern.uny", content="pass\n")
    session.create_file("legacy.pnx", content="pass\n")
    assert session.list_files() == ["legacy.pnx", "modern.uny"]


def test_workspace_new_file_defaults_to_uny_and_native_bridge_accepts_it():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    preview = (root / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    native = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")

    assert "newSourceButton.textContent='New .uny';" in preview
    assert "base+'new_file.uny'" in preview
    assert "base+(kind==='directory'?'new_directory':'new_file.uny')" in preview
    assert "session.create_file(relative)" in native
    assert "available_sources.add(relative)" in native

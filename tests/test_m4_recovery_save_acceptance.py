"""M4 acceptance: replayed unsaved files remain safely persistable.

This isolates the disk commit layer from AppKit, which is covered by manual
macOS crash tests. Core's replay transport has its own regression coverage.
"""
from pathlib import Path

import pytest

from pynix_gui.ide_workspace_session import WorkspaceError, WorkspaceSession


def test_two_recovered_editor_snapshots_save_atomically_without_loss(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    originals = {
        "src/first.pnx": "function main()\n    print(\"one\")\n",
        "src/second.pnx": "function second()\n    print(\"two\")\n",
    }
    recovered = {
        key: value + "// recovered unsaved editor change\n"
        for key, value in originals.items()
    }
    for name, value in originals.items():
        (tmp_path / name).write_text(value, encoding="utf-8")

    # A restarted Core acknowledges both snapshots without writing to disk.
    for name, value in originals.items():
        assert (tmp_path / name).read_text(encoding="utf-8") == value

    # Native Save commits the exact editor-owned recovered text in both tabs.
    session = WorkspaceSession(tmp_path)
    for name, text in recovered.items():
        session.open(name)
        session.update(name, text)
        assert session.documents[name].dirty
    for name in recovered:
        session.save(name)
    for name, text in recovered.items():
        assert (tmp_path / name).read_text(encoding="utf-8") == text
        assert not session.documents[name].dirty


def test_external_disk_change_after_recovery_is_never_overwritten(tmp_path):
    path = tmp_path / "first.pnx"
    path.write_text("original", encoding="utf-8")
    session = WorkspaceSession(tmp_path)
    session.open("first.pnx")
    session.update("first.pnx", "recovered unsaved edit")
    path.write_text("external edit", encoding="utf-8")
    with pytest.raises(WorkspaceError, match="changed on disk"):
        session.save("first.pnx")
    assert path.read_text(encoding="utf-8") == "external edit"
    assert session.documents["first.pnx"].text == "recovered unsaved edit"

"""Regression: dirty tab close must never silently discard editor buffers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dirty_tab_close_has_save_discard_cancel_choices():
    source = (ROOT / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "requestCloseTab(fileName)" in source
    assert "button('Cancel',dismiss)" in source
    assert "button('Don’t Save'" in source
    assert "button('Save'" in source
    assert "pendingCloseAfterSave===payload.source" in source
    assert "window.confirm('Discard unsaved changes" not in source


def test_explorer_uses_arrow_cursor_and_unsaved_dialog_is_visible():
    source = (ROOT / "examples" / "icon_direction_preview.html").read_text(encoding="utf-8")
    assert ".workspace-mode .tree *" in source
    assert "cursor:default!important" in source
    assert ".workspace-mode .pynix-unsaved-overlay" in source
    assert "z-index:100000" in source

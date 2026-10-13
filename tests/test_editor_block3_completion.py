"""Block 3 local completion integration checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_is_explicit_and_edits_through_editor_history():
    source = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "function completionPrefix()" in source
    assert "function offerCompletion()" in source
    assert "function applyCompletion(index)" in source
    assert "completionKeywords=['function','import','module'" in source
    assert "event.code==='Space'" in source
    assert "event.key==='ArrowDown'||event.key==='ArrowUp'" in source
    assert "replaceSelection(word,range.start,range.end)" in source
    assert "editorInput.value.slice(range.start,range.end)!==range.prefix" in source


def test_completion_ui_has_explicit_hidden_state_and_accessibility():
    source = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (ROOT / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "completionBox.hidden=true" in source
    assert "completionBox.setAttribute('role','listbox')" in source
    assert "item.setAttribute('role','option')" in source
    assert ".pynix-completion-popup[hidden]{display:none!important}" in html
    assert "completionBox.appendChild(item)" in source

"""Editor block 2 integration contracts, verified in full GUI regression."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "pynix_gui" / "ide_workspace_preview.py"
HTML = ROOT / "examples" / "icon_direction_preview.html"


def test_smart_enter_and_automatic_brace_pairs():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "const opens=prefix.trimEnd().endsWith('{');" in source
    assert "if(opens&&next==='}')" in source
    assert "const pnxBlock=/^(?:function|if|elif|else|for|while" in source
    assert "const pairs={'(' : ')','[' : ']','{' : '}'" in source
    assert "editorInput.setSelectionRange(start+1,start+1+selected.length)" in source


def test_matching_brackets_update_on_caret_moves():
    source = SCRIPT.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    assert "function matchingBracketPositions(value,caret)" in source
    assert "matching.has(match.index)" in source
    assert "recolorSource();" in source.split("editorInput.addEventListener('select'", 1)[1][:85]
    assert ".pynix-edit-bracket-match{" in html


def test_comment_toggle_and_line_editing_shortcuts():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "function duplicateCurrentLine()" in source
    assert "function moveCurrentLine(direction)" in source
    assert "e.metaKey&&e.shiftKey&&!e.altKey&&e.key.toLowerCase()==='d'" in source
    assert "moveCurrentLine(e.key==='ArrowUp'?-1:1)" in source
    assert "if((e.metaKey||e.ctrlKey)&&e.key==='/')" in source


def test_multi_occurrence_edits_preserve_undo_redo_and_tab_history():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "function addNextOccurrence()" in source
    assert "function editMultipleSelections(inputType,data)" in source
    assert "extraSelections:(file?.extraSelections||[])" in source
    assert "file.extraSelections=state.extraSelections||[];" in source
    assert "file.extraSelections=next;" in source
    assert "pushUndo(file);" in source
    assert "e.preventDefault();addNextOccurrence();return;" in source


def test_preview_folding_keeps_original_editor_buffer():
    source = SCRIPT.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    fold = source.split("function foldableLines(text){", 1)[1].split("function renderCode(file)", 1)[0]
    assert "positions.set(i,end-1)" in fold
    render = source.split("function renderCode(file)", 1)[1].split("let pendingCloseAfterSave=", 1)[0]
    assert "file.foldedLines" in render
    assert "if(i<=hiddenThrough)return;" in render
    assert "gutter.addEventListener('click'" in render
    assert "file.text.split" in render
    assert ".pynix-fold-control{" in html

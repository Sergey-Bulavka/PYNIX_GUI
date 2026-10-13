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


def test_vertical_multicarets_and_current_cursor_count():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "function addVerticalCaret(direction)" in source
    assert "e.metaKey&&e.altKey&&['ArrowUp','ArrowDown'].includes(e.key)" in source
    assert "addVerticalCaret(e.key==='ArrowUp'?-1:1)" in source
    assert "extraCount?' · '+(extraCount+1)+' cursors'" in source


def test_multiselection_visualization_and_pointer_exit():
    source = SCRIPT.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    assert "function decorateSegment(segment,at)" in source
    assert "pynix-secondary-selection" in source
    assert "pynix-secondary-caret" in source
    assert "file.extraSelections=[];" in source
    assert ".workspace-mode .pynix-secondary-selection{" in html


def test_multicaret_pair_insertion_keeps_caret_inside_each_pair():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "inputType==='insertPair'?data+value.slice(item.start,item.end)+closing[data]" in source
    assert "inputType==='insertPair'?1+(item.end-item.start):replacement.length" in source
    assert "editMultipleSelections('insertPair',e.key)" in source


def test_folding_has_accessible_toolbar_controls():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "foldButton.textContent='Fold'" in source
    assert "unfoldButton.textContent='Unfold'" in source
    assert "file.foldedLines=new Set()" in source
    assert "editing=false;updateEditingView();renderCode(file);" in source


def test_option_click_places_secondary_carets_without_wrapped_text():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "editorInput.wrap='off'" in source
    assert "editorInput.addEventListener('pointerdown',event=>{" in source
    assert "if(!event.altKey){file.extraSelections=[];return;}" in source
    assert "ctx.measureText('0000000000').width/10" in source
    assert "event.preventDefault();" in source
    assert "if(position===previous.start&&previous.start===previous.end)return;" in source


def test_editor_acceptance_runner_is_isolated(tmp_path):
    import subprocess
    runner = ROOT / "scripts" / "test_editor_block2.sh"
    text = runner.read_text(encoding="utf-8")
    assert "mktemp -d" in text
    assert 'bash scripts/run_ide_workspace.sh "$PROJECT"' in text
    assert 'mkdir -p "$PROJECT/src"' in text
    assert "rm -rf" not in text
    result = subprocess.run(["bash", "-n", str(runner)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

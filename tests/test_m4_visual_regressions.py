"""M4: native resizing and explorer highlight visual contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_native_workspace_remains_resizable_below_legacy_minimum():
    native = (ROOT / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert "AppKit.NSWindowStyleMaskResizable" in native
    assert "window.setMinSize_(AppKit.NSMakeSize(760, 520))" in native
    assert "AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable" in native


def test_explorer_active_and_selected_are_distinct():
    script = (ROOT / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (ROOT / "examples" / "icon_direction_preview.html").read_text(encoding="utf-8")
    assert "entry.path===(selectedPath??current)" in script
    assert "line.classList.add('workspace-selected')" in script
    assert "line.classList.add('workspace-active')" not in script
    assert ".workspace-mode .project-entry.workspace-selected{background:" in html
    assert "box-shadow:none" in html


def test_explorer_hover_does_not_mimic_another_selected_row():
    html = (ROOT / "examples" / "icon_direction_preview.html").read_text(encoding="utf-8")
    assert ".workspace-mode .project-entry:not(.workspace-selected):hover{background:transparent}" in html
    assert ".workspace-mode .project-entry:hover{background:#1e3046}" not in html
    assert ".workspace-mode .project-entry.workspace-selected:hover{background:#223f5e}" in html


def test_legacy_fifth_entry_demo_highlight_does_not_bleed_into_explorer():
    html = (ROOT / "examples" / "icon_direction_preview.html").read_text(encoding="utf-8")
    assert ".entry:nth-of-type(5){background:#1d3048}" in html
    assert ".workspace-mode .tree .project-entry:not(.workspace-selected){background:transparent}" in html
    assert html.index(".workspace-mode .tree .project-entry:not(.workspace-selected)") > html.index(
        ".entry:nth-of-type(5){background:#1d3048}")


def test_editor_bracket_pairs_wrap_selection_and_skip_existing_closer():
    preview = (ROOT / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    editor = preview.split("editorInput.addEventListener('keydown',e=>{", 1)[1].split(
        "const coreSyncTimers=", 1)[0]
    assert "const pairs={'(' : ')','[' : ']','{' : '}'};" in editor
    assert "e.key+selected+pairs[e.key]" in editor
    assert "editorInput.setSelectionRange(start+1,start+1+selected.length)" in editor
    assert "editorInput.value[start]===e.key" in editor
    assert "if(!e.metaKey&&!e.ctrlKey&&!e.altKey&&!e.isComposing)" in editor

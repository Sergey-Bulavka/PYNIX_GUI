"""Real V4 tab menu: compact PyCharm sizing, selectable hover, and actions."""
from pathlib import Path
import shutil
import subprocess

import pytest

from pynix_gui.ide_editor_tab_advanced import TAB_ADVANCED_JS
from pynix_gui.ide_editor_tab_controls import TAB_CONTROL_JS
from pynix_gui.ide_pycharm_chrome import CHROME_STYLE
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession


def test_menu_geometry_does_not_regress_to_oversized_blank_rows():
    css=CHROME_STYLE.split("/* V4 PyCharm tab-action menu:",1)[1]
    assert "width:min(262px,calc(100vw - 12px))!important" in css
    assert "min-height:29px!important;height:29px!important" in css
    assert "font:400 13px/20px" in css
    assert "font:500 13.5px/20px" in css
    assert "width:18px!important;height:18px!important" in css
    assert "width:17px!important;height:17px!important" in css
    assert ".pynix-tabs-menu-row:is(" in css
    assert ":hover,:focus-within,.pynix-keyboard-selected" in css
    assert "background:#304d7b!important" in css
    assert "background:transparent!important;color:#f0f2f7!important" in css
    assert "const items=[...popup.querySelectorAll" in TAB_CONTROL_JS
    assert "items[next]?.focus();" in TAB_CONTROL_JS


def test_all_reference_menu_commands_route_to_real_editor_implementations():
    for expected in (
        "row('Bookmark Open Tabs...',bookmarkOpenTabs",
        "if(bookmarked.length)row('Open Bookmarked Tabs...'",
        "row('Configure Editor Tabs...',()=>openMenu('preferences'))",
        "row(pref.minimap?'Hide Minimap':'Show Minimap',toggleMinimap)",
        "if(menu==='bookmarks'){paintBookmarks();return;}",
        "if(menu==='preferences'){paintPreferences();return;}",
        "openMenu(event.shiftKey?'locations':'recent')",
        "window.pynixOpenSearchEverywhere?.()",
    ):
        assert expected in TAB_CONTROL_JS,expected
    for absent in ("row('Bookmark Open Tabs...',null",
                   "row('Configure Editor Tabs...',null",
                   "row('Show Minimap',null"):
        assert absent not in TAB_CONTROL_JS


def test_bookmark_sets_persist_and_restore_through_real_open_file_path():
    for expected in (
        "const optionsKey='pynix.ide.tabs.v1:'+PROJECT_PATH;",
        "localStorage.getItem(optionsKey)",
        "localStorage.setItem(optionsKey,JSON.stringify({",
        "files:[...openTabs]",
        "const restoreBookmarks=entry=>{",
        "if(byName.has(name))show(name);",
        "const paintBookmarks=()=>{",
        "saveOptions();paint();position();",
        "const answer=window.prompt(",
    ):
        assert expected in TAB_ADVANCED_JS, expected


def test_tab_preferences_are_actual_visual_controls():
    for name in ("compact", "icons", "closeAlways"):
        assert "'"+name+"'" in TAB_ADVANCED_JS
    assert "tabs.dataset.pynixCompact=String(pref.compact)" in TAB_ADVANCED_JS
    assert "tabs.dataset.pynixIcons=String(pref.icons)" in TAB_ADVANCED_JS
    assert "tabs.dataset.pynixClose=String(pref.closeAlways)" in TAB_ADVANCED_JS
    for selector in ('[data-pynix-icons="false"]',
                     '[data-pynix-close="true"]',
                     '[data-pynix-compact="true"]'):
        assert selector in CHROME_STYLE


def test_minimap_renders_current_buffer_and_supports_interactive_scrolling():
    for part in (
        "const miniCanvas=document.createElement('canvas');",
        "const drawMinimap=()=>{",
        "mini.hidden=!pref.minimap;",
        "ctx.fillRect(x,i*scale",
        "ctx.strokeRect(",
        "const target=scrollHost();",
        "target.scrollTop=Math.round(position*max)",
        "editorInput.addEventListener('input',scheduleMinimap)",
        "code.addEventListener('scroll',scheduleMinimap,true)",
        "new ResizeObserver(scheduleMinimap).observe(editorHost)",
        "const toggleMinimap=()=>setMinimap(!pref.minimap)",
    ):
        assert part in TAB_ADVANCED_JS, part
    for style in (".workspace-mode .pynix-editor-minimap{",
                  ".workspace-mode .pynix-editor-minimap[hidden]",
                  "position:absolute!important;z-index:21!important"):
        assert style in CHROME_STYLE


def test_integrated_workspace_javascript_parses_under_node(tmp_path):
    node=shutil.which("node")
    if not node:
        pytest.skip("Node.js unavailable")
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    js=workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "__PYNIX_ADVANCED_TABS__" not in js
    assert "const bookmarked=" not in js  # declared with let for deletion/reordering
    assert "let bookmarked=Array.isArray(" in js
    script=js.split("<script>",1)[1].split("</script>",1)[0]
    result=subprocess.run([node,"--check"],input=script,text=True,
                          encoding="utf-8",capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr

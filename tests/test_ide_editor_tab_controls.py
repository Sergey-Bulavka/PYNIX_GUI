"""Active IDE V4 tab overflow and menu. No fake duplicate tab model."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from pynix_gui.ide_editor_tab_controls import TAB_CONTROL_JS
from pynix_gui.ide_pycharm_chrome import CHROME_STYLE
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession


def test_overflow_planner_keeps_current_and_hides_only_unfitted_tabs():
    node=shutil.which("node")
    if not node:
        pytest.skip("Node.js needed for live JS overflow tests")
    planner=TAB_CONTROL_JS[:TAB_CONTROL_JS.index(" const tabControls=(()=>{")]
    query="global.window={};\n"+planner+"""
const test=(widths,space,active)=>planTabOverflow(widths,space,active);
console.log(JSON.stringify([
 test([110,120,140],500,2),
 test([110,120,140],230,2),
 test([110,120,140],120,1),
 test([150,130,120],0,0),
 test([110],100,0)
]));
"""
    result=subprocess.run([node,"-e",query],capture_output=True,
                          text=True,encoding="utf-8",timeout=20)
    assert result.returncode==0,result.stderr
    values=json.loads(result.stdout)
    assert values[0]==[]
    assert 2 not in values[1] and values[1]
    assert 1 not in values[2] and values[2]
    assert values[3]==[1,2]
    assert values[4]==[]


def test_runtime_uses_real_tab_identity_and_native_close_safety(tmp_path):
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    script=workspace_bootstrap(WorkspaceSession(tmp_path))
    for text in (
        "const planTabOverflow=",
        "window.pynixPlanTabOverflow=planTabOverflow",
        "const tabControls=(()=>{",
        "tabControls.strip.replaceChildren();",
        "tabControls.strip.appendChild(wrap);",
        "tabControls.schedule();",
        "tabControls.visited(name);",
        "tabControls.tabDidClose(name);",
        "const cancel=button('Cancel',()=>{tabControls.stopBulk();dismiss();});",
        "tabControls.stopBulk();",
        "row('Close All Tabs'",
        "row('Close Unmodified Tabs'",
        "row('Reopen Closed Tab'",
        "requestCloseTab(name)",
        "new ResizeObserver(schedule).observe(tabs);",
    ):
        assert text in script,text
    assert "__PYNIX_TAB_CONTROLS__" not in script
    assert "tabs.replaceChildren(strip,actions);" in TAB_CONTROL_JS
    assert "tabs.replaceChildren();" not in script[script.index(" function renderTabs(){"):
                                                      script.index(" function show(name)")]
    assert script.count("const tabControls=(()=>{")==1


def test_menu_matches_reference_but_unimplemented_actions_are_disabled():
    for label in (
        "Show Hidden Tabs",
        "Recent Files, Tab Actions, and More",
        "Recent Files",
        "Recent Locations",
        "Go to File...",
        "Close All Tabs",
        "Close Unmodified Tabs",
        "Reopen Closed Tab",
        "Bookmark Open Tabs...",
        "Configure Editor Tabs...",
        "Show Minimap",
    ):
        assert label in TAB_CONTROL_JS,label
    assert "row('Recent Locations',()=>openMenu('locations')" in TAB_CONTROL_JS
    assert "recordLocation=()=>{" in TAB_CONTROL_JS
    assert "selectNavigationLocation({" in TAB_CONTROL_JS
    assert "row('Bookmark Open Tabs...',null,{disabled:true})" in TAB_CONTROL_JS
    assert "row('Configure Editor Tabs...',null,{disabled:true})" in TAB_CONTROL_JS
    assert "row('Show Minimap',null,{disabled:true})" in TAB_CONTROL_JS
    assert "window.pynixOpenSearchEverywhere?.()" in TAB_CONTROL_JS
    assert "popup.setAttribute('role','menu')" in TAB_CONTROL_JS
    assert "button.setAttribute('aria-label'" not in TAB_CONTROL_JS


def test_chrome_does_not_allow_popups_to_be_clipped_or_overflow_button_to_show_when_hidden():
    for rule in (
        ".editor-tabs .pynix-tabs-strip",
        ".editor-tabs .pynix-tabs-actions",
        ".editor-tabs .pynix-tabs-action[hidden]",
        ".editor-tabs .pynix-editor-tab[hidden]",
        ".workspace-mode>.pynix-tabs-popup",
        ".workspace-mode>.pynix-tabs-popup[hidden]",
        ".pynix-tabs-menu-row.active",
        ".pynix-tabs-menu-item:disabled",
        ".pynix-tabs-menu-shortcut",
    ):
        assert rule in CHROME_STYLE,rule
    assert "position:fixed;z-index:11000" in CHROME_STYLE
    assert "popup.hidden=true;document.body.appendChild(popup)" in TAB_CONTROL_JS
    assert "hiddenButton.hidden=true" in TAB_CONTROL_JS


def test_js_bundle_compiles_as_single_workspace_script(tmp_path):
    node=shutil.which("node")
    if not node:
        pytest.skip("Node.js unavailable")
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    html=workspace_bootstrap(WorkspaceSession(tmp_path))
    script=html.split("<script>",1)[1].split("</script>",1)[0]
    result=subprocess.run([node,"--check"],input=script,capture_output=True,
                          text=True,encoding="utf-8",timeout=20)
    assert result.returncode==0,result.stderr

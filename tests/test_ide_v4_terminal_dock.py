"""Native V4 Terminal dock: distinct, real tools with no false shared state."""
from pathlib import Path
import shutil
import subprocess

import pytest

from pynix_gui.ide_terminal_dock import TERMINAL_DOCK_JS
from pynix_gui.ide_pycharm_chrome import CHROME_STYLE, apply_pycharm_chrome
from pynix_gui.ide_edge_profile import EXISTING_ACTIONS
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession


def test_two_real_tool_window_actions_never_alias():
    assert EXISTING_ACTIONS["Terminal"]=="terminal:system"
    assert EXISTING_ACTIONS["PYNIX Terminal"]=="terminal:pynix"
    assert "window.pynixTerminalDock={" in TERMINAL_DOCK_JS
    assert "state:()=>({scope,visible:isVisible()})" in TERMINAL_DOCK_JS
    assert "window.dispatchEvent(new CustomEvent('pynix:terminal-change',{detail}))" in TERMINAL_DOCK_JS
    assert "const select=id=>{" in TERMINAL_DOCK_JS
    assert "scope===id&&isVisible()" in TERMINAL_DOCK_JS


def test_pycharm_shell_header_keeps_functional_buttons():
    for expected in (
        "title.className='pynix-terminal-dock-title'",
        "newSession.title='New Tab (⌘T)'",
        "newSession.addEventListener('click',()=>createShell(defaultShell))",
        "summary.className='pynix-terminal-dock-action pynix-terminal-shell-chevron'",
        "summary.innerHTML='<svg viewBox=",
        "for(const shell of ['bash','zsh'])",
        "menuButton(popup,'Settings'",
        "function createShell(shell){",
        "native({scope:'shell',action:'create',shell})",
        "const shellTabs=new Map()",
        "paintSessions();paintShell()",
        "const pynix=makePanel('pynix-language-terminal'",
        "native({scope:'pynix',action:'execute',command})",
    ):
        assert expected in TERMINAL_DOCK_JS,expected
    assert "newSession.disabled=true" not in TERMINAL_DOCK_JS


def test_project_tree_and_editor_reclaim_space_when_dock_hidden():
    css=CHROME_STYLE
    assert "Native V4 PyCharm terminal tool-window:" in css
    assert ".integrated-terminal.pynix-tool-window-collapsed{" in css
    assert "display:none!important;height:0!important;min-height:0!important;" in css
    assert ".terminal-resizer[hidden]{" in css
    assert ".integrated-terminal .terminal-console[hidden]" in css
    assert ".integrated-terminal .pynix-system-terminal[hidden]" in css
    assert ".integrated-terminal .pynix-language-terminal[hidden]" in css
    assert ".pynix-terminal-new,.workspace-mode .pynix-terminal-shell-dropdown{" in css
    assert ".integrated-terminal:hover .pynix-terminal-new" in css
    assert ".integrated-terminal:focus-within .pynix-terminal-shell-dropdown" in css


def test_real_workspace_mounts_only_one_dock_controller(tmp_path):
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    html=workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "__PYNIX_TERMINAL_DOCK__" not in html
    assert html.count("window.pynixTerminalDock={")==1
    assert "window.pynixTerminalDock?.sync();" in html
    assert "window.pynixTerminalNativeEvent=event=>" in html
    assert "setToolWindowVisible(false);" in html
    assert "const toolViews=new Map();" in html
    assert "scope='other';sync();" in html
    assert "selectedTool='TERMINAL'" in html


def test_full_workspace_javascript_is_valid(tmp_path):
    node=shutil.which("node")
    if not node:
        pytest.skip("Node not available")
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    page=workspace_bootstrap(WorkspaceSession(tmp_path))
    source=page.split("<script>",1)[1].split("</script>",1)[0]
    run=subprocess.run([node,"--check"],input=source,text=True,
                       capture_output=True,timeout=20,encoding="utf-8")
    assert run.returncode==0,run.stderr
    chrome=apply_pycharm_chrome('<html><body class="workspace-mode"></body></html>',
                                iconless=True)
    assert ".pynix-terminal-shell-chevron svg" in chrome

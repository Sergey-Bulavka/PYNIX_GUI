"""Separate Terminal / PYNIX Terminal semantics and real local sessions."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from pynix_gui.ide_edge_profile import EXISTING_ACTIONS, EDGE_PROFILE_SCRIPT
from pynix_gui.ide_terminal_dock import TERMINAL_DOCK_JS
from pynix_gui.ide_terminal_sessions import (
    LocalTerminalSessions, TerminalSessionError, PynixCommandConsole,
)
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession


def test_pynix_and_system_terminal_have_distinct_commands_and_selection():
    assert EXISTING_ACTIONS["Terminal"] == "terminal:system"
    assert EXISTING_ACTIONS["PYNIX Terminal"] == "terminal:pynix"
    assert "window.pynixTerminalDock?.select(command.slice(9))" in EDGE_PROFILE_SCRIPT
    assert "window.addEventListener('pynix:terminal-change',sync)" in EDGE_PROFILE_SCRIPT
    assert "state.visible&&state.scope===scope" in EDGE_PROFILE_SCRIPT
    assert "const select=id=>{" in TERMINAL_DOCK_JS
    assert "scope===id&&isVisible()" in TERMINAL_DOCK_JS
    assert "setToolWindowVisible(false)" in TERMINAL_DOCK_JS
    assert "window.pynixTerminalDock={" in TERMINAL_DOCK_JS


def test_shell_tabs_and_menu_are_real_not_disabled_or_shared_output():
    for value in (
        "pynix-terminal-shell-chevron",
        '<svg viewBox="0 0 16 16"',
        "function createShell(shell){",  # prefer function if implementation changes
        "scope:'shell',action:'create'",
        "scope:'shell',action:'write'",
        "scope:'shell',action:'poll'",
        "scope:'shell',action:'close'",
        "for(const shell of ['bash','zsh'])",
        "menuButton(popup,'Settings'",
        "shellTabs.size===0?'Local':'Local '+serial",
        "const shellTabs=new Map()",
        "const pynix=makePanel('pynix-language-terminal'",
        "pynix.input.addEventListener('keydown'",
        "scope:'pynix',action:'execute'",
        "pynix-terminal-new",
        "pynix-terminal-shell-dropdown",
    ):
        assert value in TERMINAL_DOCK_JS, value
    assert "newSession.disabled=true" not in TERMINAL_DOCK_JS
    assert "local.textContent='Local'" not in TERMINAL_DOCK_JS


def test_embedded_workspace_script_is_valid_javascript(tmp_path):
    node=shutil.which("node")
    if not node:
        pytest.skip("Node unavailable")
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    document=workspace_bootstrap(WorkspaceSession(tmp_path))
    script=document.split("<script>",1)[1].split("</script>",1)[0]
    result=subprocess.run([node,"--check"],text=True,encoding="utf-8",
                          input=script,capture_output=True,timeout=20)
    assert result.returncode == 0, result.stderr
    assert "__PYNIX_TERMINAL_DOCK__" not in document
    assert "window.pynixTerminalNativeEvent=event=>" in document


def test_compiler_console_commands_are_isolated_and_validate_project_paths(tmp_path):
    compiler=tmp_path/"compiler";compiler.mkdir()
    (compiler/"__main__.py").write_text(
        "import sys\nprint('PYNIX-RUN',sys.argv[1:])\n",encoding="utf-8")
    (tmp_path/"hello.pnx").write_text("function main()\n",encoding="utf-8")
    console=PynixCommandConsole(tmp_path,Path(sys.executable))
    assert "not a Python shell" in console.execute("help")
    assert str(tmp_path) == console.execute("pwd")
    assert "hello.pnx" in console.execute("files")
    assert "PYNIX-RUN" in console.execute("run hello.pnx")
    assert "outside" in console.execute("run ../outside.pnx") or "Only existing" in console.execute("run ../outside.pnx")
    assert "Unknown" in console.execute("import os")
    assert "Unknown" in console.execute("rm -rf .")


@pytest.mark.skipif(os.name!="posix" or not Path("/bin/bash").exists(),
                    reason="POSIX/bash PTY required")
def test_each_terminal_tab_is_a_real_independent_shell_process(tmp_path):
    service=LocalTerminalSessions(tmp_path)
    try:
        first=service.create("bash")["id"]
        second=service.create("bash")["id"]
        assert first!=second
        service.write(first,"printf 'SHELL_TAB_ONE_READY\\n'\n")
        service.write(second,"printf 'SHELL_TAB_TWO_READY\\n'\n")
        outputs={first:"",second:""}
        deadline=time.monotonic()+7
        while time.monotonic()<deadline:
            for sid in outputs:
                outputs[sid]+=service.poll(sid)["data"]
            if "SHELL_TAB_ONE_READY" in outputs[first] and "SHELL_TAB_TWO_READY" in outputs[second]:
                break
            time.sleep(0.05)
        assert "SHELL_TAB_ONE_READY" in outputs[first], repr(outputs[first])
        assert "SHELL_TAB_TWO_READY" in outputs[second], repr(outputs[second])
        assert service.close(first)["kind"]=="closed"
        assert second in service._sessions
        with pytest.raises(TerminalSessionError):
            service.write(first,"echo NO\n")
    finally:
        service.shutdown()


def test_native_backend_bridge_is_registered_without_pretending_to_support_windows():
    source=(Path(__file__).resolve().parents[1]/
            "examples/ide_native_v4.py").read_text(encoding="utf-8")
    for name in (
        "LocalTerminalSessions(session.root)",
        "PynixCommandConsole(session.root, command_python)",
        'terminal_session_handler, "pynixTerminalSession"',
        "window.pynixTerminalNativeEvent?.(",
        'native_shells.create(str(request.get("shell", "")))',
        'native_shells.poll(str(request.get("id", "")))',
        "run_threading.Thread(target=worker, daemon=True).start()",
    ):
        assert name in source, name


def test_terminal_scope_switches_without_activating_both_tools():
    """Exercise selection logic in Node, not only its string signature."""
    node=shutil.which("node")
    if not node:
        pytest.skip("Node not available")
    start=TERMINAL_DOCK_JS.index("  const select=id=>{")
    end=TERMINAL_DOCK_JS.index("  window.pynixTerminalDock={",start)
    select_source=TERMINAL_DOCK_JS[start:end]
    setup=r"""
let scope='other',open=false,spawnCount=0,events=[];
const system={input:{focus(){}}},pynix={input:{focus(){}}};
const shellTabs=new Map(),pynixTabs=new Map();
let defaultShell='zsh';
const isVisible=()=>open;
const createShell=()=>{spawnCount++;};
const createPynixTab=()=>{pynixTabs.set('pynix-1',{});};
const packagesOnShow=()=>{};
const servicesOnShow=()=>{};
const setToolWindowVisible=value=>{
 open=value;events.push({scope,open});
};
"""
    assertion=r"""
select('system');
if(!open||scope!=='system'||spawnCount!==1)throw Error('system not opened');
select('pynix');
if(!open||scope!=='pynix'||spawnCount!==1)throw Error('PYNIX must not inherit shell');
select('pynix');
if(open||scope!=='pynix')throw Error('second PYNIX click must hide');
select('system');
if(!open||scope!=='system')throw Error('system must re-open');
console.log(JSON.stringify(events));
"""
    result=subprocess.run([node,"-e",setup+select_source+assertion],
                          text=True,encoding="utf-8",capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr

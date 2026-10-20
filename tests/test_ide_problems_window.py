"""Problems tool window: native wiring, source navigation, safe diagnostics."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from pynix_gui.ide_problems_window import (
    PROBLEMS_CSS, PROBLEMS_JS, apply_problems_window,
)
from pynix_gui.ide_edge_profile import EDGE_PROFILE_SCRIPT
from pynix_gui.ide_terminal_dock import TERMINAL_DOCK_JS
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession
from pynix_gui.ide_tooling_diagnostics import Problem, read_diagnostics


def test_problems_is_a_separate_dock_tool_and_not_terminal_buffer():
    assert "window.pynixTerminalDock?.toggleProblems?.();" in EDGE_PROFILE_SCRIPT
    assert "const showProblems=()=>{" in TERMINAL_DOCK_JS
    assert "const toggleProblems=()=>{" in TERMINAL_DOCK_JS
    assert "activateToolView('PROBLEMS');" in TERMINAL_DOCK_JS
    assert "scope='other';" in TERMINAL_DOCK_JS
    assert "showProblems,toggleProblems" in TERMINAL_DOCK_JS
    assert "pynix-problems-active" in PROBLEMS_CSS
    assert "window.pynixLiveDiagnosticsResult=receiveDiagnostics;" in PROBLEMS_JS


def test_problems_installs_only_once_and_handles_missing_body():
    base="<html><body class='workspace-mode'><div>IDE</div></body></html>"
    result=apply_problems_window(base)
    assert 'id="pynix-problems-controller"' in result
    assert apply_problems_window(result)==result
    with pytest.raises(ValueError, match="HTML body"):
        apply_problems_window("<html><head></head></html>")


def test_problems_js_is_valid_and_supports_file_project_and_navigation(tmp_path):
    node=shutil.which("node")
    if node:
        source=PROBLEMS_JS.split("<script id=\"pynix-problems-controller\">",1)[1].split("</script>",1)[0]
        path=tmp_path/"problems.js"
        path.write_text(source,encoding="utf-8")
        checked=subprocess.run([node,"--check",str(path)],capture_output=True,
                               text=True,timeout=20)
        assert checked.returncode==0,checked.stderr
    for marker in (
        "const tabs=['File','Project Errors','AI Self-Review']",
        "window.pynixGetActiveSource?.()",
        "pynixGetProblemPreview",
        "e.key==='F4'",
        "e.key==='ArrowDown'",
        "pynix:navigate",
        "selectedTab==='Project Errors'",
        "Show errors",
        "Show warnings",
        "Sort by severity",
        "Read-only preview",
        "not connected. No AI analysis results",
        "Quick fixes unavailable",
        "Checking saved project",
    ):
        assert marker in PROBLEMS_JS,marker


def test_workspace_connects_file_switch_save_and_preview(tmp_path):
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    markup=workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "window.pynixGetActiveSource=()=>current;" in markup
    assert "window.pynixGetProblemPreview=source=>" in markup
    assert "new CustomEvent('pynix:file-opened'" in markup
    assert "window.pynixProblems?.receiveDiagnostics?.({" in markup
    assert "window.pynixTerminalDock?.state()?.tool!=='PROBLEMS'" in markup


def test_native_installs_problems_after_chrome_and_runs_diagnostics_async():
    native=(Path(__file__).resolve().parents[1]/"examples"/"ide_native_v4.py").read_text()
    assert "document = apply_problems_window(document)" in native
    assert native.index("document = apply_pycharm_chrome(document)") < native.index(
        "document = apply_problems_window(document)")
    assert "run_threading.Thread(target=worker, daemon=True).start()" in native
    assert 'NSOperationQueue.mainQueue().addOperationWithBlock_(publish)' in native
    assert '"severity": p.severity' in native


def test_diagnostic_severity_from_tooling_is_preserved(monkeypatch,tmp_path):
    (tmp_path/"pynix.toml").write_text("[project]\n",encoding="utf-8")
    interpreter=tmp_path/"python"
    interpreter.write_text("",encoding="utf-8")
    packet={"protocol":"pynix-tooling","version":1,"kind":"diagnostics",
            "diagnostics":[
                {"source":"main.pnx","code":"W101","message":"Unused name",
                 "severity":"warning","start":{"line":3,"column":4}},
                {"source":"main.pnx","code":"E102","message":"Unknown name",
                 "start":{"line":7,"column":8}}]}
    monkeypatch.setattr("pynix_gui.ide_tooling_diagnostics.subprocess.run",
                        lambda *args,**kwargs: SimpleNamespace(
                            returncode=0,stdout=json.dumps(packet)))
    snapshot=read_diagnostics(tmp_path,interpreter)
    assert snapshot.error==""
    assert snapshot.problems==(
        Problem("main.pnx",3,4,"W101","Unused name","warning"),
        Problem("main.pnx",7,8,"E102","Unknown name","error"),
    )

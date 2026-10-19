"""IDE Run/Stop unit and integration contracts."""
from pathlib import Path
from io import StringIO
from types import SimpleNamespace
import pytest

from pynix_gui.ide_project_runner import ProjectRunner, RunError


def test_runner_rejects_project_without_manifest(tmp_path):
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    with pytest.raises(RunError, match="manifest"):
        ProjectRunner(tmp_path, python).start()


def test_runner_invokes_compiler_without_shell(tmp_path, monkeypatch):
    (tmp_path / "pynix.toml").write_text("[project]\nname='demo'\n")
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    captured = []
    class FakeProcess:
        returncode = 0
        stdout = StringIO("hello\n")
        def poll(self): return 0
        def wait(self, timeout=None): return 0
    def fake_popen(command, **kwargs):
        captured.append((command, kwargs))
        return FakeProcess()
    monkeypatch.setattr("pynix_gui.ide_project_runner.subprocess.Popen", fake_popen)
    runner = ProjectRunner(tmp_path, python)
    runner.start()
    chunks = []
    result = runner.collect(on_output=chunks.append)
    assert captured[0][0] == [str(python), "-u", "-m", "compiler", "run", str(tmp_path)]
    assert captured[0][1]["stdin"] is not None
    assert "shell" not in captured[0][1]
    assert result["output"] == "hello\n"
    assert chunks == ["hello\n"]
    assert result["exitCode"] == 0


def test_native_run_stop_wiring_and_dirty_buffer_guard():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert 'controller.addScriptMessageHandler_name_(project_run_handler, "pynixProjectRun")' in native
    assert "project_runner.close()" in native
    assert "run_threading.Thread(target=worker, daemon=True).start()" in native
    assert "window.pynixProjectRunResult=packet=>" in preview
    assert "file=>file.dirty" in preview
    assert "renderRunOutputLinks(consolePanel,(packet.output||'')" in preview


def test_native_controller_publishes_chunks():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert 'result = project_runner.collect(on_output=deliver)' in native
    assert '{"state": "output", "chunk": chunk}' in native
    assert "else if(state==='output')" in preview
    assert "consolePanel.scrollTop=consolePanel.scrollHeight" in preview


def test_restart_is_generation_guarded_and_nonblocking():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert 'elif action in ("stop", "restart"):' in native
    assert 'if action == "restart":' in native
    assert 'run_generation["value"] == generation' in native
    assert "run_threading.Thread(target=stop_or_restart, daemon=True).start()" in native
    assert "restartButton.textContent='Restart'" in preview
    assert "const prior=action==='restart'?lastRunRequest:null;" in preview
    assert "const source=prior?(prior.source||null)" in preview
    assert "bridge.postMessage(request)" in preview


def test_run_error_locations_are_clickable_and_bounded():
    root = Path(__file__).resolve().parents[1]
    source = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "function renderRunOutputLinks(panel,output)" in source
    assert "window.pynixIndexedSources||[]" in source
    assert "split('\\\\n').slice(0,4000)" in source
    assert "jump.addEventListener('click'" in source
    assert "new CustomEvent('pynix:navigate'" in source



def test_runner_check_configuration_uses_pinned_compiler(tmp_path, monkeypatch):
    from io import StringIO
    (tmp_path / "pynix.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    commands = []
    class FakeProcess:
        returncode = 0
        stdout = StringIO("No issues\n")
        def poll(self): return 0
        def wait(self, timeout=None): return 0
    def fake_popen(command, **kwargs):
        commands.append((command, kwargs))
        return FakeProcess()
    monkeypatch.setattr("pynix_gui.ide_project_runner.subprocess.Popen", fake_popen)
    runner = ProjectRunner(tmp_path, python)
    runner.start(mode="check")
    assert commands[0][0] == [str(python), "-u", "-m", "compiler", "check", str(tmp_path)]
    assert runner.collect()["exitCode"] == 0
    with pytest.raises(RunError, match="Unsupported run configuration"):
        runner.start(mode="--arbitrary")


def test_run_configuration_is_restricted_at_native_and_ui_boundaries():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert 'if mode not in ("run", "check"):' in native
    assert 'start_project_run(mode, source)' in native
    assert "runModeSelect.setAttribute('aria-label','PYNIX run configuration')" in preview
    assert "['run','Run project']" in preview
    assert "['check','Check project']" in preview
    assert "bridge.postMessage({action,mode})" in preview
    assert "bridge.postMessage(request)" in preview
    assert "['file','Current File']" in preview
    assert "const source=prior?(prior.source||null)" in preview


def test_run_current_pynix_file_invokes_single_file_compiler(tmp_path, monkeypatch):
    source = tmp_path / "src" / "main.pnx"
    source.parent.mkdir()
    source.write_text('print("hello")', encoding="utf-8")
    python = tmp_path / "compiler_python"
    python.write_text("", encoding="utf-8")
    calls = []

    class FakeProcess:
        returncode = 0
        stdout = StringIO("hello\\n")
        def poll(self): return 0
        def wait(self, timeout=None): return 0

    monkeypatch.setattr(
        "pynix_gui.ide_project_runner.subprocess.Popen",
        lambda command, **kwargs: (calls.append((command, kwargs)) or FakeProcess()),
    )
    runner = ProjectRunner(tmp_path, python)
    runner.start(source="src/main.pnx")
    assert calls[0][0] == [
        str(python), "-u", "-m", "compiler", "run", str(source), "--single-file"
    ]
    assert calls[0][1]["cwd"] == tmp_path
    assert runner.collect()["exitCode"] == 0


def test_run_current_python_file_uses_project_interpreter(tmp_path, monkeypatch):
    script = tmp_path / "test_diagnostics.py"
    script.write_text("print('OK')", encoding="utf-8")
    venv_python = tmp_path / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")
    compiler_python = tmp_path / "compiler_python"
    compiler_python.write_text("", encoding="utf-8")
    calls = []

    class FakeProcess:
        returncode = 0
        stdout = StringIO("OK\\n")
        def poll(self): return 0
        def wait(self, timeout=None): return 0

    monkeypatch.setattr(
        "pynix_gui.ide_project_runner.subprocess.Popen",
        lambda command, **kwargs: (calls.append(command) or FakeProcess()),
    )
    runner = ProjectRunner(tmp_path, compiler_python)
    runner.start(source="test_diagnostics.py")
    assert calls == [[str(venv_python), "-u", str(script)]]
    assert runner.collect()["output"] == "OK\\n"


@pytest.mark.parametrize("source", [
    "../outside.py", "/tmp/outside.py", "missing.pnx",
    "project/config.toml", "main.pnx;rm -rf .", "",
])
def test_run_current_rejects_untrusted_source_paths(tmp_path, source):
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    runner = ProjectRunner(tmp_path, python)
    with pytest.raises(RunError):
        runner.start(source=source)


def test_run_current_rejects_symlink_outside_root(tmp_path):
    source = tmp_path.parent / "external_run.py"
    source.write_text("print('unsafe')", encoding="utf-8")
    (tmp_path / "external.py").symlink_to(source)
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    with pytest.raises(RunError):
        ProjectRunner(tmp_path, python).start(source="external.py")


def test_native_run_buttons_select_current_file_and_output_window():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    dock = (root / "pynix_gui/ide_terminal_dock.py").read_text(encoding="utf-8")
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    assert 'source not in available_sources' in native
    assert 'start_project_run(mode, source)' in native
    assert "window.pynixProjectRunResult=packet=>" in preview
    assert "window.pynixTerminalDock?.showRun?.();" in preview
    assert "consoleTab?.click()" not in preview
    assert "runActions.hidden=!(scope==='other'&&selectedTool==='TERMINAL')" in dock
    assert "document.querySelector('.pynix-stop-action')?.click()" in dock
    assert "setRunState:running=>" in dock
    assert "['file','Current File']" in chrome
    assert "['run','Run Project']" in chrome


def test_run_output_links_support_python_tracebacks_and_pynix_locations():
    preview = (
        Path(__file__).resolve().parents[1] /
        "pynix_gui" / "ide_workspace_preview.py"
    ).read_text(encoding="utf-8")
    assert r"\\.(?:pnx|py)" in preview
    assert 'line.match(/File ["\']' in preview
    assert "new CustomEvent('pynix:navigate'" in preview


def test_run_sidebar_does_not_switch_project_tree():
    root = Path(__file__).resolve().parents[1]
    edge = (root / "pynix_gui/ide_edge_profile.py").read_text(encoding="utf-8")
    dock = (root / "pynix_gui/ide_terminal_dock.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")

    assert '"Run": "run-window"' in edge
    assert "if(command==='run-window')" in edge
    assert "window.pynixTerminalDock?.toggleRun?.();" in edge
    assert '"Run": "rail:3"' not in edge

    assert "showRun,toggleRun" in dock
    assert "activateToolView('TERMINAL');" in dock
    assert "setToolWindowVisible(true);" in dock
    assert "const detail={scope,tool:selectedTool,visible:isVisible()};" in dock
    assert "state.tool==='TERMINAL'" in edge

    assert "window.pynixTerminalDock?.showRun?.();" in preview
    assert "consoleTab?.click()" not in preview
    assert "setToolWindowVisible(true);\n   consoleTab?.click();" not in preview
    assert "if(i===3&&document.body.classList.contains('workspace-mode'))" in html
    assert "window.pynixTerminalDock?.toggleRun?.();return;" in html


def test_current_file_regex_has_valid_python_string_escape():
    import ast
    root = Path(__file__).resolve().parents[1]
    preview_file = root / "pynix_gui/ide_workspace_preview.py"
    source = preview_file.read_text(encoding="utf-8")
    ast.parse(source)
    assert r"if(!/\\.(pnx|py)$/i.test(source)" in source
    assert r"if(!/\.(pnx|py)$/i.test(source)" not in source

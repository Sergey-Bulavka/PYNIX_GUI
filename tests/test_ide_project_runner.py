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
    assert "consolePanel.textContent=(packet.output||'')" in preview


def test_native_controller_publishes_chunks():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert 'on_output=lambda chunk: publish_run_result(' in native
    assert '{"state": "output", "chunk": chunk}' in native
    assert "else if(state==='output')" in preview
    assert "consolePanel.scrollTop=consolePanel.scrollHeight" in preview

import json
from pathlib import Path
from types import SimpleNamespace

from pynix_gui.ide_tooling_diagnostics import read_diagnostics, DiagnosticSnapshot, Problem
from pynix_gui.ide_workspace_preview import attach_diagnostics


def test_diagnostics_reads_public_tooling_v1(monkeypatch, tmp_path):
    (tmp_path / "pynix.toml").write_text("[project]\n", encoding="utf-8")
    python = tmp_path / "python"
    python.write_text("")
    data = {
        "protocol": "pynix-tooling", "version": 1, "kind": "diagnostics",
        "diagnostics": [{"source": "src/main.pnx", "code": "E123",
                         "message": "Unknown name", "start": {"line": 3, "column": 5}}]
    }
    captured = {}
    def run(cmd, **kwargs):
        captured["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout=json.dumps(data))
    monkeypatch.setattr("pynix_gui.ide_tooling_diagnostics.subprocess.run", run)
    result = read_diagnostics(tmp_path, python)
    assert result.error == ""
    assert result.problems == (Problem("src/main.pnx", 3, 5, "E123", "Unknown name"),)
    assert captured["cmd"][2:5] == ["compiler", "tooling", "diagnostics"]
    assert captured["cmd"][5] == str(tmp_path.resolve())
    assert not captured["cmd"][5].endswith(".toml")


def test_unavailable_compiler_is_nonfatal(tmp_path):
    assert "manifest" in read_diagnostics(tmp_path, tmp_path / "missing").error


def test_diagnostics_is_script_safe():
    snap = DiagnosticSnapshot((Problem("a.pnx", 1, 1, "E", "</script><script>bad()</script>"),))
    source = attach_diagnostics("<body></body>", snap)
    assert "</script><script>bad()" not in source
    assert "\\u003c/script" in source
    assert "row.textContent=text" in source


def test_native_window_exposes_explicit_diagnostics_mode():
    src = (Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py").read_text()
    assert '"--diagnostics"' in src
    assert '"--compiler-python"' in src
    assert "attach_diagnostics" in src


def test_tooling_target_is_project_not_manifest(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace
    (tmp_path / "pynix.toml").write_text("[project]\\n", encoding="utf-8")
    executable = tmp_path / "python"
    executable.write_text("")
    called = []
    def run(command, **kwargs):
        called.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            "protocol": "pynix-tooling", "version": 1,
            "kind": "diagnostics", "diagnostics": []}))
    monkeypatch.setattr("pynix_gui.ide_tooling_diagnostics.subprocess.run", run)
    result = read_diagnostics(tmp_path, executable)
    assert not result.error
    assert called[0][-1] == str(tmp_path.resolve())

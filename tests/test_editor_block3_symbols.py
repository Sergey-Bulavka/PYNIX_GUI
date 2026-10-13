"""Executable compiler-symbol completion adapter tests without a compiler process."""
import json
from pathlib import Path
from types import SimpleNamespace

from pynix_gui.ide_tooling_symbols import read_symbols


def test_symbols_adapter_accepts_public_protocol_and_bounds_entries(tmp_path, monkeypatch):
    (tmp_path / "pynix.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    interpreter = tmp_path / "python"
    interpreter.write_text("", encoding="utf-8")
    payload = {
        "protocol": "pynix-tooling", "version": 1, "kind": "symbols",
        "symbols": [
            {"name": "helper", "kind": "function"},
            {"name": "Widget", "kind": "class"},
            {"name": "<script>", "kind": "function"},
            {"name": "", "kind": "class"},
        ],
    }
    calls = []
    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload))
    monkeypatch.setattr("pynix_gui.ide_tooling_symbols.subprocess.run", fake_run)
    result = read_symbols(tmp_path, interpreter)
    assert result == {"symbols": [
        {"name": "helper", "kind": "function"},
        {"name": "Widget", "kind": "class"},
    ]}
    assert calls[0][0][2:5] == ["compiler", "tooling", "symbols"]
    assert calls[0][1]["timeout"] == 20


def test_symbols_adapter_rejects_unknown_protocol(tmp_path, monkeypatch):
    (tmp_path / "pynix.toml").write_text("[project]", encoding="utf-8")
    interpreter = tmp_path / "python"
    interpreter.write_text("", encoding="utf-8")
    def fake_run(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout='{"version":2,"symbols":[]}')
    monkeypatch.setattr("pynix_gui.ide_tooling_symbols.subprocess.run", fake_run)
    result = read_symbols(tmp_path, interpreter)
    assert result["symbols"] == []
    assert "protocol" in result["error"]


def test_symbols_adapter_fails_closed_without_project(tmp_path):
    result = read_symbols(tmp_path, Path("/this/path/does/not/exist"))
    assert result["symbols"] == []
    assert result["error"]

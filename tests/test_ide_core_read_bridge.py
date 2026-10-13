"""M1: isolated official IDE Core read transport, without mutating V4 state."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pynix_gui import ide_core_read_bridge as bridge


def test_read_snapshot_runs_official_core_in_isolated_temp_project(tmp_path, monkeypatch):
    ide = tmp_path / "PYNIX_IDE"
    (ide / "src").mkdir(parents=True)
    for name in ("ide_session.pnx", "project.pnx", "tooling.pnx"):
        (ide / "src" / name).write_text("placeholder", encoding="utf-8")
    target = tmp_path / "target"
    target.mkdir()
    (target / "pynix.toml").write_text("[project]", encoding="utf-8")
    (target / "main.pnx").write_text("function main()\n", encoding="utf-8")
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    observed = {}

    def fake_run(argv, **kw):
        root = Path(kw["cwd"])
        program = (root / "src" / "main.pnx").read_text(encoding="utf-8")
        observed["program"] = program
        assert "ide.workspaceReadSnapshot()" in program
        assert "ide.openSource(" in program
        return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps(
            {"projectOpen": True, "projectPath": str(target), "openSources": []}
        ) + "\n")

    monkeypatch.setattr(bridge.subprocess, "run", fake_run)
    got = bridge.read_core_snapshot(ide, target, python, source="main.pnx")
    assert got["projectOpen"] is True
    assert "main.pnx" in observed["program"]


def test_read_snapshot_refuses_outside_paths(tmp_path):
    ide = tmp_path / "IDE"
    (ide / "src").mkdir(parents=True)
    (ide / "src" / "ide_session.pnx").write_text("", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    (project / "pynix.toml").write_text("", encoding="utf-8")
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    with pytest.raises(bridge.CoreSnapshotError):
        bridge.read_core_snapshot(ide, project, python, source="../escape.pnx")


def test_v4_integrates_core_snapshot_without_replacing_editor():
    root = Path(__file__).resolve().parents[1]
    source = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert 'parser.add_argument("--ide-core"' in source
    assert "PersistentCoreReader(args.ide_core, session.root, compiler_for_core)" in source
    assert "core_reader.start()" in source
    assert "IDE Core: connected (persistent, read-only)" in source
    assert "core_reader.open_source(source)" in source
    assert "core_reader.close()" in source
    assert "session.save(source)" in source
    assert "read_core_snapshot(args.ide_core" not in source

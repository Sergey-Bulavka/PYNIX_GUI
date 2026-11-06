"""Contract tests for the macOS V4 launcher and optional official IDE Core."""
from pathlib import Path
import os
import shutil
import subprocess

import pytest


LAUNCHER = Path(__file__).resolve().parents[1] / "scripts" / "run_ide_workspace.sh"


def _launch(tmp_path, *, with_core=False, extra=(), env=None):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash launcher is only available on Unix-like hosts")
    root = tmp_path / "Zunyite_GUI"
    script = root / "scripts" / "run_ide_workspace.sh"
    script.parent.mkdir(parents=True)
    script.write_text(LAUNCHER.read_text(encoding="utf-8"), encoding="utf-8")
    python = root / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n', encoding="utf-8")
    python.chmod(0o755)
    project = tmp_path / "project"
    project.mkdir()
    core = tmp_path / "Zunyite_IDE"
    if with_core:
        host = core / "src" / "workspace_read_host.uny"
        host.parent.mkdir(parents=True)
        host.write_text("pass\n", encoding="utf-8")
    environment = os.environ.copy()
    environment.pop("ZUNYITE_IDE_CORE", None)
    environment.update(env or {})
    result = subprocess.run([bash, str(script), str(project), *extra],
                            text=True, capture_output=True, env=environment,
                            check=True)
    return result.stdout.splitlines(), project, core


def test_launcher_discovers_official_core_and_passes_project(tmp_path):
    output, project, core = _launch(tmp_path, with_core=True)
    assert "Connecting Zunyite IDE Core:" in output[0]
    assert output[1:] == [
        "-m", "examples.ide_native_v4", "--project", str(project),
        "--ide-core", str(core),
    ]


def test_launcher_does_not_invent_core_when_absent(tmp_path):
    output, project, _ = _launch(tmp_path)
    assert output == ["-m", "examples.ide_native_v4", "--project", str(project)]


def test_launcher_respects_explicit_core_override(tmp_path):
    output, project, _ = _launch(
        tmp_path, with_core=True, extra=("--ide-core", "/custom/IDE"))
    assert output == [
        "-m", "examples.ide_native_v4", "--project", str(project),
        "--ide-core", "/custom/IDE",
    ]


def test_launcher_core_discovery_can_be_disabled(tmp_path):
    output, project, _ = _launch(
        tmp_path, with_core=True, env={"ZUNYITE_IDE_CORE": "off"})
    assert output == ["-m", "examples.ide_native_v4", "--project", str(project)]

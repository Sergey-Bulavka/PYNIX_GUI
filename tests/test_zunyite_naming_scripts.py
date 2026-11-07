"""Canonical naming guard for active macOS IDE acceptance launchers.

Compatibility tests for .pnx and historical materials are intentionally exempt.
"""
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SCRIPTS = (
    "test_editor_block2.sh",
    "test_editor_block3.sh",
    "test_m4_core_recovery.sh",
    "accept_workspace_interactive.sh",
    "run_ide_workspace.sh",
)


@pytest.mark.parametrize("script_name", CANONICAL_SCRIPTS)
def test_active_launcher_uses_canonical_zunyite_names(script_name):
    source = (ROOT / "scripts" / script_name).read_text(encoding="utf-8")
    assert "/Users/morphey/" not in source
    assert "/PYNIX/" not in source and "/PYNIX_IDE" not in source
    assert "pynix.toml" not in source
    assert ".pnx" not in source or script_name == "accept_workspace_interactive.sh"
    if script_name.startswith("test_"):
        assert "zunyite.toml" in source
        assert ".uny" in source
        assert 'ZUNYITE_COMPILER_PYTHON' in source
        assert 'ZUNYITE_IDE_CORE' in source


@pytest.mark.parametrize("script_name", CANONICAL_SCRIPTS)
def test_active_launcher_has_valid_bash_syntax(script_name):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash not installed on this test host")
    result = subprocess.run(
        [bash, "-n", str(ROOT / "scripts" / script_name)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_public_package_name_remains_canonical():
    config = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "zunyite-gui"' in config
    package = (ROOT / "zunyite_gui" / "__init__.py").read_text(encoding="utf-8")
    assert "from pynix_gui import *" in package  # deliberate old-module bridge


def test_active_debugger_workflow_uses_canonical_checkout_path():
    active = ROOT / ".github" / "workflows" / "zunyite-debugger-external.yml"
    assert active.is_file()
    assert not (active.parent / "pynix-debugger-external.yml").exists()
    workflow = active.read_text(encoding="utf-8")
    assert "path: zunyite-compiler" in workflow
    assert "pynix-compiler" not in workflow
    # The secret is a GitHub setting, not an in-repo filename; leave it stable.
    assert "secrets.PYNIX_CI_READ_TOKEN" in workflow

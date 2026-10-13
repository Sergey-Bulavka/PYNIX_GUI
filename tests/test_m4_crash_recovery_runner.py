"""Safety checks for isolated macOS M4 crash recovery exercise."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_crash_recovery_runner_isolated_and_valid_shell():
    runner = ROOT / "scripts" / "test_m4_core_recovery.sh"
    source = runner.read_text(encoding="utf-8")
    assert "mktemp -d" in source
    assert 'mkdir -p "$PROJECT/src"' in source
    assert 'bash scripts/run_ide_workspace.sh "$PROJECT"' in source
    assert "kill -9 <CORE_PID>" in source
    assert "rm -rf" not in source
    assert "pkill " not in source
    assert "killall " not in source
    result = subprocess.run(["bash", "-n", str(runner)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_native_indicator_exposes_only_its_own_core_pid():
    native = (ROOT / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert "core_reader._process.pid" in native
    assert "PID {core_reader._process.pid}" in native

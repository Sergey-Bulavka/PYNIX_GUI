"""Launch-contract and legacy preview retention checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_v4_launcher_targets_active_workspace():
    source = (ROOT / "scripts" / "run_ide_workspace.sh").read_text(encoding="utf-8")
    assert "set -euo pipefail" in source
    assert 'examples.ide_native_v4 --project "$PROJECT" "$@"' in source
    assert "Project directory not found" in source


def test_historical_ide_smokes_are_intentionally_retained():
    for name, test_name in (
        ("examples/ide_shell_showcase.py", "tests/test_ide_shell_showcase.py"),
        ("examples/ide_native_visual_shell.py", "tests/test_ide_native_visual_shell.py"),
        ("examples/adv_01_commands_smoke.py", "tests/test_advanced_commands.py"),
    ):
        assert (ROOT / name).is_file()
        assert (ROOT / test_name).is_file()

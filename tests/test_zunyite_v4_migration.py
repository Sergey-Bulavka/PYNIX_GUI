"""Zunyite Workspace V4 source-convention migration checks."""

from pathlib import Path

from pynix_gui.ide_file_icons import file_icon_type
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession
from pynix_gui.ide_project_runner import ProjectRunner


def test_zunyite_and_legacy_extensions_share_file_icon():
    assert file_icon_type("src/main.uny") == "pynix"
    assert file_icon_type("src/main.pnx") == "pynix"


def test_workspace_generates_uny_source_actions(tmp_path: Path):
    (tmp_path / "main.uny").write_text("function main()\\n    pass\\n", encoding="utf-8")
    page = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "new_file.uny" in page
    assert "New .uny" in page
    assert "main.uny" in page


def test_project_runner_accepts_new_manifest_without_running(tmp_path: Path):
    (tmp_path / "zunyite.toml").write_text('[project]\\nname = "demo"\\n', encoding="utf-8")
    (tmp_path / "main.uny").write_text("function main()\\n    pass\\n", encoding="utf-8")
    compiler_python = tmp_path / "python"
    compiler_python.touch()
    runner = ProjectRunner(tmp_path, compiler_python)
    assert runner.root == tmp_path.resolve()

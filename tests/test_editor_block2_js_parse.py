"""Validate generated workspace JavaScript before macOS visual acceptance."""
from pathlib import Path
import shutil
import subprocess

import pytest

from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession


def test_generated_editor_javascript_parses_with_node_when_available(tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js not installed; macOS WKWebView acceptance still required")
    (tmp_path / "main.pnx").write_text("function main()\n    print(\"hello\")\n", encoding="utf-8")
    html = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert html.startswith("<script>")
    assert html.endswith("</script>")
    program = html.removeprefix("<script>").removesuffix("</script>")
    result = subprocess.run(
        [node, "--check"], input=program, text=True, capture_output=True, timeout=20
    )
    assert result.returncode == 0, result.stderr

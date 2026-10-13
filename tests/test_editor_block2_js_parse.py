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


def test_bracket_matching_and_indentation_folding_behavior_with_node(tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js not installed; behavior is checked in macOS acceptance")
    (tmp_path / "main.pnx").write_text("function main()\n    print(1)\n", encoding="utf-8")
    html = workspace_bootstrap(WorkspaceSession(tmp_path))
    matching = html.split(" function matchingBracketPositions(value,caret){", 1)[1].split(
        " function recolorSource(){", 1)[0]
    folding = html.split(" function foldableLines(text){", 1)[1].split(
        " function renderCode(file)", 1)[0]
    program = (
        "function matchingBracketPositions(value,caret){" + matching
        + "function foldableLines(text){" + folding
        + """
const structural = 'function a(){ print("}") }';
const open = structural.indexOf('{');
const close = structural.lastIndexOf('}');
if (!matchingBracketPositions(structural,open).has(close)) process.exit(11);
if (!matchingBracketPositions('(){',2).has(2)) process.exit(14);
if (!matchingBracketPositions('()',2).has(0)) process.exit(15);
const comment = '// { ignored';
if (matchingBracketPositions(comment,comment.indexOf('{')).size) process.exit(12);
const lines = 'function main()\\n    print(1)\\n    return 1\\nprint(2)';
if (foldableLines(lines).get(0)!==2) process.exit(13);
"""
    )
    result = subprocess.run([node, "-"], input=program, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr or f"Node exit {result.returncode}"

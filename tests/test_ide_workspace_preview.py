from pathlib import Path

from pynix_gui.ide_workspace_preview import attach_workspace, workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession


def test_real_source_embeds_only_project_files(tmp_path):
    (tmp_path / "main.pnx").write_text('print("<script>alert(1)</script>")', encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "gui.pnx").write_text("function gui()", encoding="utf-8")
    session = WorkspaceSession(tmp_path)
    js = workspace_bootstrap(session)
    assert "main.pnx" in js
    assert "sub/gui.pnx" in js
    assert "<script>alert(1)</script>" not in js
    assert "\\u003cscript" in js
    assert session.documents == {}
    assert session.active is None


def test_attach_workspace_replaces_only_body_end(tmp_path):
    (tmp_path / "a.pnx").write_text("hello", encoding="utf-8")
    html = "<html><body class=\"workspace-mode\">old</body></html>"
    output = attach_workspace(html, WorkspaceSession(tmp_path))
    assert output.startswith("<html><body")
    assert "a.pnx" in output
    assert output.endswith("</body></html>")


def test_binary_and_oversized_documents_skipped(tmp_path):
    (tmp_path / "binary.pnx").write_bytes(b"\\xff")
    (tmp_path / "huge.pnx").write_text("x" * 1001)
    (tmp_path / "fine.pnx").write_text("working")
    result = workspace_bootstrap(WorkspaceSession(tmp_path), max_bytes=1000)
    assert "fine.pnx" in result
    assert "huge.pnx" not in result
    assert "binary.pnx" not in result


def test_native_v4_supports_explicit_project_argument():
    source = (Path(__file__).resolve().parents[1] / "examples" /
              "ide_native_v4.py").read_text(encoding="utf-8")
    assert '"--project"' in source
    assert "attach_workspace" in source

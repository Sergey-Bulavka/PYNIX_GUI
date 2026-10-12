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
    (tmp_path / "binary.pnx").write_bytes(bytes([0xff]))
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


def test_v43_nested_tree_and_selection_binding(tmp_path):
    (tmp_path / "src" / "ui").mkdir(parents=True)
    (tmp_path / "src" / "main.pnx").write_text("main()", encoding="utf-8")
    (tmp_path / "src" / "ui" / "view.pnx").write_text("view()", encoding="utf-8")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "function buildTree()" in js
    assert "function visit(node,depth)" in js
    assert "expanded.add(segments.slice(0,i).join('/'))" in js
    assert "entry.path===current" in js
    assert "src/ui/view.pnx" in js
    assert "folder-open" in js
    assert "file-code" in js
    assert "project-glyph" in js


def test_v43_uses_original_vector_assets_and_restores_explorer(tmp_path):
    (tmp_path / "main.pnx").write_text("hello", encoding="utf-8")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "xmlns='http://www.w3.org/2000/svg'" in js
    assert "explorerControl?.addEventListener('click'" in js
    assert "function renderTree()" in js


def test_v43_header_escapes_project_title(tmp_path):
    project = tmp_path / "Example & Project"
    project.mkdir()
    (project / "main.pnx").write_text("ok", encoding="utf-8")
    output = attach_workspace(
        "<body><b>PYNIX</b> / Icon System</body>",
        WorkspaceSession(project))
    assert "Example &amp; Project" in output
    assert "PROJECT_NAME_PAYLOAD" not in output


def test_v43_root_and_nested_folders_share_disclosure_renderer(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.pnx").write_text("hello", encoding="utf-8")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "function appendRow(entry, depth, isRoot=false)" in js
    assert "appendRow({name:PROJECT_NAME,path:'',folder:true},0,true)" in js
    assert "appendRow(entry,depth)" in js
    assert "project-chevron" in js
    assert "chevron.classList.add('collapsed')" in js
    assert "chevron.textContent=" not in js


def test_v43_disclosure_and_glyph_slots_have_fixed_geometry():
    preview = (Path(__file__).resolve().parents[1] / "examples" /
               "icon_direction_preview.html").read_text(encoding="utf-8")
    assert ".workspace-mode .project-entry{height:32px;display:flex;align-items:center;" in preview
    assert ".workspace-mode .project-chevron{width:16px;min-width:16px;height:16px;" in preview
    assert ".workspace-mode .project-glyph{width:20px;height:20px;" in preview
    assert ".workspace-mode .project-chevron.collapsed svg{transform:rotate(-90deg)}" in preview

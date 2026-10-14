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
    assert '"name": "huge.pnx"' in result
    assert '"unloaded": true' in result
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
    assert "entry.path===(selectedPath??current)" in js
    assert "line.classList.add('workspace-selected')" in js
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


def test_v4_generated_project_javascript_parses_with_node_if_available(tmp_path):
    import re
    import shutil
    import subprocess
    import pytest
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable; JS syntax validation requires a JavaScript engine")
    (tmp_path / "main.pnx").write_text("print('test')", encoding="utf-8")
    source = workspace_bootstrap(WorkspaceSession(tmp_path))
    match = re.fullmatch(r"<script>\s*(.*?)\s*</script>", source, re.S)
    assert match is not None
    proc = subprocess.run([node, "--check", "-"], input=match.group(1), encoding="utf-8",
                          text=True, capture_output=True, timeout=10)
    assert proc.returncode == 0, proc.stderr


def test_explorer_includes_empty_and_unscanned_directory_nodes(tmp_path):
    (tmp_path / "empty").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.pnx").write_text("function main()")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib").mkdir()
    result = workspace_bootstrap(WorkspaceSession(tmp_path), max_files=1)
    assert '"empty"' in result
    assert '".venv"' in result
    assert '"src"' in result
    assert '"FOLDER_PAYLOAD"' not in result
    assert "const folders = " in result


def test_explorer_file_metadata_survives_preview_content_limit(tmp_path):
    (tmp_path / "one.pnx").write_text("first")
    (tmp_path / "two.pnx").write_text("second")
    result = workspace_bootstrap(WorkspaceSession(tmp_path), max_files=1)
    assert '"one.pnx"' in result
    assert '"two.pnx"' in result
    assert '"unloaded": true' in result


def test_single_pointer_press_and_lazy_file_open_bridge(tmp_path):
    (tmp_path / "first.pnx").write_text("first")
    (tmp_path / "second.pnx").write_text("second")
    bootstrap = workspace_bootstrap(WorkspaceSession(tmp_path), max_files=1)
    assert "line.addEventListener('dblclick'" in bootstrap
    assert "if(e.button!==0)return" in bootstrap
    assert "window.webkit?.messageHandlers?.pynixFileOpen" in bootstrap
    assert "window.pynixReceiveFile=function(payload)" in bootstrap
    assert '"unloaded": true' in bootstrap


def test_mac_host_has_bounded_lazy_source_reader():
    src = (Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert 'class FileOpenHandler(NSObject)' in src
    assert 'source not in available_sources' in src
    assert 'session.resolve_file(source)' in src
    assert 'pynixFileOpen' in src
    assert 'window.pynixReceiveFile(' in src


def test_single_click_selects_and_double_click_opens_file(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "let selectedPath = null" in js
    assert "selectedPath=entry.path;\n         renderTree();" in js
    assert "line.addEventListener('dblclick'" in js
    assert "selectedPath=entry.path;\n         show(entry.path);" in js
    assert "if(!entry.folder&&entry.path===(selectedPath??current))line.classList.add('workspace-selected');" in js
    assert "line.addEventListener('pointerdown'" not in js
    assert "if(entry.folder){" in js


def test_native_editor_has_caret_save_and_dirty_tracking(tmp_path):
    (tmp_path / "main.pnx").write_text("main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "pynix-source-input" in js
    assert "editorInput.addEventListener('input'" in js
    assert "file.dirty=file.text!==file.savedText" in js
    assert "window.webkit?.messageHandlers?.pynixFileSave" in js
    assert "window.pynixSaveResult=payload" in js
    assert "e.metaKey||e.ctrlKey" in js


def test_native_save_host_uses_session_guard(tmp_path):
    source = (Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py").read_text()
    assert "class FileSaveHandler(NSObject)" in source
    assert "session.update(source, content)" in source
    assert "session.save(source)" in source
    assert 'pynixFileSave' in source


def test_editor_tabs_can_close_and_reload_sources(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "function renderTabs()" in js
    assert "close.setAttribute('aria-label','Close '+fileName)" in js
    assert "Save changes to " in js
    assert "button('Don’t Save'" in js
    assert "button('Cancel'" in js
    assert "button('Save'" in js
    assert "file.unloaded=true" in js
    assert "line.addEventListener('dblclick'" in js


def test_editor_has_live_syntax_overlay(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "function recolorSource()" in js
    assert "pynix-edit-highlight" in js
    assert "recolorSource();" in js
    assert "caret" not in js or "editorInput" in js


def test_workspace_opens_in_edit_mode_with_compact_tree(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "let editing=true;" in js
    assert "   editing=true;\n   if(file.unloaded)" in js
    assert "7+Math.min(depth,12)*13" in js
    assert "close.innerHTML=" in js


def test_editable_gutter_and_cursor_are_kept_per_file(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()\n    return 1\n")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "pynix-edit-gutter" in js
    assert "cursorStatus.textContent='Ln '" in js
    assert "file.cursorStart=editorInput.selectionStart" in js
    assert "file.scrollTop=editorInput.scrollTop" in js
    assert "editorInput.setSelectionRange(" in js
    assert "gutter.scrollTop=editorInput.scrollTop" in js


def test_v418_editor_lexer_comments_and_strings_are_atomic(tmp_path):
    (tmp_path / "main.pnx").write_text('// 123 comment\\nfunction main()')
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "t.startsWith('//')||t.startsWith('#')" in js
    assert "kind='comment'" in js
    assert "kind='string'" in js
    assert "kind='type'" in js
    assert "kind='constant'" in js
    assert "last=token.lastIndex" in js


def test_v418_indent_and_selected_line_shortcuts(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "function indentSelectedLines(outdent)" in js
    assert "if(e.key==='Tab')" in js
    assert "e.shiftKey" in js
    assert "e.key==='Enter'" in js
    assert "setRangeText(" in js
    assert "pynix-active-line" in js


def test_v418_refresh_diagnostics_only_after_save(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "Diagnostics require save" in js
    assert "payload.diagnostics||[]" in js
    native=(Path(__file__).resolve().parents[1]/"examples"/"ide_native_v4.py").read_text()
    assert "snapshot = read_diagnostics(session.root, compiler_python)" in native


def test_active_line_uses_computed_font_metrics(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "const metrics=getComputedStyle(editorInput)" in js
    assert "parseFloat(metrics.lineHeight)" in js
    assert "parseFloat(metrics.paddingTop)" in js
    assert "(line-1)*lineHeight-editorInput.scrollTop" in js
    assert "21.45" not in js


def test_edit_lexer_distinguishes_comments_and_calls(tmp_path):
    (tmp_path / "main.pnx").write_text("// number 123\\nfunction main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "t.startsWith('//')||t.startsWith('#')" in js
    assert "kind='call'" in js
    assert "kind='builtin'" in js


def test_v420_per_file_undo_redo_and_automatic_indents(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "function pushUndo(file)" in js
    assert "function restoreHistory(direction)" in js
    assert "undoLimit=200" in js
    assert "file.redoStack=[]" in js
    assert "editorInput.addEventListener('beforeinput'" in js
    assert "restoreHistory(e.shiftKey?'redo':'undo')" in js
    assert "pushUndo(byName.get(current))" in js


def test_fixed_height_custom_caret_is_independent_of_native_webkit_caret(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "pynix-custom-caret" in js
    assert "editorInput.wrap='off'" in js
    assert "customCaret.style.transform=" in js
    assert "document.activeElement!==editorInput" in js
    assert "measure.style.fontFamily=metrics.fontFamily" in js
    assert "measure.style.fontSize=metrics.fontSize" in js


def test_v423_find_in_editor_shortcuts_and_navigation(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "pynix-find-bar" in js
    assert "function findMatches()" in js
    assert "function navigateFind(step=1,reset=false)" in js
    assert "function openFind()" in js
    assert "function closeFind()" in js
    assert "findInput.addEventListener('keydown'" in js
    assert "e.shiftKey?-1:1" in js
    assert "findIndex=-1" in js


def test_find_navigation_does_not_steal_search_focus(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    part = js.split("function navigateFind(step=1,reset=false)", 1)[1].split("function openFind()", 1)[0]
    assert "editorInput.focus()" not in part
    assert "editorInput.setSelectionRange(at,at+findInput.value.length)" in part
    assert "findInput.focus()" in js
    assert "findInput.addEventListener('keydown'" in js


def test_find_matches_are_decorated_in_source_highlight_without_focus_change(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "function decorateFindMatches()" in js
    assert "document.createTreeWalker(coloredSource,NodeFilter.SHOW_TEXT)" in js
    assert "pynix-find-current" in js
    assert "pynix-find-match" in js
    assert "recolorSource();" in js.split("function navigateFind(step=1,reset=false)", 1)[1].split("function openFind()", 1)[0]
    assert "editorInput.focus()" not in js.split("function navigateFind(step=1,reset=false)", 1)[1].split("function openFind()", 1)[0]


def test_v425_replace_and_go_to_line_controls(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "function openReplace()" in js
    assert "function replaceCurrent()" in js
    assert "function replaceEvery()" in js
    assert "pushUndo(byName.get(current))" in js
    assert "function goToLine(line)" in js
    assert "goInput.addEventListener('keydown'" in js


def test_v425_project_search_navigates_after_lazy_open(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "pynixProjectSearch" in js
    assert "window.pynixProjectSearchResult=payload=>" in js
    assert "let pendingNavigation=null" in js
    assert "selectNavigationLocation(pendingNavigation)" in js
    assert "document.dispatchEvent(new CustomEvent('pynix:navigate'" in js


def test_v425_project_results_are_positioned_below_search_and_escape_closes(tmp_path):
    (tmp_path / "main.pnx").write_text("function main()")
    js = workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "document.body.appendChild(projectResults)" in js
    assert "function positionProjectResults()" in js
    assert "projectFindBar.getBoundingClientRect()" in js
    assert "rect.bottom+7" in js
    assert "function closeProjectFind()" in js
    assert "e.stopImmediatePropagation();closeProjectFind()" in js
    assert "if(projectFindBar.hidden)return;" in js

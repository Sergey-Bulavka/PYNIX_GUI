"""Working PyCharm Project tree header (not the old visual shell)."""

from pathlib import Path

from pynix_gui.ide_pycharm_chrome import (
    CHROME_SCRIPT, CHROME_STYLE, apply_pycharm_chrome,
)
from pynix_gui.ide_iconless_mode import ICONLESS_STYLE
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession


def test_root_shows_actual_local_project_path_with_safe_js_quoting(tmp_path):
    root=tmp_path / "PYNIX"
    root.mkdir()
    (root / "main.pnx").write_text("function main()\n",encoding="utf-8")
    js=workspace_bootstrap(WorkspaceSession(root))
    assert "const PROJECT_PATH = " in js
    assert str(root) in js
    assert "path.textContent=PROJECT_PATH;" in js
    assert "path.title=PROJECT_PATH;" in js
    assert "label.classList.add('pynix-project-root-name');" in js
    for expected in ("min-width:0!important", "text-overflow:ellipsis!important",
                     ".pynix-project-root-path", ".pynix-project-root-name"):
        assert expected in CHROME_STYLE
    assert "innerHTML=PROJECT_PATH" not in js


def test_every_toolbar_action_has_correct_order_and_a_real_target():
    script=CHROME_SCRIPT
    for mark in (
        "viewLabel.textContent='Project'",
        "menu('pynix-project-create-menu','New File or Directory…'",
        "divider.className='pynix-project-header-separator'",
        "quick('Select Opened File','general/locate'",
        "quick('Expand Selected','general/expandAll'",
        "makeIcon('general/collapseAll')",
        "menu('pynix-project-more-menu','Options','general/moreVertical'",
        "quick('Hide','general/hide'",
        "actions.replaceChildren(create,divider,locate,expand,collapseAction,more,hide);",
    ):
        assert mark in script,mark
    for handler in (
        "window.pynixCreateProjectEntry?.('file')",
        "window.pynixCreateProjectEntry?.('directory')",
        "window.pynixProjectSelectOpenedFile?.()",
        "window.pynixProjectExpandSelected?.()",
        "window.pynixProjectCollapseAll?.()",
        "document.querySelectorAll('.workspace-mode .rail>.rail-item')[0]?.click();",
    ):
        assert handler in script,handler
    for option in ("['New File…'", "['New Directory…'",
                   "['Expand All'", "['Collapse All'"):
        assert option in script


def test_hover_reveals_toolbar_on_whole_tree_and_keyboard_focus():
    for rule in (
        ".workspace-mode .tree:hover .pynix-project-header-actions",
        ".workspace-mode .tree:focus-within .pynix-project-header-actions",
        ".workspace-mode .tree .pynix-project-header-actions:has(details[open])",
        "opacity:0!important;pointer-events:none!important;",
        "opacity:1!important;pointer-events:auto!important;",
        ".pynix-project-quick-button:hover",
        ".pynix-project-quick-button:focus-visible",
        "background:#3a3d45!important;",
        ".pynix-project-header-separator",
        ".pynix-project-popup",
    ):
        assert rule in CHROME_STYLE,rule
    assert "new MutationObserver(initProjectHeader).observe(tree,{childList:true})" in CHROME_SCRIPT
    assert "if(!head||head.dataset.pynixPyCharmHeader)return;" in CHROME_SCRIPT
    assert "if(details.open&&!details.contains(event.target))details.open=false;" in CHROME_SCRIPT


def test_project_toolbar_glyphs_work_in_default_and_full_icon_modes():
    html='<html><body class="workspace-mode"></body></html>'
    for iconless in (False,True):
        page=apply_pycharm_chrome(html,iconless=iconless)
        for key in ("general/add", "general/locate", "general/expandAll",
                    "general/collapseAll", "general/moreVertical", "general/hide",
                    "general/chevronDown"):
            assert f'"{key}"' in page
    assert ".pynix-project-header .pynix-project-quick-button>svg" in ICONLESS_STYLE
    assert ".pynix-project-header .pynix-project-header-button>svg" in ICONLESS_STYLE


def test_native_creates_file_and_directory_through_safe_workspace_api(tmp_path):
    root=tmp_path / "PYNIX"
    root.mkdir()
    session=WorkspaceSession(root)
    session.create_directory("src")
    assert (root / "src").is_dir()
    document=session.create_file("src/new_file.pnx")
    assert document.text == ""
    assert (root / "src" / "new_file.pnx").is_file()
    native=(Path(__file__).resolve().parents[1] /
            "examples/ide_native_v4.py").read_text(encoding="utf-8")
    assert 'kind = request.get("kind", "file")' in native
    assert 'session.create_directory(relative)' in native
    assert 'doc = session.create_file(relative)' in native
    assert 'response = {"ok": True, "kind": "directory", "source": relative}' in native
    assert 'response["icon"]' not in native
    assert '"icon": file_icon_type(relative)' in native
    assert 'controller.addScriptMessageHandler_name_(project_create_handler, "pynixProjectCreate")' in native
    js=workspace_bootstrap(session)
    assert "window.pynixProjectCreateResult=result=>{" in js
    assert "if(result.kind==='directory'){" in js
    assert "root=buildTree();" in js
    assert "window.pynixCreateProjectEntry=kind=>{" in js
    assert "window.pynixProjectSelectOpenedFile=()=>{" in js
    assert "window.pynixProjectExpandSelected=(all=false)=>{" in js
    assert "window.pynixProjectCollapseAll=()=>{" in js
    assert "if(entry.folder&&selectedPath===entry.path)" in js


def test_tooltips_are_delegated_and_shortcuts_preserved():
    from pynix_gui.ide_tooltips import TOOLTIP_SCRIPT
    assert "locate.dataset.pynixShortcut='⌥F1, 1'" in CHROME_SCRIPT
    assert "expand.dataset.pynixTooltip='Expand Selected\\nPress ⇧⌘+ to expand all nodes'" in CHROME_SCRIPT
    assert "hide.dataset.pynixShortcut='⇧⎋'" in CHROME_SCRIPT
    assert "'.pynix-project-quick-button'" in TOOLTIP_SCRIPT
    assert "'.pynix-project-header-button'" in TOOLTIP_SCRIPT
    assert "event.key==='+'||event.key==='='" in CHROME_SCRIPT
    assert "event.key==='-'" in CHROME_SCRIPT

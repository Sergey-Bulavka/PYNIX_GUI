"""PyCharm screenshot chrome: retain real PYNIX actions and native layout."""
from pathlib import Path

from pynix_gui.ide_pycharm_chrome import (
    CHROME_STYLE, CHROME_SCRIPT, apply_pycharm_chrome,
)
from pynix_gui.ide_icon_parity import BUNDLED_ICONS
from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog


def test_chrome_uses_licensed_original_glyphs_and_escapes_svg():
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for name in ("general/search", "general/settings", "general/add",
                 "general/locate", "general/expandAll", "general/collapseAll",
                 "general/moreVertical", "general/hide",
                 "general/chevronDown", "toolwindows/vcs"):
        assert catalog.resolve(name, dark=True) is not None, name
        assert catalog.resolve(name, dark=False) is not None, name
    markup = "<html><body class='workspace-mode'></body></html>"
    rendered = apply_pycharm_chrome(markup)
    assert rendered != markup
    assert apply_pycharm_chrome(rendered) == rendered
    assert 'id="pynix-pycharm-chrome"' in rendered
    assert "__CHROME_ICONS__" not in rendered
    assert "<svg" not in rendered


def test_native_chrome_installed_last_after_workspace_and_jetbrains_icons():
    source = (Path(__file__).resolve().parents[1] / "examples" /
              "ide_native_v4.py").read_text(encoding="utf-8")
    assert "from pynix_gui.ide_pycharm_chrome import apply_pycharm_chrome" in source
    assert "document = apply_pycharm_chrome(document)" in source
    assert source.index("document = apply_new_ui_icons(document)") < source.index(
        "document = apply_edge_profile(document)"
    ) < source.index("document = apply_pycharm_chrome(document)")


def test_top_toolbar_moves_existing_run_debug_and_tools_controls():
    for name in (".pynix-run-mode", ".pynix-run-action",
                 ".pynix-debug-primary", ".pynix-stop-action",
                 ".pynix-tools-menu"):
        assert name in CHROME_SCRIPT
    assert "center.appendChild(el)" in CHROME_SCRIPT
    assert "items.prepend(save);" in CHROME_SCRIPT
    assert "document.querySelectorAll('.workspace-mode .rail>.rail-item')[1]?.click();" in CHROME_SCRIPT
    assert "document.querySelectorAll('.workspace-mode .rail>.rail-item')[5]?.click();" in CHROME_SCRIPT
    assert ".workspace-mode .workspace-toolbar .pynix-pycharm-center" in CHROME_STYLE
    assert ".workspace-mode .workspace-toolbar .pynix-pycharm-right" in CHROME_STYLE
    assert "@media(max-width:930px)" in CHROME_STYLE


def test_project_title_actions_bind_to_real_tree_and_new_file_handlers():
    for expected in (
        "title.textContent='Project'",
        "document.querySelector('.pynix-new-source')?.click()",
        ".project-entry.workspace-selected",
        "collapse?.click();more.open=false;",
        "document.querySelectorAll('.workspace-mode .rail>.rail-item')[0]?.click();",
        "new MutationObserver(initProjectHeader).observe(tree,{childList:true})",
    ):
        assert expected in CHROME_SCRIPT
    assert ".pynix-project-quick-button:focus-visible" in CHROME_STYLE
    assert "makeIcon('general/collapseAll')" in CHROME_SCRIPT
    assert "makeIcon('general/moreVertical')" in CHROME_SCRIPT


def test_status_breadcrumb_follows_current_editor_tab():
    assert "const updateBreadcrumb=()=>{" in CHROME_SCRIPT
    assert ".editor-tabs .pynix-editor-tab.active" in CHROME_SCRIPT
    assert "label.textContent=name" in CHROME_SCRIPT
    assert "new MutationObserver(()=>{" in CHROME_SCRIPT
    assert "updateBreadcrumb();" in CHROME_SCRIPT
    assert "updateRunActionTooltips();" in CHROME_SCRIPT
    assert "}).observe(tabs,{" in CHROME_SCRIPT
    assert ".workspace-mode .bottom .pynix-status-breadcrumb" in CHROME_STYLE


def test_native_toolbar_drag_overlay_excludes_centered_working_controls():
    from examples.ide_native_v4 import TOOLBAR_DRAG_SCRIPT
    assert "'.pynix-pycharm-center','.pynix-pycharm-right'" in TOOLBAR_DRAG_SCRIPT
    assert "control.getBoundingClientRect()" in TOOLBAR_DRAG_SCRIPT
    assert "area.width = Math.max(0, occupied.left - area.x - 8);" in TOOLBAR_DRAG_SCRIPT
    assert "width:Math.max(0,region.width-24)" in TOOLBAR_DRAG_SCRIPT


def test_project_logo_name_chevron_form_one_button_and_not_three_elements():
    from pynix_gui.ide_pycharm_chrome import CHROME_SCRIPT, CHROME_STYLE
    assert "const initIdentity=()=>{" in CHROME_SCRIPT
    assert "project=build('pynix-toolbar-project'" in CHROME_SCRIPT
    assert "brand.className='pynix-toolbar-project-badge';" in CHROME_SCRIPT
    assert "brand.textContent='PY';" in CHROME_SCRIPT
    assert "projectText.className='pynix-toolbar-project-name';" in CHROME_SCRIPT
    assert "projectText.textContent=projectLabel;" in CHROME_SCRIPT
    assert "project.append(brand,projectText);" in CHROME_SCRIPT
    assert "project.appendChild(projectArrow);" in CHROME_SCRIPT
    assert "legacyProject?.remove();" in CHROME_SCRIPT
    assert "title?.remove();" in CHROME_SCRIPT
    assert "initToolbar();initIdentity();initProjectHeader();" in CHROME_SCRIPT
    assert ".pynix-toolbar-project:hover" in CHROME_STYLE
    assert "gap:7px!important;padding-left:5px!important;padding-right:8px!important" in CHROME_STYLE


def test_git_branch_uses_live_snapshot_not_project_caption_or_hardcoded_main():
    from pynix_gui.ide_pycharm_chrome import CHROME_SCRIPT, CHROME_STYLE
    from pynix_gui.ide_workspace_preview import attach_git_snapshot
    from pynix_gui.ide_git_snapshot import GitSnapshot
    assert "const snapshot=window.pynixGitSnapshot;" in CHROME_SCRIPT
    assert "snapshot?.available&&snapshot.branch?" in CHROME_SCRIPT
    assert "branchTitle=branchName?'Git Branch: '+branchName:" in CHROME_SCRIPT
    assert "branchIcon=makeIcon('toolwindows/vcs');" in CHROME_SCRIPT
    assert "branchArrow=makeIcon('general/chevronDown');" in CHROME_SCRIPT
    assert "branch.appendChild(branchArrow);" in CHROME_SCRIPT
    assert "document.querySelectorAll('.workspace-mode .rail>.rail-item')[2]?.click();" in CHROME_SCRIPT
    assert "branch.textContent='main'" not in CHROME_SCRIPT
    assert "branchName='main'" not in CHROME_SCRIPT
    source = "<html><body class='workspace-mode'></body></html>"
    rendered = attach_git_snapshot(source, GitSnapshot("feature/live-branch",(),()))
    assert "window.pynixGitSnapshot" in rendered
    assert '"feature/live-branch"' in rendered
    assert "available:!!data.available" in rendered
    assert ".workspace-toolbar .pynix-toolbar-branch-icon" in CHROME_STYLE


def test_iconless_native_identity_keeps_only_real_git_and_chevron_icons():
    from pynix_gui.ide_pycharm_chrome import apply_pycharm_chrome
    source = "<html><body class='workspace-mode'></body></html>"
    rendered = apply_pycharm_chrome(source, iconless=True)
    assert '"general/chevronDown"' in rendered
    assert '"toolwindows/vcs"' in rendered
    assert '"general/search"' not in rendered
    assert 'const iconless=true;' in rendered
    assert 'classList.add(\'pynix-toolbar-branch-chevron\');' in rendered
    assert 'classList.add(\'pynix-toolbar-branch-icon\');' in rendered


def test_current_file_selector_is_one_button_with_real_mode_options():
    # The original select still drives PYNIX project's runner, while its
    # compact presentation is one accessible PyCharm-style button.
    for value in (
        "const createRunConfig=(center,select)=>{",
        "button.className='pynix-current-config';",
        "name.className='pynix-current-config-label';",
        "const arrow=makeIcon('general/chevronDown');",
        "popup.className='pynix-config-options';popup.hidden=true;",
        "['run','Current File']",
        "['check','Check Project']",
        "select.value=value;",
        "select.dispatchEvent(new Event('change',{bubbles:true}));",
        "button.setAttribute('aria-expanded',String(!popup.hidden));",
        "button.setAttribute('aria-haspopup','menu');",
        "const options=[...popup.querySelectorAll('button')];",
        "if(event.key==='Escape'&&!popup.hidden){close();button.focus();}",
        "center.insertBefore(button,select);",
        "createRunConfig(center,select);",
    ):
        assert value in CHROME_SCRIPT, value
    for rule in (
        ".pynix-pycharm-center>.pynix-run-mode{",
        "display:none!important",
        ".pynix-current-config:hover",
        ".pynix-current-config[aria-expanded=\"true\"]",
        ".pynix-config-options[hidden]{display:none!important}",
        "text-overflow:ellipsis!important",
    ):
        assert rule in CHROME_STYLE, rule


def test_run_and_debug_keep_original_clicks_and_follow_active_tab_tooltips():
    for value in (
        "for(const el of [select,run,debug,stop,tools])if(el)center.appendChild(el);",
        "for(const [button,key] of [[run,'run/run'],[debug,'run/debug']]){",
        "button.replaceChildren(icon);",
        "const updateRunActionTooltips=()=>{",
        ".editor-tabs .pynix-editor-tab.active",
        "querySelector('.pynix-editor-tab-label')",
        "const text=name?verb+\" '\"+name+\"'\"",
        "const actions=[[run,'Run','⌃R'],[debug,'Debug','⌃D']];",
        "control.dataset.pynixTooltip=text;",
        "control.dataset.pynixShortcut=shortcut;",
        "updateRunActionTooltips();",
        "new MutationObserver(()=>{",
        "updateBreadcrumb();",
    ):
        assert value in CHROME_SCRIPT, value
    catalog=JetBrainsIconCatalog(BUNDLED_ICONS)
    for key in ("run/run","run/debug"):
        assert catalog.svg(key,dark=True,tool_window=False) is not None
    for rule in (
        ".pynix-pycharm-center>.pynix-run-action svg",
        ".pynix-pycharm-center>.pynix-debug-primary svg",
    ):
        assert rule in CHROME_STYLE


def test_more_actions_is_native_icon_menu_and_preserves_existing_buttons():
    for value in (
        "const tools=toolbar.querySelector('.pynix-tools-menu');",
        "summary.replaceChildren(makeIcon('general/moreVertical')",
        "summary.title='More Actions';",
        "summary.dataset.pynixTooltip='More Actions';",
        "summary.setAttribute('aria-label','More Actions');",
        "const items=tools.querySelector('.pynix-tools-menu-items');",
        "if(items&&save)items.prepend(save);",
        "params.className='pynix-run-with-params';",
        "params.textContent='Run with Parameters...';",
        "const edit=makeIcon('general/edit');",
        "params.setAttribute('aria-disabled','true');",
        "params.dataset.pynixTooltip='Run with Parameters (not yet supported by PYNIX)';",
        "items.prepend(params);",
        "if(items&&debugStatus)items.appendChild(debugStatus);",
    ):
        assert value in CHROME_SCRIPT, value
    # Backend cannot currently pass arbitrary command-line arguments.
    assert "params.addEventListener('click'" not in CHROME_SCRIPT
    assert "params.disabled=true" not in CHROME_SCRIPT
    assert "Run with Parameters..." in CHROME_SCRIPT
    assert ".pynix-run-with-params:hover" in CHROME_STYLE
    assert ".pynix-tools-menu[open]>summary" in CHROME_STYLE


def test_iconless_chrome_still_loads_original_toolbar_icon_assets():
    document=apply_pycharm_chrome(
        '<html><body class="workspace-mode"></body></html>',iconless=True
    )
    for key in ("general/chevronDown","toolwindows/vcs",
                "general/moreVertical","general/edit","run/run","run/debug"):
        assert '"'+key+'"' in document
    assert "<svg" not in document
    assert "__CHROME_ICONS__" not in document

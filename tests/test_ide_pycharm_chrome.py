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
                 "general/locate", "general/expandAll", "general/hide"):
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
        "title.textContent='Proj'",
        "document.querySelector('.pynix-new-source')?.click()",
        ".project-entry.workspace-selected",
        "collapse?.click();more.open=false;",
        "document.querySelectorAll('.workspace-mode .rail>.rail-item')[0]?.click();",
        "new MutationObserver(initProjectHeader).observe(tree,{childList:true})",
    ):
        assert expected in CHROME_SCRIPT
    assert ".pynix-project-quick-button:focus-visible" in CHROME_STYLE


def test_status_breadcrumb_follows_current_editor_tab():
    assert "const updateBreadcrumb=()=>{" in CHROME_SCRIPT
    assert ".editor-tabs .pynix-editor-tab.active" in CHROME_SCRIPT
    assert "label.textContent=name" in CHROME_SCRIPT
    assert "new MutationObserver(updateBreadcrumb).observe(tabs" in CHROME_SCRIPT
    assert ".workspace-mode .bottom .pynix-status-breadcrumb" in CHROME_STYLE

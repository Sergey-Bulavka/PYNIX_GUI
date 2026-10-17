"""PyCharm-style icon tooltips work in native WKWebView without OS title popups."""
from pathlib import Path

from pynix_gui.ide_tooltips import (
    TOOLTIP_SCRIPT, TOOLTIP_SHORTCUTS, TOOLTIP_STYLE,
    apply_native_tooltips,
)
from pynix_gui.ide_edge_profile import EDGE_PROFILE_SCRIPT, EDGE_PROFILE_STYLE


def test_all_reference_shortcut_labels_are_explicit_and_order_independent():
    assert TOOLTIP_SHORTCUTS == {
        "Project": "⌘1",
        "Commit": "⌘0",
        "Structure": "⌘7",
        "Bookmarks": "⌘2",
        "Find": "⌘3",
        "Run": "⌘4",
        "Debug": "⌘5",
        "Services": "⌘8",
        "Terminal": "⌥F12",
        "Problems": "⌘6",
        "Git": "⌘9",
        "AI Chat": "⌥⇧1",
    }
    assert "PYNIX Terminal" not in TOOLTIP_SHORTCUTS
    assert "Notifications" not in TOOLTIP_SHORTCUTS


def test_one_tooltip_overlay_is_injected_with_no_original_workspace_changes():
    workspace = "<html><body class='workspace-mode'><button>Run</button></body></html>"
    final = apply_native_tooltips(workspace)
    assert final.count('id="pynix-native-tooltips-style"') == 1
    assert final.count('id="pynix-native-tooltips-script"') == 1
    assert 'const shortcuts={"Project":' in final
    assert r"\u23181" in final and r"\u2325F12" in final
    assert "<button>Run</button>" in final
    assert apply_native_tooltips(final) == final
    assert apply_native_tooltips("not an HTML document") == "not an HTML document"


def test_tooltips_cover_all_perimeter_and_project_buttons_via_delegation():
    for selector in (
        ".pynix-extra-tool",
        ".pynix-tool-profile-more",
        ".pynix-project-quick-button",
        ".pynix-project-header-button",
        ".pynix-project-more-menu>summary",
        ".pynix-toolbar-project",
        ".pynix-toolbar-branch",
        ".pynix-pycharm-icon-button",
        ".pynix-pycharm-center>.pynix-run-action",
        ".pynix-pycharm-center>.pynix-debug-primary",
        ".pynix-pycharm-center>.pynix-tools-menu>summary",
        ".pynix-tool-window-toggle",
        ".pynix-tool-window-restore",
    ):
        assert "'"+selector+"'" in TOOLTIP_SCRIPT

    assert "document.addEventListener('pointerover'" in TOOLTIP_SCRIPT
    assert "document.addEventListener('pointerout'" in TOOLTIP_SCRIPT
    assert "document.addEventListener('focusin'" in TOOLTIP_SCRIPT
    assert "document.addEventListener('focusout'" in TOOLTIP_SCRIPT
    assert "window.setTimeout" in TOOLTIP_SCRIPT
    assert "getBoundingClientRect()" in TOOLTIP_SCRIPT
    assert "viewportWidth" in TOOLTIP_SCRIPT
    assert "viewportHeight" in TOOLTIP_SCRIPT
    assert "button.closest('.ide>.rail')" in TOOLTIP_SCRIPT
    assert "button.closest('.right-tools')" in TOOLTIP_SCRIPT
    assert "window.addEventListener('scroll',hide,true)" in TOOLTIP_SCRIPT
    assert "window.addEventListener('blur'" in TOOLTIP_SCRIPT
    assert "event.key==='Escape'" in TOOLTIP_SCRIPT


def test_disabled_feature_icons_still_receive_pointer_and_keyboard_focus():
    assert "const unavailable=entry.state==='unavailable';" in EDGE_PROFILE_SCRIPT
    assert "button.setAttribute('aria-disabled',String(unavailable));" in EDGE_PROFILE_SCRIPT
    assert "if(!unavailable)button.addEventListener('click',()=>clickExisting(entry));" in EDGE_PROFILE_SCRIPT
    assert "button.disabled=entry.state==='unavailable'" not in EDGE_PROFILE_SCRIPT
    assert '.pynix-extra-tool[aria-disabled="true"]' in EDGE_PROFILE_STYLE
    assert "button.dataset.toolWindow=entry.label;" in EDGE_PROFILE_SCRIPT
    assert "button.dataset.toolWindow||button.dataset.pynixTooltip" in TOOLTIP_SCRIPT


def test_tooltip_owns_style_instead_of_late_native_title_popup():
    assert "button.removeAttribute('title');" in TOOLTIP_SCRIPT
    assert "button.dataset.pynixTooltip=nativeTitle;" in TOOLTIP_SCRIPT
    assert "button.setAttribute('aria-label',accessible);" in TOOLTIP_SCRIPT
    assert "position:fixed!important;z-index:10000!important" in TOOLTIP_STYLE
    assert "background:#34353b;color:#d9dbe0" in TOOLTIP_STYLE
    assert "border:1px solid #70737b" in TOOLTIP_STYLE
    assert "pointer-events:none!important" in TOOLTIP_STYLE
    assert '.pynix-native-tooltip[hidden]' in TOOLTIP_STYLE
    assert "nameNode.textContent=label;" in TOOLTIP_SCRIPT
    assert "shortcutNode.textContent=shortcut;" in TOOLTIP_SCRIPT
    assert "document.body.appendChild(tip);" in TOOLTIP_SCRIPT


def test_native_v4_always_installs_single_tooltip_layer_both_theme_modes():
    source = (Path(__file__).resolve().parents[1] /
              "examples" / "ide_native_v4.py").read_text("utf-8")
    assert "from pynix_gui.ide_tooltips import apply_native_tooltips" in source
    assert "document = apply_native_tooltips(document)" in source
    assert source.index("document = apply_native_tooltips(document)") > source.index(
        "document = apply_iconless_mode(document)")
    assert source.index("document = apply_native_tooltips(document)") < source.index(
        "document = document.replace(\"</body>\", TOOLBAR_DRAG_SCRIPT")


def test_run_and_debug_use_dynamic_filenames_with_native_macos_shortcuts():
    from pynix_gui.ide_pycharm_chrome import CHROME_SCRIPT
    assert "'⌃R'" in CHROME_SCRIPT
    assert "'⌃D'" in CHROME_SCRIPT
    assert "control.dataset.pynixShortcut=shortcut;" in CHROME_SCRIPT
    assert "button.dataset.pynixShortcut||shortcuts[label]||''" in TOOLTIP_SCRIPT
    assert "button.dataset.pynixTooltip||button.dataset.toolWindow" in TOOLTIP_SCRIPT
    assert "'.pynix-current-config'" in TOOLTIP_SCRIPT
    assert "'.pynix-config-options button'" in TOOLTIP_SCRIPT
    assert "'.pynix-pycharm-center>.pynix-run-action'" in TOOLTIP_SCRIPT
    assert "'.pynix-pycharm-center>.pynix-debug-primary'" in TOOLTIP_SCRIPT
    assert "nameNode.textContent=label;" in TOOLTIP_SCRIPT
    assert "shortcutNode.textContent=shortcut;" in TOOLTIP_SCRIPT

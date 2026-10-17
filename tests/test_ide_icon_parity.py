"""Smoke tests for bundled JetBrains expui vectors in the live PYNIX IDE."""
from pathlib import Path

from pynix_gui.ide_icon_parity import (
    BUNDLED_ICONS, ICON_BINDINGS, apply_new_ui_icons,
)
from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog, check_svg, OFFICIAL_UNHEADERED_ICONS


def test_bundled_icons_are_original_licensed_vectors():
    svg_root = BUNDLED_ICONS / "svg"
    icons = sorted(svg_root.rglob("*.svg"))
    assert len(icons) >= 44, "The expanded licensed New UI vector pack must be present"
    for icon in icons:
        ok, reason = check_svg(icon, relative_path=icon.relative_to(svg_root))
        assert ok, f"{icon}: {reason}"
        relative_name = icon.relative_to(svg_root).as_posix()
        if relative_name in OFFICIAL_UNHEADERED_ICONS:
            # Exact upstream vector bytes are licensed by the parent JetBrains
            # Apache-2.0 repository and bound to this path + pinned SHA-256.
            import hashlib
            assert hashlib.sha256(
                icon.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest() == OFFICIAL_UNHEADERED_ICONS[relative_name]
        else:
            assert "Copyright" in icon.read_text(encoding="utf-8")
            assert "Apache 2.0 license" in icon.read_text(encoding="utf-8")
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for name in ("toolwindows/project", "toolwindows/find", "toolwindows/vcs",
                 "toolwindows/run", "toolwindows/debug", "general/search",
                 "general/settings", "general/refresh", "toolwindows/structure",
                 "toolwindows/documentation", "toolwindows/problems",
                 "toolwindows/notifications", "toolwindows/services",
                 "toolwindows/commit", "general/help",
                 "general/moreHorizontal", "run/run", "run/debug"):
        assert catalog.resolve(name, dark=True) is not None, name
        assert catalog.resolve(name, dark=False) is not None, name
    assert catalog.resolve("toolwindows/project", dark=True, tool_window=True).variant == "dark_20"


def test_native_workspace_imports_icons_after_navigation_bridge():
    native = (
        Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py"
    ).read_text(encoding="utf-8")
    assert "from pynix_gui.ide_icon_parity import apply_new_ui_icons" in native
    assert "document = apply_new_ui_icons(document)" in native
    assert native.index("document = attach_navigation_controls(document)") < native.index(
        "document = apply_new_ui_icons(document)"
    )


def test_icon_injection_preserves_actions_and_replaces_only_glyph_nodes():
    text = "<html><body class='workspace-mode'><button>Ready</button></body></html>"
    output = apply_new_ui_icons(text)
    assert output.startswith("<html><body class='workspace-mode'>")
    assert output.endswith("</body></html>")
    assert "pynix-jetbrains-icon" in output
    assert "old.replaceWith(icon);" in output
    assert "target.replaceChildren(icon);" in output
    assert "target.dataset.pynixIcon=item.name;" in output
    assert "target.addEventListener" not in output
    assert "pynixToolbarDragRegion" not in output
    # The source SVG header and icon theme colors remain intact.
    assert "Apache 2.0 license" in output
    assert "nodes/folder" in output
    assert "fileTypes/text" in output
    assert "general/chevronDown" in output
    assert "run/run" in output
    assert "toolwindows/project" not in output
    # Raw SVG is JSON escaped, not pasted as a second HTML/script tag.
    assert "<svg" not in output


def test_icon_injection_does_not_depend_on_unavailable_assets(tmp_path):
    original = "<html><body class='workspace-mode'>keep</body></html>"
    assert apply_new_ui_icons(original, tmp_path) == original
    assert apply_new_ui_icons("not an HTML document") == "not an HTML document"


def test_all_imported_buttons_already_exist_and_have_semantic_bindings():
    selectors = [row[0] for row in ICON_BINDINGS]
    assert len(selectors) == len(set(selectors))
    assert all(".workspace-mode" in selector for selector in selectors)
    assert len(selectors) >= 5
    assert not any(".rail > .rail-item" in selector for selector in selectors)
    assert not any(".right-tools" in selector for selector in selectors)
    assert any(".workspace-toolbar" in selector for selector in selectors)
    # The real project breadcrumb in the bottom status strip is a legitimate
    # non-interactive icon target; all other controls retain their actions.
    assert [sel for sel in selectors if ".bottom" in sel] == [
        ".workspace-mode .bottom > span:nth-of-type(1)"
    ]


def test_action_icon_bridge_does_not_compete_with_the_visible_edge_renderer():
    from pynix_gui.ide_icon_parity import ICON_BINDINGS

    bindings = {selector: name for selector, name, _, _ in ICON_BINDINGS}
    assert bindings[".workspace-mode .workspace-toolbar .pynix-run-action"] == "run/run"
    assert bindings[".workspace-mode .workspace-toolbar .pynix-debug-primary"] == "run/debug"
    assert all(".rail > .rail-item" not in selector for selector in bindings)
    assert all(".right-tools" not in selector for selector in bindings)
    # The only visible rail painter is now the dedicated New UI edge profile.
    from pynix_gui.ide_edge_profile import TOOL_WINDOW_PROFILE, EDGE_PROFILE_SCRIPT
    names = {label: icon for label, icon, _, _ in TOOL_WINDOW_PROFILE}
    assert names["Project"] == "toolwindows/project"
    assert names["Search"] == "toolwindows/find"
    assert names["Version Control"] == "toolwindows/vcs"
    assert "const place=(edge,host)=>{" in EDGE_PROFILE_SCRIPT


def test_project_tree_icons_use_original_new_ui_nodes_and_file_types():
    from pynix_gui.ide_icon_parity import DYNAMIC_ICON_BINDINGS, ICON_BRIDGE_SCRIPT

    bindings = {selector: name for selector, name, _ in DYNAMIC_ICON_BINDINGS}
    assert bindings[".workspace-mode .project-glyph[data-pynix-semantic='folder']"] == "nodes/folder"
    assert bindings[".workspace-mode .project-glyph[data-pynix-semantic='generic']"] == "fileTypes/text"
    assert bindings[".workspace-mode .project-chevron.folder-disclosure"] == "general/chevronDown"
    assert not any(".project-glyph.file-" in selector for selector in bindings)
    assert "target.replaceChildren(icon);" in ICON_BRIDGE_SCRIPT
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for icon in bindings.values():
        for dark in (True, False):
            resolved = catalog.resolve(icon, dark=dark)
            assert resolved is not None
            assert resolved.variant.startswith("dark" if dark else "light")
    assert "new MutationObserver(synchronize).observe(tree,{childList:true,subtree:true})" in ICON_BRIDGE_SCRIPT
    assert "const tree=document.querySelector('.workspace-mode .tree')" in ICON_BRIDGE_SCRIPT
    assert 'if(target.dataset.pynixIcon===item.name && target.querySelector(".pynix-jetbrains-icon"))return;' in ICON_BRIDGE_SCRIPT
    assert "for(const target of tree.querySelectorAll(item.selector))activate(target,item)" in ICON_BRIDGE_SCRIPT
    assert "new DOMParser()" in ICON_BRIDGE_SCRIPT
    assert "old.replaceWith(icon)" in ICON_BRIDGE_SCRIPT
    assert "target.addEventListener" not in ICON_BRIDGE_SCRIPT


def test_dynamic_file_icons_are_serialized_without_raw_svg_script_injection():
    document = "<html><body class='workspace-mode'></body></html>"
    output = apply_new_ui_icons(document)
    assert "fileTypes/json" in output
    assert "fileTypes/markdown" in output
    assert "fileTypes/text" in output
    assert "nodes/folder" in output
    assert "__DYNAMIC_ICON_DATA__" not in output
    assert "<svg" not in output
    assert "MutationObserver(synchronize)" in output


def test_editor_tabs_and_status_strip_are_native_icon_targets():
    from pynix_gui.ide_icon_parity import (
        DYNAMIC_ICON_BINDINGS, ICON_BINDINGS, ICON_BRIDGE_SCRIPT,
    )
    static = {selector: name for selector, name, _, _ in ICON_BINDINGS}
    dynamic = {selector: name for selector, name, _ in DYNAMIC_ICON_BINDINGS}
    assert static[".workspace-mode .bottom > span:nth-of-type(1)"] == "nodes/ideaProject"
    assert dynamic[".workspace-mode .pynix-tab-file-glyph.file-json"] == "fileTypes/json"
    assert dynamic[".workspace-mode .pynix-tab-file-glyph.file-markdown"] == "fileTypes/markdown"
    assert dynamic[".workspace-mode .pynix-tab-file-glyph.file-text"] == "fileTypes/text"
    assert not any("file-python" in selector or "file-pynix" in selector
                   for selector in dynamic)
    assert "const editorTabs=document.querySelector('.workspace-mode .editor-tabs')" in ICON_BRIDGE_SCRIPT
    assert "new MutationObserver(synchronizeTabs).observe(editorTabs,{childList:true,subtree:true})" in ICON_BRIDGE_SCRIPT
    assert 'if(target.dataset.pynixIcon===item.name && target.querySelector(".pynix-jetbrains-icon"))return;' in ICON_BRIDGE_SCRIPT

    native_css = (Path(__file__).resolve().parents[1] / "examples" /
                  "icon_direction_preview.html").read_text(encoding="utf-8")
    assert "/* V5.26: PyCharm-style file icons" in native_css
    assert ".workspace-mode .pynix-tab-file-glyph svg" in native_css
    assert ".workspace-mode .bottom .pynix-cursor-status" in native_css
    assert ".workspace-mode .bottom > span:nth-of-type(1) > .pynix-jetbrains-icon" in native_css


def test_original_icon_source_for_status_and_tabs_is_available():
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for key in ("nodes/ideaProject", "fileTypes/json",
                "fileTypes/markdown", "fileTypes/text"):
        assert catalog.resolve(key, dark=True) is not None
        assert catalog.resolve(key, dark=False) is not None


def test_extended_file_extension_catalog_bindings_are_correct_and_licensed():
    from pynix_gui.ide_icon_parity import DYNAMIC_ICON_BINDINGS, EXTENSION_ICON_NAMES
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    role_by_extension = dict(EXTENSION_ICON_NAMES)
    expected = {
        "js": "fileTypes/javaScript", "ts": "fileTypes/typeScript",
        "css": "fileTypes/css", "html": "fileTypes/html",
        "xml": "fileTypes/xml", "yaml": "fileTypes/yaml",
        "toml": "fileTypes/toml", "sh": "fileTypes/shell",
        "svg": "fileTypes/image", "zip": "fileTypes/archive",
    }
    for extension, name in expected.items():
        assert role_by_extension[extension] == name
    for extension, name in EXTENSION_ICON_NAMES:
        assert catalog.resolve(name, dark=True) is not None, (extension, name)
        selector = f".workspace-mode .pynix-tab-file-glyph[data-extension='{extension}']"
        assert (selector, name, False) in DYNAMIC_ICON_BINDINGS
        # Project uses neutral JetBrains glyphs rather than legacy extension colors.
        assert not any(".project-glyph[data-extension=" in x for x, _, _ in DYNAMIC_ICON_BINDINGS)
    assert len({key for key, _, _ in DYNAMIC_ICON_BINDINGS}) == len(DYNAMIC_ICON_BINDINGS)


def test_native_debugger_toolbar_uses_official_step_icons_and_accessible_buttons():
    from pynix_gui.ide_icon_parity import ICON_BINDINGS
    names = {selector: name for selector, name, _, _ in ICON_BINDINGS}
    actions = {
        "continue": "run/resume",
        "pause": "run/pause",
        "stepInto": "run/stepInto",
        "stepOver": "run/stepOver",
        "stepOut": "run/stepOut",
        "stop": "run/stop",
    }
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for action, icon_name in actions.items():
        selector = (
            ".workspace-mode .pynix-debug-panel-toolbar "
            f"[data-pynix-debug-action='{action}']"
        )
        assert names[selector] == icon_name
        assert catalog.resolve(icon_name, dark=True) is not None

    source = (Path(__file__).resolve().parents[1] /
              "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "control.dataset.pynixDebugAction=action;" in source
    assert "control.setAttribute('aria-label',label);" in source
    assert "control.addEventListener('click',()=>{" in source

    html = (Path(__file__).resolve().parents[1] / "examples" /
            "icon_direction_preview.html").read_text(encoding="utf-8")
    assert "/* V5.27: original JetBrains debugger glyphs" in html
    assert ".pynix-debug-icon-action .pynix-jetbrains-icon" in html
    assert "font-size:0!important" in html
    assert ".pynix-run-action:has(.pynix-jetbrains-icon)::before" in html


def test_new_ui_interaction_states_are_scoped_and_keyboard_accessible():
    from pynix_gui.ide_icon_parity import ICON_STATE_STYLE

    document = "<html><body class='workspace-mode'></body></html>"
    output = apply_new_ui_icons(document)
    assert output.count('id="pynix-new-ui-icon-states"') == 1
    assert output.index('id="pynix-new-ui-icon-states"') < output.index("pynix-jetbrains-icon")
    for selector in (
        ".workspace-mode .rail > .rail-item:hover",
        ".workspace-mode .right-tools > button:hover",
        ".workspace-mode .workspace-toolbar > button:hover",
        ".workspace-mode .rail > .rail-item.active",
        ".workspace-mode .right-tools > button[aria-pressed=\"true\"]",
        ".workspace-mode .pynix-debug-panel-toolbar [data-pynix-debug-action]:focus-visible",
    ):
        assert selector in ICON_STATE_STYLE
    assert "outline:2px solid #80b8f4!important" in ICON_STATE_STYLE
    assert "prefers-reduced-motion:reduce" in ICON_STATE_STYLE
    assert "pointer-events:none" not in ICON_STATE_STYLE
    assert "addEventListener" not in ICON_STATE_STYLE


def test_bottom_dock_icons_bind_after_dynamic_controls_mount():
    from pynix_gui.ide_icon_parity import DOCK_ICON_BINDINGS, ICON_BRIDGE_SCRIPT
    names = {selector: (name, replace) for selector, name, replace in DOCK_ICON_BINDINGS}
    assert names[".workspace-mode .pynix-tool-window-toggle"] == ("general/hide", True)
    assert names[".workspace-mode .pynix-tool-window-restore"] == ("toolwindows/messages", False)
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for _, name, _ in DOCK_ICON_BINDINGS:
        assert catalog.resolve(name, dark=True) is not None
        assert catalog.resolve(name, dark=False) is not None
    assert "const dockItems=__DOCK_ICON_DATA__;" in ICON_BRIDGE_SCRIPT
    assert 'new MutationObserver(sync).observe(host,{childList:true,subtree:true})' in ICON_BRIDGE_SCRIPT
    output = apply_new_ui_icons("<html><body class='workspace-mode'></body></html>")
    assert "__DOCK_ICON_DATA__" not in output
    assert "general/hide" in output
    assert "toolwindows/messages" in output
    assert "target.addEventListener" not in ICON_BRIDGE_SCRIPT


def test_perimeter_icon_geometry_has_consistent_scales_without_click_overlays():
    from pynix_gui.ide_icon_parity import ICON_STATE_STYLE
    style = ICON_STATE_STYLE
    for selector in (
        ".workspace-mode .rail > .rail-item > .pynix-jetbrains-icon",
        ".workspace-mode .right-tools > button > .pynix-jetbrains-icon",
    ):
        assert selector in style
    assert "width:20px!important;height:20px!important" in style
    assert "width:16px!important;height:16px!important" in style
    assert ".workspace-mode .pynix-tool-window-toggle:has(>.pynix-jetbrains-icon)" in style
    assert ".workspace-mode .pynix-tool-window-restore:has(>.pynix-jetbrains-icon)" in style
    assert "pointer-events:none" not in style
    assert "position:absolute" not in style


def test_icon_bridge_reapplication_is_idempotent_and_repairs_removed_icons():
    from pynix_gui.ide_icon_parity import ICON_BRIDGE_SCRIPT
    document = "<html><body class='workspace-mode'></body></html>"
    first = apply_new_ui_icons(document)
    assert apply_new_ui_icons(first) == first
    assert 'target.querySelector(".pynix-jetbrains-icon")' in ICON_BRIDGE_SCRIPT
    assert 'for(const target of document.querySelectorAll(item.selector))activate(target,item)' in ICON_BRIDGE_SCRIPT
    assert 'new MutationObserver(syncStatic).observe(host,{childList:true,subtree:true})' in ICON_BRIDGE_SCRIPT
    assert 'const shell=document.querySelector' not in ICON_BRIDGE_SCRIPT
    assert '".workspace-mode .workspace-toolbar"' in ICON_BRIDGE_SCRIPT
    assert '".workspace-mode .right-tools"' in ICON_BRIDGE_SCRIPT

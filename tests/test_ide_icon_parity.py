"""Smoke tests for bundled JetBrains expui vectors in the live PYNIX IDE."""
from pathlib import Path

from pynix_gui.ide_icon_parity import (
    BUNDLED_ICONS, ICON_BINDINGS, apply_new_ui_icons,
)
from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog, check_svg


def test_bundled_icons_are_original_licensed_vectors():
    svg_root = BUNDLED_ICONS / "svg"
    icons = sorted(svg_root.rglob("*.svg"))
    assert len(icons) >= 44, "The expanded licensed New UI vector pack must be present"
    for icon in icons:
        ok, reason = check_svg(icon, relative_path=icon.relative_to(svg_root))
        assert ok, f"{icon}: {reason}"
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
    assert "toolwindows/project" in output
    assert "toolwindows/find" in output
    assert "general/settings" in output
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
    assert any(".rail > .rail-item:nth-child(1)" in selector for selector in selectors)
    assert any(".workspace-toolbar" in selector for selector in selectors)
    assert not any("bottom" in selector for selector in selectors)


def test_jetbrains_icons_are_attached_only_to_existing_rail_and_run_controls():
    from pynix_gui.ide_icon_parity import ICON_BINDINGS

    bindings = {selector: name for selector, name, _, _ in ICON_BINDINGS}
    assert bindings[".workspace-mode .rail > .rail-item:nth-child(1)"] == "toolwindows/project"
    assert bindings[".workspace-mode .rail > .rail-item:nth-child(2)"] == "toolwindows/find"
    assert bindings[".workspace-mode .rail > .rail-item:nth-child(3)"] == "toolwindows/vcs"
    assert bindings[".workspace-mode .rail > .rail-item:nth-child(4)"] == "toolwindows/run"
    assert bindings[".workspace-mode .workspace-toolbar .pynix-run-action"] == "run/run"
    assert bindings[".workspace-mode .workspace-toolbar .pynix-debug-primary"] == "run/debug"
    assert bindings[".workspace-mode .right-tools > button[title='Outline']"] == "toolwindows/structure"
    assert bindings[".workspace-mode .right-tools > button[title='Documentation']"] == "toolwindows/documentation"
    assert not any("AI tools" in selector for selector in bindings)

    html = (
        Path(__file__).resolve().parents[1] / "examples" /
        "icon_direction_preview.html"
    ).read_text(encoding="utf-8")
    assert "/* V5.25: native JetBrains New UI glyph scale" in html
    assert ".workspace-mode .rail .rail-item > .pynix-jetbrains-icon" in html
    assert ".workspace-mode .right-tools .pynix-jetbrains-icon" in html
    assert ".workspace-mode .workspace-toolbar .pynix-jetbrains-icon" in html


def test_project_tree_icons_use_original_new_ui_nodes_and_file_types():
    from pynix_gui.ide_icon_parity import DYNAMIC_ICON_BINDINGS, ICON_BRIDGE_SCRIPT

    bindings = {selector: name for selector, name, _ in DYNAMIC_ICON_BINDINGS}
    assert bindings[".workspace-mode .project-glyph.folder-icon"] == "nodes/folder"
    assert bindings[".workspace-mode .project-glyph.file-json"] == "fileTypes/json"
    assert bindings[".workspace-mode .project-glyph.file-markdown"] == "fileTypes/markdown"
    assert bindings[".workspace-mode .project-glyph.file-text"] == "fileTypes/text"
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for icon in bindings.values():
        for dark in (True, False):
            resolved = catalog.resolve(icon, dark=dark)
            assert resolved is not None
            assert resolved.variant.startswith("dark" if dark else "light")
    assert "new MutationObserver(synchronize).observe(tree,{childList:true,subtree:true})" in ICON_BRIDGE_SCRIPT
    assert "const tree=document.querySelector('.workspace-mode .tree')" in ICON_BRIDGE_SCRIPT
    assert "if(!target||target.dataset.pynixIcon===item.name)return;" in ICON_BRIDGE_SCRIPT
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

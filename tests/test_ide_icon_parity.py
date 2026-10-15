"""Smoke tests for bundled JetBrains expui vectors in the live PYNIX IDE."""
from pathlib import Path

from pynix_gui.ide_icon_parity import (
    BUNDLED_ICONS, ICON_BINDINGS, apply_new_ui_icons,
)
from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog, check_svg


def test_bundled_icons_are_original_licensed_vectors():
    svg_root = BUNDLED_ICONS / "svg"
    icons = sorted(svg_root.rglob("*.svg"))
    assert len(icons) >= 16, "The first approved New UI vector pack must be present"
    for icon in icons:
        ok, reason = check_svg(icon, relative_path=icon.relative_to(svg_root))
        assert ok, f"{icon}: {reason}"
        assert "Copyright" in icon.read_text(encoding="utf-8")
        assert "Apache 2.0 license" in icon.read_text(encoding="utf-8")
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for name in ("toolwindows/project", "toolwindows/find", "toolwindows/vcs",
                 "toolwindows/run", "toolwindows/debug", "general/search",
                 "general/settings", "general/refresh"):
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

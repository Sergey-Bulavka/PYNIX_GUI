"""A single visible icon source and licensed New UI fallback boundaries."""
import xml.etree.ElementTree as ET

from pynix_gui.ide_icon_parity import BUNDLED_ICONS
from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog, check_svg
from pynix_gui.ide_icon_parity import (
    TREE_ICON_BINDINGS, ICON_BINDINGS, DYNAMIC_ICON_BINDINGS,
)
from pynix_gui.ide_edge_profile import (
    TOOL_WINDOW_PROFILE, PINNED_TOOLS, EDGE_PROFILE_STYLE,
    EDGE_PROFILE_SCRIPT,
)


def test_all_visible_top_left_vectors_are_licensed_jetbrains_originals():
    from pynix_gui.ide_edge_profile import TOP_LEFT_ICONS
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for label, key, edge, _ in TOOL_WINDOW_PROFILE:
        if edge != "left-top" or label not in TOP_LEFT_ICONS:
            continue
        for dark in (False, True):
            resolved = catalog.resolve(key, dark=dark, tool_window=True)
            assert resolved is not None, (label, dark)
            assert check_svg(resolved.svg_path)[0], (label, dark)
            svg = catalog.svg(key, dark=dark, tool_window=True)
            assert "JetBrains s.r.o." in svg
            assert "Apache 2.0 license" in svg
            assert ET.fromstring(svg).tag.endswith("svg")
    assert catalog.resolve("general/moreHorizontal", dark=True, tool_window=True)


def test_one_authority_for_each_visible_rail_and_project_glyph():
    assert {"Project", "Commit", "Pull Requests", "Structure",
            "Run", "Terminal"} <= PINNED_TOOLS
    assert '.workspace-mode .ide>.rail>.rail-item{display:none!important}' in EDGE_PROFILE_STYLE
    assert "button.querySelectorAll('svg').forEach(svg=>svg.remove());" in EDGE_PROFILE_SCRIPT
    from pynix_gui.ide_edge_profile import apply_edge_profile
    import inspect
    source = inspect.getsource(apply_edge_profile)
    assert "native_tool_icon" not in source
    assert 'catalog.svg(key, dark=dark, tool_window=True)' in source
    assert 'catalog.svg("general/moreHorizontal"' in source
    assert not any(".rail > .rail-item" in selector or ".right-tools" in selector
                   for selector, _, _, _ in ICON_BINDINGS)
    assert len(TREE_ICON_BINDINGS) == 3
    assert all(".project-glyph" not in s or "data-pynix-semantic" in s
               for s, _, _ in DYNAMIC_ICON_BINDINGS)


def test_project_source_does_not_create_old_generic_or_folder_vectors():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] /
              "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "glyph.dataset.pynixSemantic=entry.folder?'folder':" in source
    assert "glyph.innerHTML=entry.folder?(isOpen?icon['folder-open']:icon.folder):fileIconMarkup(fileType)" not in source
    assert "glyph.dataset.pynixSemantic==='python'||glyph.dataset.pynixSemantic==='pynix'" in source
    assert "chevron.classList.add('folder-disclosure');" in source

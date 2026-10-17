"""A single visible icon source and licensed New UI fallback boundaries."""
import xml.etree.ElementTree as ET

from pynix_gui.ide_native_tool_icons import native_tool_icon
from pynix_gui.ide_icon_parity import (
    TREE_ICON_BINDINGS, ICON_BINDINGS, DYNAMIC_ICON_BINDINGS,
)
from pynix_gui.ide_edge_profile import (
    TOOL_WINDOW_PROFILE, PINNED_TOOLS, EDGE_PROFILE_STYLE,
    EDGE_PROFILE_SCRIPT,
)


def test_fallback_vectors_are_original_monochrome_accessible_and_bounded():
    for dark in (False, True):
        for name in ("Terminal", "AI Assistant", "Pull Requests"):
            svg = native_tool_icon(name, dark=dark)
            assert svg is not None
            root = ET.fromstring(svg)
            assert root.tag == "{http://www.w3.org/2000/svg}svg"
            assert root.attrib["width"] == "20"
            assert root.attrib["height"] == "20"
            assert "currentColor" in svg
            assert "<script" not in svg
    assert native_tool_icon("Python Console") is None


def test_one_authority_for_each_visible_rail_and_project_glyph():
    assert {"Project", "Commit", "Pull Requests", "Structure",
            "Run", "Terminal"} <= PINNED_TOOLS
    assert '.workspace-mode .ide>.rail>.rail-item{display:none!important}' in EDGE_PROFILE_STYLE
    assert "button.querySelectorAll('svg').forEach(svg=>svg.remove());" in EDGE_PROFILE_SCRIPT
    assert "native_tool_icon(label, dark=dark)" in __import__(
        "inspect").getsource(__import__(
        "pynix_gui.ide_edge_profile", fromlist=["apply_edge_profile"]).apply_edge_profile)
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

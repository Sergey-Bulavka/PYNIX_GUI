"""PYNIX brand marks match the existing project identity at JetBrains UI size."""
from pathlib import Path
from xml.etree import ElementTree as ET

from pynix_gui.ide_edge_profile import (
    apply_edge_profile, PYNIX_BRANDED_TOOLS, PYNIX_BRAND_ICON_FILES,
    BOTTOM_LEFT_ICONS, TOOL_WINDOW_PROFILE, EDGE_PROFILE_STYLE,
)
from pynix_gui.ide_iconless_mode import ICONLESS_STYLE

ICON_DIR = Path(__file__).resolve().parents[1] / "pynix_gui" / "assets" / "icons"
NS = "{http://www.w3.org/2000/svg}"


def _paths(name: str):
    root = ET.fromstring((ICON_DIR / name).read_text(encoding="utf-8"))
    assert root.tag == NS + "svg"
    assert root.attrib["width"] == root.attrib["height"] == "20"
    assert root.attrib["viewBox"] == "0 0 20 20"
    assert "currentColor" in (ICON_DIR / name).read_text(encoding="utf-8")
    assert not list(root.iter(NS + "image"))
    assert not list(root.iter(NS + "rect"))  # No PNG/document/page background.
    return list(root.iter(NS + "path"))


def test_pynix_terminal_uses_crisp_strokes_at_jetbrains_20px_scale():
    root = ET.fromstring((ICON_DIR / "pynix-terminal.svg").read_text("utf-8"))
    paths = _paths("pynix-terminal.svg")
    assert len(paths) == 2
    assert root.attrib["fill"] == "none"
    outer, logo = paths
    assert outer.attrib["d"] == "M10 2 17 6v8l-7 4-7-4V6Z"
    assert outer.attrib["stroke-width"] == "1.45"
    assert logo.attrib["d"] == (
        "M6.8 12.8V7.1L10 5.3l3.4 2V9L10 11"
        "l-1.1-.6v3.15L10 14.3l3.4-1.9"
    )
    assert logo.attrib["stroke-width"] == "1.3"
    assert all(p.attrib["stroke"] == "currentColor" for p in paths)
    assert all("transform" not in p.attrib for p in paths)
    assert all("fill-rule" not in p.attrib for p in paths)
    assert all("fill" not in p.attrib for p in paths)


def test_packages_has_one_unbroken_box_and_shared_pynix_symbol_not_a_sticker():
    root = ET.fromstring((ICON_DIR / "pynix-packages.svg").read_text("utf-8"))
    paths = _paths("pynix-packages.svg")
    assert len(paths) == 3
    box, folded_edges, logo = paths
    assert box.attrib["d"] == "M10 1.9 17.5 6.1v8L10 18.1 2.5 14.1v-8Z"
    assert folded_edges.attrib["d"] == (
        "M2.7 6.25 10 10.1l7.3-3.85M10 10.1v7.8"
    )
    assert box.attrib["stroke-width"] == "1.5"
    assert folded_edges.attrib["stroke-width"] == "1.45"
    assert logo.attrib["d"] == _paths("pynix-terminal.svg")[1].attrib["d"]
    assert logo.attrib["stroke-width"] == "2"
    groups = list(root.iter(NS + "g"))
    assert len(groups) == 1
    # A *single* explicit scale/translate (unlike the previously stacked,
    # miniature bitmap tracing). Effective inset stroke width = 2 * .55 = 1.1.
    assert groups[0].attrib["transform"] == "matrix(.55 0 0 .55 8.2 7.1)"
    assert all(p.attrib["stroke"] == "currentColor" for p in paths)
    assert all("fill" not in p.attrib for p in paths)
    assert not list(root.iter(NS + "clipPath"))
    assert not list(root.iter(NS + "mask"))
    assert "pythonPackages" not in (ICON_DIR / "pynix-packages.svg").read_text("utf-8")



def test_icon_profile_loads_our_two_monochrome_svgs_not_png_or_python():
    assert PYNIX_BRANDED_TOOLS == frozenset(PYNIX_BRAND_ICON_FILES)
    assert PYNIX_BRAND_ICON_FILES == {
        "PYNIX Terminal": "pynix-terminal.svg",
        "PYNIX Packages": "pynix-packages.svg",
    }
    label_icon = {label: icon for label, icon, _, _ in TOOL_WINDOW_PROFILE}
    assert label_icon["PYNIX Terminal"] == "pynix/pynix-terminal"
    assert label_icon["PYNIX Packages"] == "pynix/pynix-packages"
    html = apply_edge_profile(
        "<html><body class='workspace-mode'></body></html>", iconless=True)
    for word in ("PYNIX Terminal", "PYNIX Packages"):
        assert '"label": "' + word + '"' in html
    assert r"\u003csvg" in html
    assert '"isPynixBrand": true' in html
    assert "data:image/png;base64" not in html
    # The provenance comment may name the source PNG; no raster is displayed.
    assert r"\u003cimage" not in html
    assert "<img" not in html
    assert "entry.brand" not in html


def test_svg_only_contract_stays_20px_dimmed_and_packaged():
    assert '.pynix-extra-tools[data-edge="left-bottom"]' in ICONLESS_STYLE
    assert '.pynix-extra-tool svg' in ICONLESS_STYLE
    assert 'pynix-window-inactive' in EDGE_PROFILE_STYLE
    assert ".pynix-extra-tool[data-pynix-brand]" in EDGE_PROFILE_STYLE
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8")
    assert '"assets/icons/*.svg"' in pyproject

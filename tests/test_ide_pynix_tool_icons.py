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


def test_pynix_terminal_preserves_original_solid_geometric_mark_at_20px():
    root = ET.fromstring((ICON_DIR / "pynix-terminal.svg").read_text("utf-8"))
    paths = _paths("pynix-terminal.svg")
    assert len(paths) == 3
    assert root.attrib["shape-rendering"] == "geometricPrecision"
    assert root.attrib["fill"] == "none"
    outer, middle, lower = paths
    assert outer.attrib["d"] == (
        "M10 1.35 18 5.8V10.65L15.15 12.3V7.6L10 4.7 "
        "5.15 7.6V17L2 15.2V5.8Z"
    )
    assert middle.attrib["d"] == "M8 9.3 10 8.1 12.6 9.6 8 12.45Z"
    assert lower.attrib["d"] == "M8 12.45 11 14.25 18 10.25V15L10 19 8 17.9Z"
    # The original PYNIX logomark has a continuous solid silhouette, not
    # a thin hexagon with illegible nested strokes or transformed fragments.
    assert all(p.attrib["fill"] == "currentColor" for p in paths)
    assert all("stroke-width" not in p.attrib for p in paths)
    assert all("transform" not in p.attrib for p in paths)
    assert not list(root.iter(NS + "g"))


def test_pynix_packages_is_coherent_20px_box_with_integral_readable_monogram():
    root = ET.fromstring((ICON_DIR / "pynix-packages.svg").read_text("utf-8"))
    paths = _paths("pynix-packages.svg")
    assert len(paths) == 3
    box, folded_edges, inset = paths
    assert root.attrib["shape-rendering"] == "geometricPrecision"
    assert box.attrib["d"] == "M10 1.85 17.5 6v8L10 18.1 2.5 14V6Z"
    assert folded_edges.attrib["d"] == (
        "M2.5 6 10 10.15 17.5 6M10 10.15V18"
    )
    assert inset.attrib["d"] == "M12 15.7V12.1L13.5 11.2 15.1 12.1 13 13.4"
    assert [p.attrib["stroke-width"] for p in paths] == ["1.5", "1.4", "1.2"]
    assert all(p.attrib["stroke"] == "currentColor" for p in paths)
    assert all("transform" not in p.attrib for p in paths)
    assert not list(root.iter(NS + "g"))
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

def test_all_native_tool_svg_paths_use_antialiasing_not_pixelated_mode():
    from pynix_gui.ide_iconless_mode import ICONLESS_STYLE
    for selector in (
        ".workspace-mode svg",
        ".workspace-mode svg path",
        ".workspace-mode svg circle",
        ".workspace-mode svg rect",
        ".workspace-mode svg line",
        ".workspace-mode svg polyline",
        ".workspace-mode svg polygon",
    ):
        assert selector in ICONLESS_STYLE
    assert "shape-rendering:geometricPrecision!important;" in ICONLESS_STYLE
    assert "image-rendering:auto!important;" in ICONLESS_STYLE
    assert "max-width:20px!important;max-height:20px!important;" in ICONLESS_STYLE
    assert "transform:none!important;" in ICONLESS_STYLE
    assert "image-rendering:pixelated" not in ICONLESS_STYLE
    assert "shape-rendering:crispEdges" not in ICONLESS_STYLE


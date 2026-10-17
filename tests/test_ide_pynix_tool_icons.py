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


def test_pynix_terminal_is_the_pure_existing_logo_mark():
    paths = _paths("pynix-terminal.svg")
    assert len(paths) == 1
    logo = paths[0]
    assert logo.attrib["fill"] == "currentColor"
    assert logo.attrib["fill-rule"] == "evenodd"
    assert logo.attrib["transform"] == "translate(-4.88 -8.29) scale(0.62)"
    assert "M24 16L12 23V35L24 43L36 35V23L24 16Z" in logo.attrib["d"]


def test_pynix_packages_replaces_python_with_exact_same_pynix_logo():
    source = _paths("pynix-terminal.svg")[0]
    paths = _paths("pynix-packages.svg")
    assert len(paths) == 2
    box, mark = paths
    assert box.attrib["fill"] == "currentColor"
    assert box.attrib["d"].startswith("M1 5.65028C1 5.25509")
    assert mark.attrib["d"] == source.attrib["d"]
    assert "translate(8.8 8.5)" in mark.attrib["transform"]
    assert mark.attrib["fill-rule"] == "evenodd"
    # Exactly two paths: the unchanged JetBrains box silhouette and our
    # PYNIX mark. None of the original Python snake paths are present.
    assert "M10.75 17C10.75 16.5858" not in (ICON_DIR / "pynix-packages.svg").read_text(
        encoding="utf-8")


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
    assert "pnx-file.png" not in html
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

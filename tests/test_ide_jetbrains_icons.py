"""Offline contracts for the licensed, category-wide JetBrains icon importer."""
from pathlib import Path

import pytest

from pynix_gui.ide_jetbrains_icons import (
    JetBrainsIconCatalog, _source_key, build_catalog, check_svg,
)


HEADER = (
    "<!-- Copyright 2000-2026 JetBrains s.r.o. and contributors. "
    "Use of this source code is governed by the Apache 2.0 license. -->\n"
)
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><path d="M1 1L5 5"/></svg>'


def create_icon(root: Path, relative: str, *,
                licensed: bool = True, svg: str = SVG) -> Path:
    file = root / relative
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text((HEADER if licensed else "") + svg, encoding="utf-8")
    return file


def test_catalog_key_preserves_categories_and_groups_resolution_variants():
    assert _source_key(Path("actions/add.svg")) == ("actions/add", "light_normal")
    assert _source_key(Path("actions/add_dark.svg")) == ("actions/add", "dark_normal")
    assert _source_key(Path("toolwindows/project@20x20_dark.svg")) == (
        "toolwindows/project", "dark_20"
    )
    assert _source_key(Path("toolwindows/project@2x.svg")) == (
        "toolwindows/project", "light_2x"
    )
    assert _source_key(Path("actions/project.svg")) != _source_key(
        Path("toolwindows/project.svg")
    )


def test_imports_all_licensed_categories_and_dark_variants(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    create_icon(source, "actions/add.svg")
    create_icon(source, "actions/add_dark.svg")
    create_icon(source, "toolwindows/project@20x20.svg")
    create_icon(source, "toolwindows/project@20x20_dark.svg")
    create_icon(source, "toolwindows/project.svg")
    create_icon(source, "nodes/folder.svg")
    create_icon(source, "vcs/branch.svg")
    manifest = build_catalog(source, destination)
    assert len(manifest["icons"]) == 4
    assert sum(len(parts) for parts in manifest["icons"].values()) == 7
    assert manifest["license"].endswith("LICENSE-2.0")
    assert (destination / "manifest.json").exists()
    icons = JetBrainsIconCatalog(destination)
    assert len(icons) == 4
    assert sorted(icons.names("toolwindows/")) == ["toolwindows/project"]
    assert icons.resolve("toolwindows/project", dark=True, tool_window=True).variant == "dark_20"
    assert icons.resolve("toolwindows/project", dark=False, compact=True).variant == "light_normal"
    assert icons.svg("actions/add", dark=True).startswith("<!-- Copyright")
    assert icons.resolve("nonexistent") is None
    assert icons.svg("nonexistent") is None


def test_import_never_copies_unlicensed_trademarks_or_remote_svg(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    create_icon(source, "actions/allowed.svg")
    create_icon(source, "actions/unlicensed.svg", licensed=False)
    create_icon(source, "productLogos/pycharm.svg")
    create_icon(source, "actions/splash.svg")
    create_icon(source, "actions/script.svg", svg=SVG.replace("<path", "<script>alert(1)</script><path"))
    create_icon(source, "actions/remote.svg", svg=SVG.replace("<path", '<image href="https://example.com/icon.svg"/><path'))
    create_icon(source, "actions/bad.svg", svg="<svg><path>")
    manifest = build_catalog(source, destination)
    assert set(manifest["icons"]) == {"actions/allowed"}
    assert manifest["skipped"] == {
        "license-not-explicit": 1, "trademark": 2,
        "unsafe-svg": 2, "malformed-svg": 1,
    }
    assert (destination / "svg/actions/allowed.svg").is_file()
    assert not (destination / "svg/actions/unlicensed.svg").exists()
    assert not (destination / "svg/productLogos/pycharm.svg").exists()


def test_dry_run_is_read_only_and_does_not_copy_icons(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    create_icon(source, "actions/run.svg")
    catalog = build_catalog(source, destination, dry_run=True)
    assert "actions/run" in catalog["icons"]
    assert not destination.exists()


def test_import_rejects_destination_nested_beneath_source(tmp_path):
    source = tmp_path / "upstream"
    source.mkdir()
    with pytest.raises(ValueError, match="Destination"):
        build_catalog(source, source / "out")


def test_runtime_detects_svg_modified_after_import(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    create_icon(source, "actions/run.svg")
    build_catalog(source, destination)
    icon = JetBrainsIconCatalog(destination)
    (destination / "svg/actions/run.svg").write_text("<svg></svg>", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from licensed manifest"):
        icon.svg("actions/run")


def test_source_path_does_not_falsely_trigger_trademark_restriction(tmp_path):
    path = create_icon(tmp_path / "JetBrains", "expui/actions/add.svg")
    assert check_svg(path)[0]
    assert check_svg(path, relative_path=Path("expui/actions/add.svg"))[0]


def test_gallery_covers_every_imported_category_and_is_searchable(tmp_path):
    from examples.icon_catalog_gallery import render_gallery

    source, destination = tmp_path / "source", tmp_path / "destination"
    create_icon(source, "actions/add.svg")
    create_icon(source, "toolwindows/project@20x20_dark.svg")
    create_icon(source, "nodes/folder.svg")
    build_catalog(source, destination)
    html = render_gallery(JetBrainsIconCatalog(destination))
    assert "actions/add" in html
    assert "toolwindows/project" in html
    assert "nodes/folder" in html
    assert "svg/toolwindows/project@20x20_dark.svg" in html
    assert 'id="query"' in html
    assert 'data-search="actions/add"' in html
    assert "3 licensed icons" in html

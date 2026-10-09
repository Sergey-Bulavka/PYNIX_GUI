# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import importlib.util
from pathlib import Path

import pytest

from pynix_gui import validate_view


def _gallery_module():
    path = Path(__file__).resolve().parents[1] / "examples" / "showcase.py"
    spec = importlib.util.spec_from_file_location("pynix_product_gallery", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _state(module):
    return {
        "search": "",
        "name": "PYNIX Developer",
        "notes": "Commercial defaults.",
        "checked": True,
        "appearance": 0,
        "scale": 72.0,
        "tree_selected": "main",
        "table_selected": "editor",
        "source": module.SOURCE,
        "selection_start": 0,
        "selection_end": 0,
    }


@pytest.mark.parametrize(
    "page",
    ["overview", "controls", "data", "editor", "canvas", "forms", "dashboard", "ide", "settings", "files"],
)
def test_product_gallery_page_is_valid_gui_tree(page):
    gallery = _gallery_module()
    validate_view(gallery.build(page, _state(gallery)))


def test_product_gallery_contains_four_application_examples():
    gallery = _gallery_module()
    pages = {page for page, _label in gallery.NAVIGATION}

    assert {"dashboard", "ide", "settings", "files"} <= pages


def test_product_gallery_canvas_labels_are_centered_inside_shape_bounds():
    gallery = _gallery_module()
    scene = gallery.product_scene()
    texts = {command.values[2]: command for command in scene.commands
             if command.kind == "text"}
    circle = texts["72%"]
    status = texts["HEALTHY"]
    assert circle.values == (320, 135, "72%", 150, 150)
    assert status.values == (530, 160, "HEALTHY", 160, 28)
    assert circle.text_align == status.text_align == "center"
    assert circle.text_valign == status.text_valign == "center"
    assert status.fill_role == "textOnAccent"
    assert texts["24.8k"].text_align == "start"


def _walk(view):
    yield view
    for child in view.children:
        yield from _walk(child)


def test_product_gallery_has_guided_entry_point_and_routes():
    gallery = _gallery_module()
    assert ("start", "Start Here") in gallery.NAVIGATION
    assert set(gallery.DISCOVERY_ROUTES.values()) <= {
        page for page, _label in gallery.NAVIGATION
    }
    for page in ("start", "overview"):
        view = gallery.build(page, _state(gallery))
        validate_view(view)
        actions = {
            node.target
            for node in _walk(view)
            if node.kind == "button" and node.target
        }
        assert "discover-start" in actions or "discover-controls" in actions
        assert any(target in gallery.DISCOVERY_ROUTES for target in actions)


def test_every_discovery_destination_is_valid_and_has_real_content():
    gallery = _gallery_module()
    for destination in gallery.DISCOVERY_ROUTES.values():
        view = gallery.page_view(destination, _state(gallery))
        validate_view(view)
        assert sum(1 for _ in _walk(view)) > 10


def test_guide_has_real_clickable_navigation_not_inert_promises():
    gallery = _gallery_module()
    guide = gallery.getting_started_page()
    buttons = {
        item.target for item in _walk(guide)
        if item.kind == "button" and item.target is not None
    }
    assert {"discover-controls", "discover-forms", "discover-ide"} <= buttons
    assert buttons <= set(gallery.DISCOVERY_ROUTES)

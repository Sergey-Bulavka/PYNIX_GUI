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


def test_workspace_compact_navigation_removes_sidebar_without_losing_content():
    gallery = _gallery_module()
    state = _state(gallery)
    regular = gallery.build("overview", state)
    state["compact_navigation"] = True
    compact = gallery.build("overview", state)
    validate_view(regular)
    validate_view(compact)
    def targets(root):
        return {node.target for node in _walk(root)
                if node.kind == "button" and node.target}
    assert "toggle-navigation" in targets(regular)
    assert "toggle-navigation" in targets(compact)
    assert "nav-overview" in targets(regular)
    assert "nav-overview" not in targets(compact)
    assert "discover-start" in targets(compact)


def test_workspace_compact_mode_preserves_all_pages():
    gallery = _gallery_module()
    state = _state(gallery)
    state["compact_navigation"] = True
    for page, label in gallery.NAVIGATION:
        root = gallery.build(page, state)
        validate_view(root)
        assert "toggle-navigation" in {
            node.target for node in _walk(root)
            if node.kind == "button" and node.target
        }


def test_workspace_visual_tokens_and_keyboard_discovery_are_consistent():
    from pynix_gui.design import WORKSPACE_METRICS
    assert WORKSPACE_METRICS["sidebarMinimum"] <= WORKSPACE_METRICS["sidebarMaximum"]
    assert WORKSPACE_METRICS["headerGap"] < WORKSPACE_METRICS["sectionGap"]
    assert WORKSPACE_METRICS["contentInset"] >= WORKSPACE_METRICS["sectionGap"]
    gallery = _gallery_module()
    guide = gallery.getting_started_page()
    copy = [node.text for node in _walk(guide)
            if node.kind == "text" and node.text]
    assert any("Keyboard-friendly" in item for item in copy)


def test_automatic_sidebar_switches_at_window_breakpoint_without_resetting_state():
    gallery = _gallery_module()
    state = _state(gallery)
    state["window_width"] = 1440
    state["navigation_override"] = None
    state["name"] = "Preserved entry"
    desktop = gallery.build("controls", state)
    state["window_width"] = 820
    narrow = gallery.build("controls", state)
    assert any(node.target == "nav-overview" for node in _walk(desktop))
    assert not any(node.target == "nav-overview" for node in _walk(narrow))
    assert any(node.text == "Preserved entry" or node.value == "Preserved entry"
               for node in _walk(narrow))
    state["window_width"] = 1440
    restored = gallery.build("controls", state)
    assert any(node.target == "nav-overview" for node in _walk(restored))


def test_manual_override_takes_priority_over_automatic_breakpoint():
    gallery = _gallery_module()
    state = _state(gallery)
    state["window_width"] = 820
    state["navigation_override"] = False
    forced_open = gallery.build("overview", state)
    assert any(node.target == "nav-overview" for node in _walk(forced_open))
    state["window_width"] = 1600
    state["navigation_override"] = True
    forced_closed = gallery.build("overview", state)
    assert not any(node.target == "nav-overview" for node in _walk(forced_closed))


def test_responsive_gallery_reflows_card_grids_without_losing_actions():
    gallery = _gallery_module()
    state = _state(gallery)
    for width, expected in [(1440, 3), (1000, 2), (620, 1)]:
        state["window_width"] = width
        state["navigation_override"] = None
        root = gallery.build("overview", state)
        validate_view(root)
        grids = [node for node in _walk(root) if node.kind == "grid"]
        assert any(node.columns == expected for node in grids)
        assert any(node.target == "discover-start" for node in _walk(root))


def test_responsive_pair_switches_to_column_at_narrow_width():
    gallery = _gallery_module()
    state = _state(gallery)
    from pynix_gui import button
    children = [button("responsive-a", "A"), button("responsive-b", "B")]
    state["window_width"] = 620
    narrow = gallery.responsive_pair(state, children)
    assert narrow.kind == "column"
    state["window_width"] = 1440
    wide = gallery.responsive_pair(state, children)
    assert wide.kind == "row"


def test_every_gallery_page_valid_at_three_responsive_widths():
    gallery = _gallery_module()
    state = _state(gallery)
    for width in (620, 1000, 1440):
        state["window_width"] = width
        state["navigation_override"] = None
        for page, _ in gallery.NAVIGATION:
            validate_view(gallery.build(page, state))

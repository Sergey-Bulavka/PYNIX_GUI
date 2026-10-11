# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

from examples.ide_shell_showcase import SOURCE, build, dispatch
from pynix_gui.core import validate_view
from pynix_gui.layout import layout


def state():
    return {
        "sidebar": True, "bottom": True, "editor": True,
        "expanded": ["src"], "selected": "main.pnx",
        "source": SOURCE, "tool_tab": "Terminal", "tool_message": "Ready",
    }


def test_ide_shell_builds_all_panels_from_gui_components():
    view = build(state())
    validate_view(view)


def test_ide_shell_toggles_panels_without_touching_editor_source():
    current = state()
    dispatch(current, SimpleNamespace(kind="ACTIVATE", target="shell-toggle-sidebar"))
    dispatch(current, SimpleNamespace(kind="ACTIVATE", target="shell-toggle-bottom"))
    assert current["sidebar"] is False
    assert current["bottom"] is False
    assert current["source"] == SOURCE
    validate_view(build(current))


def test_ide_shell_tool_tab_and_editor_selection():
    current = state()
    dispatch(current, SimpleNamespace(kind="ACTIVATE", target="shell-problems"))
    assert current["tool_tab"] == "Problems"
    assert current["bottom"] is True
    dispatch(current, SimpleNamespace(kind="ACTIVATE", target="shell-close-tab"))
    assert current["editor"] is False
    dispatch(current, SimpleNamespace(kind="SELECTION", target="shell-tree", item_id="main.pnx"))
    assert current["editor"] is True


def test_ide_shell_close_event_stops_loop():
    assert dispatch(state(), SimpleNamespace(kind="CLOSE", target=None)) is False


def test_ide_shell_layout_gives_editor_and_explorer_visible_area():
    scene = build(state())
    validate_view(scene)
    laid_out = layout(scene, 1440, 900)
    found = {}
    def walk(node):
        target = getattr(node.view, "target", None)
        if target:
            found[target] = node.rect
        for child in node.children:
            walk(child)
    walk(laid_out)
    assert found["shell-tree"].width >= 180
    assert found["shell-tree"].height >= 300
    assert found["shell-editor"].width >= 600
    assert found["shell-editor"].height >= 300

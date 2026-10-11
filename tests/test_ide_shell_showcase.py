# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

from examples.ide_shell_showcase import SOURCE, build, dispatch, initial_state, shell_menus
from pynix_gui.core import validate_view
from pynix_gui.layout import layout, measure


def assert_shell_valid(scene):
    """Report the offending subtree instead of only a root size error."""
    def check(node, path):
        try:
            measure(node)
        except ValueError as error:
            for index, child in enumerate(node.children):
                check(child, path + f"/{index}:{child.kind}")
            raise AssertionError(f"Invalid GUI constraints at {path}: {error}") from error
    check(scene, "root")
    validate_view(scene)


def event(kind, target=None, **kw):
    return SimpleNamespace(kind=kind, target=target, **kw)


def test_shell_all_panels_have_valid_constraints():
    state = initial_state()
    assert_shell_valid(build(state))
    assert shell_menus() is not None


def test_shell_panel_visibility_and_activity_are_controlled():
    state = initial_state()
    dispatch(state, event("ACTIVATE", "shell-toggle-sidebar"))
    assert not state["sidebar"]
    dispatch(state, event("ACTIVATE", "shell-activity-search"))
    assert state["sidebar"] and state["activity"] == "Search"
    dispatch(state, event("ACTIVATE", "shell-toggle-inspector"))
    assert state["inspector"]
    dispatch(state, event("ACTIVATE", "shell-toggle-bottom"))
    assert not state["bottom"]
    assert_shell_valid(build(state))


def test_shell_has_multiple_working_editor_tabs():
    state = initial_state()
    dispatch(state, event("SELECTION", "shell-tree", item_id="gui.pnx"))
    assert state["active"] == "gui.pnx"
    assert state["tabs"] == ["main.pnx", "gui.pnx"]
    dispatch(state, event("ACTIVATE", "shell-file-main.pnx"))
    assert state["active"] == "main.pnx"
    dispatch(state, event("ACTIVATE", "shell-close-tab"))
    assert state["active"] == "gui.pnx"
    assert state["tabs"] == ["gui.pnx"]
    assert state["source"] != SOURCE
    assert_shell_valid(build(state))


def test_shell_bottom_tools_and_visual_run():
    state = initial_state()
    dispatch(state, event("ACTIVATE", "shell-tool-problems"))
    assert state["tool_tab"] == "Problems"
    dispatch(state, event("ACTIVATE", "shell-run"))
    assert state["tool_tab"] == "Output"
    assert "no code executed" in state["tool_message"]
    assert_shell_valid(build(state))


def test_shell_open_project_and_close():
    state = initial_state()
    assert dispatch(state, event("CLOSE")) is False
    dispatch(state, event("ACTIVATE", "shell-project"))
    assert state["sidebar"]


def test_shell_visual_geometry_at_desktop_sizes():
    for width, height in ((1024, 640), (1280, 800), (1440, 900), (1920, 1080)):
        state = initial_state()
        scene = build(state)
        assert_shell_valid(scene)
        root = layout(scene, width, height)
        regions = {}
        def walk(node):
            target = getattr(node.view, "target", None)
            if target:
                regions[target] = node.rect
            for child in node.children:
                walk(child)
        walk(root)
        assert regions["shell-tree"].width >= 180
        assert regions["shell-tree"].height >= 240
        assert regions["shell-editor"].width >= 440
        assert regions["shell-editor"].height >= 180

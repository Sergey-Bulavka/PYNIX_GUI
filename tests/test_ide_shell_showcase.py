# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

from examples.ide_shell_showcase import (SOURCE, IDE_VERSION, build, dispatch, initial_state, shell_menus, search_everywhere_items)
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



def walk_view(view):
    yield view
    for child in view.children:
        yield from walk_view(child)


def test_topbar_search_settings_and_beta_version_are_present_and_semantic():
    state = initial_state()
    nodes = list(walk_view(build(state)))
    targets = {node.target for node in nodes if node.target}
    assert {"shell-search-everywhere", "shell-ide-settings",
            "shell-run", "shell-debug", "shell-more-actions",
            "shell-current-file", "shell-branch"} <= targets
    tooltips = [node.tooltip_text for node in nodes if node.kind == "tooltip"]
    assert any("Search Everywhere" in value and "Classes" in value
               and "Files" in value and "Settings" in value for value in tooltips)
    assert "IDE and Project Settings" in tooltips
    assert "Updates available. IDE and Project Settings" not in tooltips
    assert any(node.text == "Beta Version · " + IDE_VERSION for node in nodes)
    assert_shell_valid(build(state))


def test_topbar_update_dot_only_when_service_reports_updates():
    state = initial_state()
    assert not state["updates_available"]
    state["updates_available"] = True
    nodes = list(walk_view(build(state)))
    assert any(node.tooltip_text == "Updates available. IDE and Project Settings"
               for node in nodes)
    assert any(node.target == "shell-ide-settings" and "•" in node.text
               for node in nodes)
    assert_shell_valid(build(state))


def test_search_everywhere_indexes_real_preview_data_and_opens_results():
    state = initial_state()
    dispatch(state, event("ACTIVATE", "shell-search-everywhere"))
    assert state["everywhere_open"] and not state["settings_open"]
    dispatch(state, event("CHANGE", "shell-everywhere-query", text="gui"))
    assert ("Files", "gui.pnx", "shell-file-gui.pnx") in search_everywhere_items("gui")
    assert any(category == "Symbols" and "render" in title
               for category, title, _ in search_everywhere_items("render"))
    assert any(category == "Tool Windows"
               for category, _, _ in search_everywhere_items("terminal"))
    assert any(category == "Settings"
               for category, _, _ in search_everywhere_items("project settings"))
    dispatch(state, event("ACTIVATE", "shell-search-hit:shell-file-gui.pnx"))
    assert state["active"] == "gui.pnx"
    assert not state["everywhere_open"]
    assert_shell_valid(build(state))


def test_search_everywhere_does_not_dispatch_hidden_or_fabricated_results():
    state = initial_state()
    dispatch(state, event("ACTIVATE", "shell-search-everywhere"))
    dispatch(state, event("CHANGE", "shell-everywhere-query", text="settings"))
    before = state["active"]
    dispatch(state, event("ACTIVATE", "shell-search-hit:shell-file-gui.pnx"))
    assert state["active"] == before
    assert state["everywhere_open"]
    assert_shell_valid(build(state))


def test_settings_and_debug_controls_advertise_preview_limitations():
    state = initial_state()
    dispatch(state, event("ACTIVATE", "shell-ide-settings"))
    assert state["settings_open"] and not state["everywhere_open"]
    dispatch(state, event("ACTIVATE", "shell-settings-project-settings"))
    assert state["settings_page"] == "Project Settings"
    dispatch(state, event("ACTIVATE", "shell-settings-check-updates"))
    assert "not connected" in state["message"]
    dispatch(state, event("ACTIVATE", "shell-settings-close"))
    assert not state["settings_open"]
    dispatch(state, event("ACTIVATE", "shell-debug"))
    assert state["tool_tab"] == "Debug Console"
    assert "not connected" in state["tool_message"]
    assert_shell_valid(build(state))

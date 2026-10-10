# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Lazy tree acceptance: only expanded branches may be traversed."""

from pathlib import Path

from pynix_gui import GUIEvent, validate_view
from examples.project_explorer import ProjectExplorer
from examples.real_project_app import _nodes, build, dispatch


def _state():
    return {"expanded": ["__project_root__"], "preview": "", "message": "Ready",
            "show_hidden": False}


def _find(nodes, path):
    for node in nodes:
        if node.node_id == path:
            return node
        nested = _find(node.children, path)
        if nested is not None:
            return nested
    return None


def test_deep_folders_not_limited_to_four_levels(tmp_path):
    current = tmp_path
    for index in range(9):
        current = current / ("d" + str(index))
        current.mkdir()
    explorer = ProjectExplorer(tmp_path)
    state = _state()
    for index in range(9):
        prefix = "/".join("d" + str(i) for i in range(index + 1))
        nodes = _nodes(explorer, expanded=state["expanded"])
        assert _find(nodes, prefix) is None if index > 0 else True
        state["expanded"].append(prefix)
    nodes = _nodes(explorer, expanded=state["expanded"])
    assert _find(nodes, "/".join("d" + str(i) for i in range(9))) is not None
    validate_view(build(explorer, state))


def test_collapsed_branches_are_not_traversed(tmp_path):
    (tmp_path / "src" / "nested").mkdir(parents=True)
    (tmp_path / "other" / "deep").mkdir(parents=True)
    explorer = ProjectExplorer(tmp_path)
    calls = []
    original_entries = explorer.entries

    def tracking(folder=None):
        calls.append(folder)
        if folder == "src/nested" or folder == "other/deep":
            raise AssertionError("Unexpanded grandchildren must not be read")
        return original_entries(folder)

    explorer.entries = tracking
    nodes = _nodes(explorer)
    assert _find(nodes, "src") is not None
    assert _find(nodes, "src/nested") is None
    assert _find(nodes, "__lazy__/src") is not None


def test_tree_expand_and_collapse_preserve_other_branches(tmp_path):
    (tmp_path / "src" / "nested").mkdir(parents=True)
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    explorer = ProjectExplorer(tmp_path)
    state = _state()
    dispatch(explorer, state, GUIEvent("EXPANSION", target="real-project-tree",
                                      item_id="src", checked=True))
    assert "src" in state["expanded"]
    validate_view(build(explorer, state))
    dispatch(explorer, state, GUIEvent("EXPANSION", target="real-project-tree",
                                      item_id="src", checked=False))
    assert "src" not in state["expanded"]
    validate_view(build(explorer, state))


def test_navigating_directly_to_deep_folder_opens_ancestors(tmp_path):
    (tmp_path / "src" / "ui" / "components").mkdir(parents=True)
    explorer = ProjectExplorer(tmp_path)
    state = _state()
    explorer.folder = "src/ui/components"
    from examples.real_project_app import _expand_ancestors
    _expand_ancestors(state, explorer.folder)
    assert {"__project_root__", "src", "src/ui"} <= set(state["expanded"])
    validate_view(build(explorer, state))

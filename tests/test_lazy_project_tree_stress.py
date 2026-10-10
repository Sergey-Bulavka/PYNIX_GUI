# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Stress-oriented bounds checks for the local lazy folder explorer."""

from examples.project_explorer import ProjectExplorer
from examples.real_project_app import _nodes, _visible, build


def test_generated_directories_are_hidden_by_default(tmp_path):
    for name in ["__pycache__", ".git", ".venv", "node_modules", "src"]:
        (tmp_path / name).mkdir()
    explorer = ProjectExplorer(tmp_path)
    entries = explorer.entries()
    assert [e.name for e in entries if _visible(e, False)] == ["src"]
    assert {e.name for e in entries if _visible(e, True)} == {
        "__pycache__", ".git", ".venv", "node_modules", "src"
    }


def test_many_siblings_do_not_trigger_recursive_traversal(tmp_path):
    for index in range(160):
        parent = tmp_path / f"folder_{index:03d}"
        (parent / "child" / "grandchild").mkdir(parents=True)
    explorer = ProjectExplorer(tmp_path)
    original = explorer.entries
    visited = []
    def observe(folder=None):
        visited.append(folder)
        if folder and folder.count("/") >= 1:
            raise AssertionError("Collapsed subtree was traversed")
        return original(folder)
    explorer.entries = observe
    nodes = _nodes(explorer)
    assert len(nodes) == 160
    assert len(visited) <= 161
    assert all(node.has_children is True for node in nodes)


def test_open_one_branch_only_descends_into_that_branch(tmp_path):
    for index in range(60):
        (tmp_path / f"folder_{index:03d}" / "child" / "grandchild").mkdir(parents=True)
    explorer = ProjectExplorer(tmp_path)
    nodes = _nodes(explorer, expanded={"folder_020"})
    assert len(nodes) == 60
    opened = next(n for n in nodes if n.node_id == "folder_020")
    assert [c.label for c in opened.children] == ["child"]
    assert len([n for n in nodes if n.children]) == 1

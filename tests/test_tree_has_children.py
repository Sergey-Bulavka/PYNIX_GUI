# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import GUIError, tree_node, tree, validate_view


def test_declared_children_without_loaded_nodes():
    item = tree_node("folder", "Folder", kind="folder", has_children=True)
    assert item.children == ()
    assert item.has_children is True
    validate_view(tree("project", [item]))


def test_explicit_leaf_and_backwards_compatibility():
    leaf = tree_node("empty", "Empty", has_children=False)
    old = tree_node("parent", "Parent", [leaf])
    assert leaf.has_children is False
    assert old.has_children is None
    validate_view(tree("project", [old], expanded_ids=["parent"]))


@pytest.mark.parametrize("has_children", ["yes", 1, 0])
def test_invalid_declared_child_flag(has_children):
    with pytest.raises(GUIError):
        tree_node("item", "Folder", has_children=has_children)


def test_explicit_leaf_cannot_contain_nodes():
    with pytest.raises(GUIError):
        tree_node("parent", "Parent", [tree_node("child", "Child")],
                  has_children=False)

# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Shared tree explorer presentation rules; no platform handles in the model."""

from __future__ import annotations


def tree_node_kind(node) -> str:
    """Distinguish folders from documents without changing tree event IDs.

    Any expandable node is a folder. Leaf nodes are documents unless the
    caller explicitly sets the optional kind in a future semantic model.
    """
    return "folder" if node.children else "file"


def compact_tree_label_width(label: str, available: float) -> float:
    """Bound the clickable text/icon surface rather than filling the row."""
    if available <= 0:
        return 0.0
    estimated = max(56.0, len(label) * 8.3 + 46.0)
    return min(float(available), estimated)

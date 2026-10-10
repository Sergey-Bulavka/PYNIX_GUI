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


def tree_icon_size(row_height: float, font_size: float) -> float:
    """Native icon point size: font-led and always smaller than the row."""
    if row_height <= 0 or font_size <= 0:
        return 0.0
    return min(max(12.0, font_size * 1.18), row_height * 0.64)


def tree_disclosure_size(row_height: float, font_size: float) -> float:
    """A clearly visible chevron balanced with the item icon and row."""
    if row_height <= 0 or font_size <= 0:
        return 0.0
    return min(max(13.0, font_size * 1.16), row_height * 0.60)

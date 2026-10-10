# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Real Project Explorer V1: python -m examples.real_project_app /path/to/project.

Standalone GUI product example. No IDE-specific services are imported.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pynix_gui import (
    GUIRuntime, button, column, fill, max_size, padding, rich_editor, row,
    table, table_column, table_row, text, tree, tree_node, horizontal_split,
    vertical_split,
)
from pynix_gui.backends import default_backend

from .project_explorer import ProjectExplorer, ProjectExplorerError


def _nodes(explorer, folder="", depth=0, show_hidden=False):
    """Show folders only, bounded to prevent expensive workspace-wide scans.

    The right table remains the authoritative complete listing (including files).
    """
    if depth >= min(explorer.max_depth, 4):
        return []
    directories = [entry for entry in explorer.entries(folder)
                   if entry.is_directory and (show_hidden or not entry.name.startswith("."))]
    return [
        tree_node(entry.path, entry.name, _nodes(explorer, entry.path, depth + 1, show_hidden), kind="folder")
        for entry in directories
    ]


def _folder_ids(nodes):
    result = set()
    for node in nodes:
        result.add(node.node_id)
        result.update(_folder_ids(node.children))
    return result


def build(explorer, state):
    """Application-scoped model -> platform-independent GUI view."""
    entries = explorer.entries()
    rows = [
        table_row(entry.path, [
            entry.name,
            "Folder" if entry.is_directory else ("PYNIX" if entry.name.lower().endswith(".pnx") else "File"),
            "—" if entry.size is None else str(entry.size) + " B",
        ])
        for entry in entries
    ]
    selected = explorer.selected
    visible_ids = {entry.path for entry in entries}
    if selected not in visible_ids:
        selected = None

    editor = rich_editor(
        "real-project-preview",
        state["preview"], 0, 0, [], read_only=True,
    )
    folders = [tree_node("__project_root__", explorer.root.name, _nodes(explorer, show_hidden=state.get("show_hidden", False)), kind="folder")]
    visible_folders = _folder_ids(folders)
    expanded = [folder for folder in state["expanded"] if folder in visible_folders]
    current_folder = explorer.folder if explorer.folder in visible_folders else "__project_root__"
    left = column([
        text("Project folders", "subheading"),
        fill(tree(
            "real-project-tree",
            folders,
            expanded_ids=expanded,
            selected_id=current_folder,
        )),
    ], 8)
    right = column([
        row([
            button("real-project-up", "Up"),
            button("real-project-open", "Open"),
            button("real-project-refresh", "Refresh"),
            button("real-project-hidden", "Hide hidden" if state.get("show_hidden") else "Show hidden"),
            fill(text(explorer.folder or explorer.root.name, "caption")),
        ], 10),
        fill(vertical_split(
            table(
                "real-project-files",
                [
                    table_column("name", "Name", 290),
                    table_column("type", "Type", 130),
                    table_column("size", "Size", 110),
                ],
                rows, selected_id=selected,
            ),
            column([
                text(state["message"], "caption"),
                text("PYNIX source preview (read-only)", "subheading"),
                fill(editor),
            ], 8),
        )),
    ], 12)
    return padding(
        horizontal_split("real-project-layout", max_size(left, 300, 1200), fill(right), 290),
        16,
    )


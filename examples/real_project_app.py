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
)
from pynix_gui.backends import default_backend

from .project_explorer import ProjectExplorer, ProjectExplorerError


def _nodes(explorer, folder="", depth=0):
    # Lazy directory-only disclosure is a later enhancement; cap this preview.
    nodes = []
    for entry, children in explorer.tree(folder, depth=depth):
        nodes.append(tree_node(
            entry.path, entry.name,
            _tuples_to_nodes(children), kind="folder" if entry.is_directory else "file",
        ))
    return nodes


def _tuples_to_nodes(items):
    return [
        tree_node(
            entry.path, entry.name, _tuples_to_nodes(children),
            kind="folder" if entry.is_directory else "file",
        )
        for entry, children in items
    ]


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
    left = column([
        text("Project folders", "subheading"),
        fill(tree(
            "real-project-tree",
            [tree_node("__project_root__", explorer.root.name, _nodes(explorer), kind="folder")],
            expanded_ids=state["expanded"],
            selected_id=explorer.folder or "__project_root__",
        )),
    ], 8)
    right = column([
        row([
            button("real-project-up", "Up"),
            button("real-project-open", "Open"),
            button("real-project-refresh", "Refresh"),
            fill(text(explorer.folder or explorer.root.name, "caption")),
        ], 10),
        fill(table(
            "real-project-files",
            [
                table_column("name", "Name", 290),
                table_column("type", "Type", 130),
                table_column("size", "Size", 110),
            ],
            rows, selected_id=selected,
        )),
        text(state["message"], "caption"),
        text("PYNIX source preview (read-only)", "subheading"),
        fill(editor),
    ], 8)
    return padding(
        horizontal_split(max_size(left, 340, 1200), fill(right)),
        16,
    )


def dispatch(explorer, state, event):
    """Translate semantic events into application state; return False on close."""
    if event.kind == "CLOSE":
        return False
    try:
        if event.kind == "SELECTION" and event.target == "real-project-files":
            explorer.select(event.item_id)
        elif event.kind == "OPEN" and event.target == "real-project-files":
            _open(explorer, state, event.item_id)
        elif event.kind == "ACTIVATE" and event.target == "real-project-open":
            _open(explorer, state, None)
        elif event.kind == "ACTIVATE" and event.target == "real-project-up":
            explorer.up()
        elif event.kind == "ACTIVATE" and event.target == "real-project-refresh":
            explorer.entries()
        elif event.kind == "SELECTION" and event.target == "real-project-tree":
            path = event.item_id
            if path == "__project_root__":
                explorer.folder, explorer.selected = "", None
            elif explorer._resolve(path).is_dir():
                explorer.folder, explorer.selected = path, None
            else:
                state["message"] = "Select a file in the table to open it."
        elif event.kind == "EXPANSION" and event.target == "real-project-tree":
            expanded = set(state["expanded"])
            if event.checked:
                expanded.add(event.item_id)
            else:
                expanded.discard(event.item_id)
            state["expanded"] = sorted(expanded)
        state["message"] = state["message"] or "Ready"
    except ProjectExplorerError as exc:
        state["message"] = str(exc)
    return True


def _open(explorer, state, item_id):
    path = explorer.open(item_id)
    if path is None:
        state["message"] = "Folder: " + (explorer.folder or explorer.root.name)
        return
    if not path.lower().endswith(".pnx"):
        state["message"] = "Only .pnx files can be previewed."
        return
    state["preview"] = explorer.read_pnx(path)
    state["message"] = "Preview: " + path + " (read-only)"


def main():
    parser = argparse.ArgumentParser(description="PYNIX real project explorer")
    parser.add_argument("root", type=Path, help="Local project directory")
    args = parser.parse_args()
    explorer = ProjectExplorer(args.root)
    backend = default_backend()
    if backend is None:
        raise SystemExit("No native PYNIX GUI backend is available.")
    runtime = GUIRuntime(backend)
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI backend is unavailable.")
    state = {"expanded": ["__project_root__"], "preview": "", "message": "Ready"}
    window = runtime.open("PYNIX GUI — Real Project Explorer", 1160, 760)
    try:
        window.render(build(explorer, state))
        while True:
            event = window.next_event()
            if not dispatch(explorer, state, event):
                break
            window.render(build(explorer, state))
    finally:
        window.close()


if __name__ == "__main__":
    main()

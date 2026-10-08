# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Native macOS smoke for GUI-ADV-02 Tree and Table."""

from pynix_gui import (
    GUIRuntime,
    column,
    group,
    row,
    table,
    table_column,
    table_row,
    text,
    theme,
    tree,
    tree_node,
)
from pynix_gui.backends import MacOSGUIBackend


TREE_NODES = [
    tree_node(
        "src",
        "src",
        [
            tree_node("main", "main.pnx"),
            tree_node(
                "ui",
                "ui",
                [
                    tree_node("window", "window.pnx"),
                    tree_node("controls", "controls.pnx"),
                ],
            ),
        ],
    ),
    tree_node(
        "tests",
        "tests",
        [
            tree_node("test-main", "test_main.pnx"),
            tree_node("test-ui", "test_ui.pnx"),
        ],
    ),
    tree_node("readme", "README.md"),
]

TABLE_COLUMNS = [
    table_column("name", "Name", 220),
    table_column("kind", "Kind", 120),
    table_column("status", "Status", 120),
]

TABLE_ROWS = [
    table_row("file-main", ["main.pnx", "PYNIX", "Modified"]),
    table_row("file-window", ["window.pnx", "PYNIX", "Clean"]),
    table_row("file-controls", ["controls.pnx", "PYNIX", "Clean"]),
    table_row("file-readme", ["README.md", "Markdown", "Clean"]),
]


def build_root(expanded, tree_selected, table_selected):
    return theme(
        column([
            text("ADV-02 Tree & Table", "title"),
            text(
                "Stable identity, controlled selection and expansion.",
                "body",
            ),
            row([
                group(
                    column([
                        text("Project tree", "titleSmall"),
                        tree(
                            "project-tree",
                            TREE_NODES,
                            expanded_ids=sorted(expanded),
                            selected_id=tree_selected,
                        ),
                    ], 8),
                    "section",
                ),
                group(
                    column([
                        text("Files", "titleSmall"),
                        table(
                            "files-table",
                            TABLE_COLUMNS,
                            TABLE_ROWS,
                            selected_id=table_selected,
                        ),
                    ], 8),
                    "section",
                ),
            ], 16),
        ], 16),
        "system",
    )


def main():
    runtime = GUIRuntime(MacOSGUIBackend())
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI macOS backend is unavailable.")

    window = runtime.open("PYNIX GUI — ADV-02 Tree & Table", 980, 620)

    expanded = {"src", "ui"}
    tree_selected = "main"
    table_selected = "file-main"

    window.render(build_root(expanded, tree_selected, table_selected))

    while True:
        event = window.next_event()
        print("event:", event)

        if event.kind == "CLOSE":
            break

        if event.kind == "EXPANSION" and event.target == "project-tree":
            if event.checked:
                expanded.add(event.item_id)
            else:
                expanded.discard(event.item_id)
            window.render(build_root(expanded, tree_selected, table_selected))
            continue

        if event.kind == "SELECTION" and event.target == "project-tree":
            tree_selected = event.item_id
            window.render(build_root(expanded, tree_selected, table_selected))
            continue

        if event.kind == "SELECTION" and event.target == "files-table":
            table_selected = event.item_id
            window.render(build_root(expanded, tree_selected, table_selected))

    window.close()
    print("PYNIX GUI ADV-02 macOS smoke: PASS")


if __name__ == "__main__":
    main()

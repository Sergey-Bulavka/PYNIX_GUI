# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Cross-platform commercial showcase for PYNIX GUI."""

from pynix_gui import (
    GUIRuntime,
    button,
    canvas,
    canvas_ellipse,
    canvas_line,
    canvas_rect,
    canvas_scene,
    canvas_text,
    column,
    dialog,
    dialog_action,
    dock_panel,
    dock_placement,
    dock_state,
    dock_workspace,
    group,
    menu,
    menu_bar,
    menu_item,
    padding,
    rich_editor,
    row,
    shortcut,
    status_bar,
    table,
    table_column,
    table_row,
    text,
    text_span,
    theme,
    toolbar,
    tree,
    tree_node,
)
from pynix_gui.backends import default_backend


TREE = [
    tree_node(
        "src",
        "src",
        [
            tree_node("main", "main.pnx"),
            tree_node("ui", "ui", [tree_node("app", "app.pnx")]),
        ],
    ),
    tree_node("tests", "tests"),
]

COLUMNS = [
    table_column("name", "Name", 220),
    table_column("type", "Type", 120),
    table_column("state", "State", 120),
]

ROWS = [
    table_row("main", ["main.pnx", "PYNIX", "Modified"]),
    table_row("app", ["app.pnx", "PYNIX", "Clean"]),
    table_row("readme", ["README.md", "Markdown", "Clean"]),
]

SOURCE = """fn main() {
    let app = GUI.open("PYNIX")
    app.render(build())
}
"""


def source_spans(value):
    result = []
    for token, role in (
        ("fn", "keyword"),
        ("main", "function"),
        ("let", "keyword"),
        ("GUI", "type"),
        ('"PYNIX"', "string"),
    ):
        start = value.find(token)
        if start >= 0:
            result.append(text_span(start, start + len(token), role))
    return result


def scene():
    return canvas_scene(
        520,
        260,
        [
            canvas_rect(10, 10, 500, 240, fill="surface", stroke="borderStrong"),
            canvas_text(30, 45, "PYNIX GUI", role="titleLarge"),
            canvas_line(30, 70, 490, 70, stroke="separator"),
            canvas_rect(
                35, 105, 160, 90,
                fill="surfaceSelected",
                stroke="accent",
                hit_target="showcase-card",
            ),
            canvas_text(58, 155, "Interactive", role="titleSmall"),
            canvas_ellipse(
                250, 105, 90, 90,
                fill="accentMuted",
                stroke="accent",
                hit_target="showcase-circle",
            ),
        ],
    )


def make_dock_state():
    return dock_state(
        [
            dock_placement("project", "left"),
            dock_placement("editor", "center"),
            dock_placement("inspector", "right"),
            dock_placement("output", "bottom"),
        ],
        active_left="project",
        active_center="editor",
        active_right="inspector",
        active_bottom="output",
        left_width=230,
        right_width=250,
        bottom_height=150,
    )


def build(source, selection_start, selection_end, tree_selected, table_selected):
    project = dock_panel(
        "project",
        "Project",
        group(
            tree(
                "project-tree",
                TREE,
                expanded_ids=["src", "ui"],
                selected_id=tree_selected,
            ),
            "section",
        ),
    )

    editor = dock_panel(
        "editor",
        "Editor",
        rich_editor(
            "source-editor",
            source,
            selection_start,
            selection_end,
            source_spans(source),
        ),
        closable=False,
    )

    inspector = dock_panel(
        "inspector",
        "Inspector",
        group(
            table(
                "file-table",
                COLUMNS,
                ROWS,
                selected_id=table_selected,
            ),
            "section",
        ),
    )

    output = dock_panel(
        "output",
        "Output",
        group(
            column([
                text("Canvas preview", "titleSmall"),
                canvas("preview", scene()),
            ], 8),
            "section",
        ),
    )

    workspace = dock_workspace(
        "showcase-workspace",
        [project, editor, inspector, output],
        make_dock_state(),
    )

    return theme(
        column([
            toolbar(
                row([
                    button("new", "New", "primary"),
                    button("open-dialog", "Dialog"),
                    text("PYNIX Standard", "label"),
                ], 8)
            ),
            padding(workspace, 12),
            status_bar(
                row([
                    text("PYNIX GUI 0.1.x", "caption"),
                    text("Ready", "caption"),
                ], 12)
            ),
        ], 0),
        "system",
    )


def main():
    backend = default_backend()
    if backend is None:
        raise SystemExit("No native PYNIX GUI backend is available on this platform.")

    runtime = GUIRuntime(backend)
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI backend is unavailable.")

    window = runtime.open("PYNIX GUI Showcase", 1280, 820)
    window.set_menu_bar(
        menu_bar([
            menu(
                "File",
                [
                    menu_item("new", "New", shortcut("n", ["primary"])),
                    menu_item(
                        "open-dialog",
                        "Show Dialog",
                        shortcut("d", ["primary"]),
                    ),
                ],
            )
        ])
    )

    source = SOURCE
    selection_start = 0
    selection_end = 0
    tree_selected = "main"
    table_selected = "main"

    window.render(
        build(
            source,
            selection_start,
            selection_end,
            tree_selected,
            table_selected,
        )
    )

    while True:
        event = window.next_event()
        print("event:", event)

        if event.kind == "CLOSE":
            break

        if event.kind == "ACTIVATE" and event.target == "open-dialog":
            window.present_dialog(
                dialog(
                    "showcase-dialog",
                    "PYNIX GUI",
                    column([
                        text("Commercial desktop GUI toolkit", "title"),
                        text(
                            "The dialog uses the same semantic GUI model.",
                            "body",
                        ),
                    ], 12),
                    [
                        dialog_action(
                            "dialog-ok",
                            "Continue",
                            role="primary",
                            default=True,
                        )
                    ],
                )
            )
            continue

        if event.kind == "CHANGE" and event.target == "source-editor":
            source = event.text
            selection_start = min(selection_start, len(source))
            selection_end = min(selection_end, len(source))
        elif event.kind == "EDITOR_SELECTION" and event.target == "source-editor":
            selection_start = event.selection_start
            selection_end = event.selection_end
            continue
        elif event.kind == "SELECTION" and event.target == "project-tree":
            tree_selected = event.item_id
        elif event.kind == "SELECTION" and event.target == "file-table":
            table_selected = event.item_id
        elif event.kind == "EXPANSION":
            # The showcase keeps its initial expanded set fixed; dedicated ADV-02 smoke
            # verifies controlled expansion behavior.
            continue
        elif event.kind == "ACTIVATE" and event.target in {
            "showcase-card",
            "showcase-circle",
        }:
            print("canvas activation:", event.target)
            continue
        elif event.kind == "ACTIVATE" and event.target == "dialog-ok":
            continue
        elif event.kind == "ACTIVATE" and event.target == "new":
            source = SOURCE
            selection_start = selection_end = 0

        window.render(
            build(
                source,
                selection_start,
                selection_end,
                tree_selected,
                table_selected,
            )
        )

    window.close()
    print("PYNIX GUI cross-platform showcase: PASS")


if __name__ == "__main__":
    main()

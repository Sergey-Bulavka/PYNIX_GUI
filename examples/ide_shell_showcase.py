# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Visual-first PYNIX IDE shell. Run: python -m examples.ide_shell_showcase

Deliberately uses sample project data, not live IDE session/tooling services.
"""

from pynix_gui import (
    GUIRuntime, button, column, fill, horizontal_split, max_size, min_size,
    padding, rich_editor, row, text, text_span, tree, tree_node, vertical_split,
)
from pynix_gui.backends import default_backend


SOURCE = '''function main()
    message = "Hello from PYNIX"
    count = 3
    print(message)
'''
FILES = [
    tree_node("src", "src", [
        tree_node("main.pnx", "main.pnx"),
        tree_node("gui.pnx", "gui.pnx"),
        tree_node("tooling.pnx", "tooling.pnx"),
    ], kind="folder"),
    tree_node("tests", "tests", [
        tree_node("test_main.pnx", "test_main.pnx"),
    ], kind="folder"),
]


def build(state):
    top = row([
        text("PYNIX IDE", "titleSmall"),
        fill(text("  /  Visual Shell Preview", "caption")),
        button("shell-project", "Project"),
        button("shell-run", "Run"),
    ], 12)
    explorer = column([
        row([text("EXPLORER", "subheading"), fill(text("PYNIX", "caption"))], 8),
        fill(tree("shell-tree", FILES, expanded_ids=state["expanded"],
                  selected_id=state["selected"])),
    ], 8)
    if state["editor"]:
        center = column([
            row([
                text("main.pnx", "bodyStrong"),
                fill(text("PYNIX  /  src", "caption")),
                button("shell-close-tab", "×"),
            ], 8),
            fill(rich_editor(
                "shell-editor", state["source"], 0, 0,
                [text_span(0, 8, "keyword"),
                 text_span(32, 50, "string")],
                read_only=True,
            )),
        ], 8)
    else:
        center = column([
            fill(text("Select main.pnx in Explorer to open the editor", "body")),
        ], 8)
    tool_area = column([
        row([
            button("shell-problems", "Problems"),
            button("shell-output", "Output"),
            button("shell-terminal", "Terminal"),
            fill(text(state["tool_tab"], "caption")),
            button("shell-toggle-bottom", "Hide panel"),
        ], 8),
        fill(text(state["tool_message"], "body")),
    ], 8)
    if state["bottom"]:
        workspace = vertical_split("shell-workspace", fill(center), tool_area, 650)
    else:
        workspace = fill(center)
    main = horizontal_split("shell-explorer", explorer, fill(workspace), 270) if state["sidebar"] else fill(workspace)
    return padding(column([
        top,
        row([
            button("shell-toggle-sidebar", "Explorer"),
            button("shell-tab", "main.pnx"),
            fill(text("Project: PYNIX", "caption")),
        ], 8),
        fill(main),
        row([
            text("●  Ready", "caption"),
            fill(text("main.pnx    UTF-8    PYNIX", "caption")),
            text("Ln 1, Col 1", "caption"),
        ], 12),
    ], 8), 12)


def dispatch(state, event):
    if event.kind == "CLOSE":
        return False
    if event.kind == "ACTIVATE":
        if event.target == "shell-toggle-sidebar":
            state["sidebar"] = not state["sidebar"]
        elif event.target == "shell-toggle-bottom":
            state["bottom"] = not state["bottom"]
        elif event.target in ("shell-problems", "shell-output", "shell-terminal"):
            state["bottom"] = True
            state["tool_tab"] = event.target.replace("shell-", "").title()
            state["tool_message"] = {
                "shell-problems": "No problems found",
                "shell-output": "Build successful — visual shell preview",
                "shell-terminal": "Terminal session will connect in IDE integration phase",
            }[event.target]
        elif event.target == "shell-close-tab":
            state["editor"] = False
        elif event.target == "shell-tab":
            state["editor"] = True
        elif event.target == "shell-run":
            state["bottom"] = True
            state["tool_tab"] = "Output"
            state["tool_message"] = "Visual preview only — execution intentionally not connected"
        elif event.target == "shell-project":
            state["sidebar"] = True
    if event.kind == "EXPANSION" and event.target == "shell-tree":
        expanded = set(state["expanded"])
        if event.checked:
            expanded.add(event.item_id)
        else:
            expanded.discard(event.item_id)
        state["expanded"] = sorted(expanded)
    if event.kind == "SELECTION" and event.target == "shell-tree":
        state["selected"] = event.item_id
        if event.item_id == "main.pnx":
            state["editor"] = True
    return True


def main():
    backend = default_backend()
    if backend is None:
        raise SystemExit("No GUI backend available")
    runtime = GUIRuntime(backend)
    if not runtime.is_available():
        raise SystemExit("GUI backend unavailable")
    state = {
        "sidebar": True, "bottom": True, "editor": True,
        "expanded": ["src"], "selected": "main.pnx",
        "source": SOURCE, "tool_tab": "Terminal",
        "tool_message": "Ready — layout preview, no live subprocess",
    }
    window = runtime.open("PYNIX IDE — Visual Foundation V1", 1440, 900)
    try:
        window.render(build(state))
        while True:
            event = window.next_event()
            if not dispatch(state, event):
                break
            window.render(build(state))
    finally:
        window.close()


if __name__ == "__main__":
    main()

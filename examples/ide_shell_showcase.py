# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Visual-first, interactive IDE shell; no compiler or filesystem side effects.

Run: python -m examples.ide_shell_showcase
"""

from pynix_gui import (
    GUIRuntime, button, column, fill, max_size, min_size, padding,
    rich_editor, row, text, text_span, tree, tree_node, toolbar, status_bar,
    separator, menu, menu_bar, menu_item, search_field,
)
from pynix_gui.backends import default_backend

SOURCES = {
    "main.pnx": 'function main()\n    message = "Hello from PYNIX"\n    count = 3\n    print(message)\n',
    "gui.pnx": 'import ui\n\nfunction render()\n    return ui.column([])\n',
    "tooling.pnx": 'function inspect(source: String)\n    return source.len\n',
    "test_main.pnx": 'function test_main()\n    assert 1 + 1 == 2\n',
}
SOURCE = SOURCES["main.pnx"]
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


def initial_state():
    return {
        "sidebar": True, "bottom": True, "editor": True, "inspector": False,
        "expanded": ["src"], "selected": "main.pnx", "active": "main.pnx",
        "tabs": ["main.pnx"], "source": SOURCE,
        "tool_tab": "Terminal",
        "tool_message": "pynix$  Ready — visual preview, no live subprocess",
        "search": "", "activity": "Explorer", "message": "Ready",
    }


def source_spans(source):
    spans = []
    for token, role in (("function", "keyword"), ("import", "keyword"),
                        ("return", "keyword"), ("String", "type"),
                        ('"Hello from PYNIX"', "string")):
        start = source.find(token)
        if start >= 0:
            spans.append(text_span(start, start + len(token), role))
    return spans


def _activity_rail(state):
    return max_size(column([
        button("shell-activity-explorer", "▤", "primary" if state["activity"] == "Explorer" else "quiet"),
        button("shell-activity-search", "⌕", "primary" if state["activity"] == "Search" else "quiet"),
        button("shell-activity-run", "▶", "quiet"),
        button("shell-activity-settings", "⚙", "quiet"),
    ], 8), 54, 1200)


def _sidebar(state):
    if state["activity"] == "Search":
        return column([
            text("SEARCH", "overline"),
            search_field("shell-search", state["search"], "Find in workspace"),
            text("Preview only — no indexing or file search", "caption"),
            fill(text("Type a query to preview search", "caption")),
        ], 8)
    return column([
        row([text("EXPLORER", "overline"), fill(text("PYNIX", "caption"))], 8),
        separator("horizontal"),
        fill(tree("shell-tree", FILES, expanded_ids=state["expanded"],
                  selected_id=state["selected"])),
        separator("horizontal"),
        text("OUTLINE", "overline"),
        text("main()   •   function", "caption"),
    ], 8)


def _editor(state):
    if not state["editor"] or not state["tabs"]:
        return column([fill(text("Open a source file from Explorer", "subheading"))], 8)
    name = state["active"]
    source = SOURCES[name]
    tab_controls = [button("shell-file-" + tab, ("● " if tab == name else "") + tab,
                           "primary" if tab == name else "quiet") for tab in state["tabs"]]
    tab_controls.append(button("shell-close-tab", "×", "quiet"))
    # The rich editor renders the code itself. A narrow, noninteractive line-number
    # gutter is used until the public Rich Editor gutter contract is available.
    gutter = column([text(str(i), "caption") for i in range(1, source.count("\n") + 1)], 4)
    return column([
        row(tab_controls + [fill(text("", "caption"))], 4),
        separator("horizontal"),
        row([text("PYNIX", "caption"), text("/", "caption"),
             text("src", "caption"), text("/", "caption"), text(name, "caption"),
             fill(text("UTF-8", "caption"))], 7),
        fill(row([
            max_size(gutter, 35, 1500),
            fill(rich_editor("shell-editor", source, 0, 0,
                             source_spans(source), read_only=True)),
        ], 6)),
    ], 7)


def _bottom(state):
    tabs = []
    for name in ("Problems", "Output", "Terminal", "Debug Console"):
        slug = name.lower().replace(" ", "-")
        tabs.append(button("shell-tool-" + slug, name,
                           "primary" if state["tool_tab"] == name else "quiet"))
    return column([
        separator("horizontal"),
        row(tabs + [fill(text("", "caption")),
                    button("shell-toggle-bottom", "×", "quiet")], 5),
        fill(text(state["tool_message"], "body")),
    ], 6)


def build(state):
    top = toolbar(row([
        text("PYNIX", "titleSmall"),
        text("IDE", "label"),
        fill(text("PYNIX  /  Visual workspace", "caption")),
        button("shell-project", "Open Project", "quiet"),
        button("shell-toggle-inspector", "Inspector", "quiet"),
        button("shell-run", "▶ Run", "primary"),
    ], 8))
    rail = _activity_rail(state)
    center = _editor(state)
    if state["bottom"]:
        center = column([fill(center),
                         max_size(min_size(_bottom(state), 0, 138), 1800, 175)], 4)
    if state["sidebar"]:
        workspace = row([
            rail,
            max_size(min_size(_sidebar(state), 215, 0), 300, 1800),
            fill(center),
        ], 6)
    else:
        workspace = row([rail, fill(center)], 6)
    if state["inspector"]:
        inspector = column([
            text("INSPECTOR", "overline"),
            separator("horizontal"),
            text("Properties", "subheading"),
            text("File: " + state["active"], "caption"),
            text("Language: PYNIX", "caption"),
            text("Encoding: UTF-8", "caption"),
            fill(text("Preview metadata", "caption")),
        ], 8)
        workspace = row([fill(workspace),
                         max_size(min_size(inspector, 195, 0), 260, 1500)], 8)
    status = status_bar(row([
        text("●  " + state["message"], "caption"),
        fill(text("PYNIX  ·  " + state["active"], "caption")),
        text("UTF-8   ·   Spaces: 4   ·   Ln 1, Col 1", "caption"),
    ], 9))
    return column([
        top,
        padding(row([
            button("shell-toggle-sidebar", "☰", "quiet"),
            text("PROJECT", "overline"),
            fill(text("PYNIX / " + state["active"], "caption")),
            button("shell-tab", "Open Editor", "quiet"),
        ], 8), 8),
        fill(padding(workspace, 8)),
        status,
    ], 3)


def dispatch(state, event):
    if event.kind == "CLOSE":
        return False
    target = event.target or ""
    if event.kind == "CHANGE" and target == "shell-search":
        state["search"] = event.text or ""
    elif event.kind == "EXPANSION" and target == "shell-tree":
        expanded = set(state["expanded"])
        if event.checked:
            expanded.add(event.item_id)
        else:
            expanded.discard(event.item_id)
        state["expanded"] = sorted(expanded)
    elif event.kind in ("SELECTION", "OPEN") and target == "shell-tree":
        state["selected"] = event.item_id
        if event.item_id in SOURCES:
            _open_file(state, event.item_id)
    elif event.kind == "ACTIVATE":
        if target in ("shell-toggle-sidebar", "shell-activity-explorer"):
            state["sidebar"] = not state["sidebar"] if target == "shell-toggle-sidebar" else True
            state["activity"] = "Explorer"
        elif target == "shell-activity-search":
            state["activity"], state["sidebar"] = "Search", True
        elif target == "shell-toggle-inspector":
            state["inspector"] = not state["inspector"]
        elif target in ("shell-toggle-bottom", "shell-menu-bottom"):
            state["bottom"] = not state["bottom"]
        elif target.startswith("shell-tool-"):
            name = target[len("shell-tool-"):].replace("-", " ").title()
            state["bottom"], state["tool_tab"] = True, name
            state["tool_message"] = {
                "Problems": "No problems detected",
                "Output": "Build output will appear here",
                "Terminal": "pynix$  Ready — visual preview",
                "Debug Console": "Debugger is not connected in the visual preview",
            }[name]
        elif target.startswith("shell-file-"):
            _open_file(state, target[len("shell-file-"):])
        elif target == "shell-close-tab" and state["tabs"]:
            state["tabs"].remove(state["active"])
            state["editor"] = bool(state["tabs"])
            if state["tabs"]:
                state["active"] = state["tabs"][-1]
                state["source"] = SOURCES[state["active"]]
        elif target in ("shell-tab", "shell-menu-editor"):
            _open_file(state, state["active"])
        elif target in ("shell-run", "shell-activity-run", "shell-menu-run"):
            state["bottom"], state["tool_tab"] = True, "Output"
            state["tool_message"] = "Visual shell only — no code executed"
        elif target in ("shell-project", "shell-menu-project"):
            state["sidebar"], state["activity"] = True, "Explorer"
        elif target == "shell-activity-settings":
            state["inspector"] = True
    return True


def _open_file(state, name):
    if name not in SOURCES:
        return
    if name not in state["tabs"]:
        state["tabs"].append(name)
    state["active"], state["selected"], state["editor"] = name, name, True
    state["source"] = SOURCES[name]


def shell_menus():
    return menu_bar([
        menu("File", [menu_item("shell-menu-project", "Project"),
                       menu_item("shell-menu-editor", "Open Editor")]),
        menu("View", [menu_item("shell-toggle-sidebar", "Toggle Explorer"),
                       menu_item("shell-menu-bottom", "Toggle Bottom Panel"),
                       menu_item("shell-toggle-inspector", "Toggle Inspector")]),
        menu("Run", [menu_item("shell-menu-run", "Run Current File")]),
    ])


def main():
    backend = default_backend()
    if backend is None:
        raise SystemExit("No GUI backend available")
    runtime = GUIRuntime(backend)
    if not runtime.is_available():
        raise SystemExit("GUI backend unavailable")
    state = initial_state()
    window = runtime.open("PYNIX IDE — Complete Visual Shell Preview", 1440, 900)
    try:
        window.set_menu_bar(shell_menus())
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

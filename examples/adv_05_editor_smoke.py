# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Native macOS smoke for GUI-ADV-05 Rich Editor."""

from pynix_gui import (
    GUIRuntime,
    column,
    rich_editor,
    text,
    text_span,
    theme,
)
from pynix_gui.backends import MacOSGUIBackend


INITIAL = """fn main() {
    let answer = 42
    print("PYNIX GUI")
}
"""


def make_spans(value):
    result = []
    for token, role in (
        ("fn", "keyword"),
        ("main", "function"),
        ("let", "keyword"),
        ("42", "number"),
        ('"PYNIX GUI"', "string"),
    ):
        start = value.find(token)
        if start >= 0:
            result.append(text_span(start, start + len(token), role))
    return result


def build(value, start, end):
    return theme(
        column([
            text("ADV-05 Rich Editor", "title"),
            text(
                "Edit text, move the caret, select ranges and use native keyboard navigation.",
                "body",
            ),
            rich_editor(
                "source-editor",
                value,
                start,
                end,
                make_spans(value),
            ),
        ], 16),
        "system",
    )


def main():
    runtime = GUIRuntime(MacOSGUIBackend())
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI macOS backend is unavailable.")

    window = runtime.open("PYNIX GUI — ADV-05 Rich Editor", 1000, 720)

    value = INITIAL
    selection_start = 0
    selection_end = 0
    window.render(build(value, selection_start, selection_end))

    while True:
        event = window.next_event()
        print("event:", event)

        if event.kind == "CLOSE":
            break

        if event.kind == "CHANGE" and event.target == "source-editor":
            value = event.text
            selection_start = min(selection_start, len(value))
            selection_end = min(selection_end, len(value))
            window.render(build(value, selection_start, selection_end))
            continue

        if (
            event.kind == "EDITOR_SELECTION"
            and event.target == "source-editor"
        ):
            selection_start = event.selection_start
            selection_end = event.selection_end
            # Selection-only events are observed without rerender to avoid
            # fighting native caret motion. The next controlled render restores it.

    window.close()
    print("PYNIX GUI ADV-05 macOS smoke: PASS")


if __name__ == "__main__":
    main()

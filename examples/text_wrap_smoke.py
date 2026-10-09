# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Interactive V4 macOS reflow check.

Run `python examples/text_wrap_smoke.py`, then resize the window
horizontally while watching both the row and the grid.
"""

from pynix_gui import GUIRuntime, column, grid, panel, row, text
from pynix_gui.backends import MacOSGUIBackend


def build_root():
    return panel(column([
        text("V4 · Height-for-Width", "title"),
        text(
            "Resize this window horizontally. Wrapped labels must grow "
            "vertically without overlapping the following rows.",
            "body", overflow="wrap",
        ),
        row([
            text(
                "This long label uses real AppKit font measurements and "
                "should occupy several lines when the window becomes narrow.",
                "body", overflow="wrap",
            ),
            text("ROW END", "caption"),
        ], 12),
        text("The second row must remain below the entire wrapped row.",
             "bodyStrong"),
        grid(2, [
            text(
                "First grid cell: long words and punctuation should "
                "stay in their own allocated row.",
                "body", overflow="wrap",
            ),
            text("Short right-hand cell", "body"),
            text("Second grid row begins here.", "body"),
            text(
                "Unicode check: українська мова, e\u0301, "
                "emoji \U0001f469\u200d\U0001f4bb must render without overlap.",
                "body", overflow="wrap",
            ),
        ], 12, 14),
        text("BOTTOM MARKER — should never overlap content above.", "caption"),
    ], 16), "workspace")


def main():
    runtime = GUIRuntime(MacOSGUIBackend())
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI macOS backend unavailable")
    window = runtime.open("PYNIX GUI · Text Wrap V4", 780, 680)
    window.render(build_root())
    while True:
        event = window.next_event()
        if event.kind == "CLOSE":
            break
    window.close()
    print("PYNIX GUI V4 native wrap smoke: PASS")


if __name__ == "__main__":
    main()

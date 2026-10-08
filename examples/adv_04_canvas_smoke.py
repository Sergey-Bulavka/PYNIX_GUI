# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Native macOS smoke for GUI-ADV-04 Canvas 2D."""

from pynix_gui import (
    GUIRuntime,
    canvas,
    canvas_clip,
    canvas_ellipse,
    canvas_line,
    canvas_path,
    canvas_rect,
    canvas_scene,
    canvas_text,
    canvas_transform,
    column,
    text,
    theme,
)
from pynix_gui.backends import MacOSGUIBackend


def make_scene():
    return canvas_scene(
        900,
        500,
        [
            canvas_rect(20, 20, 860, 460, stroke="borderStrong", fill="surface"),
            canvas_text(50, 60, "PYNIX retained Canvas 2D", role="titleLarge"),
            canvas_line(50, 105, 850, 105, stroke="separator"),
            canvas_rect(
                70,
                150,
                220,
                120,
                fill="surfaceSelected",
                stroke="accent",
                line_width=2,
                hit_target="canvas-card",
            ),
            canvas_text(100, 200, "Click this card", role="titleSmall"),
            canvas_ellipse(
                360,
                155,
                120,
                120,
                fill="accentMuted",
                stroke="accent",
                hit_target="canvas-circle",
            ),
            canvas_path(
                [(560, 250), (650, 145), (740, 250)],
                closed=True,
                fill="warning",
                stroke="borderStrong",
                hit_target="canvas-triangle",
            ),
            canvas_clip(
                70,
                320,
                260,
                100,
                [
                    canvas_transform(
                        [
                            canvas_rect(0, 0, 90, 90, fill="success"),
                            canvas_text(12, 32, "clip", role="bodyStrong"),
                        ],
                        translate_x=170,
                        rotate=8,
                    ),
                ],
            ),
        ],
    )


def main():
    runtime = GUIRuntime(MacOSGUIBackend())
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI macOS backend is unavailable.")

    window = runtime.open("PYNIX GUI — ADV-04 Canvas 2D", 1000, 680)
    root = theme(
        column([
            text("ADV-04 Canvas 2D", "title"),
            text("Click the card, circle and triangle.", "body"),
            canvas("main-canvas", make_scene()),
        ], 16),
        "system",
    )
    window.render(root)

    while True:
        event = window.next_event()
        print("event:", event)
        if event.kind == "CLOSE":
            break
        if event.kind == "ACTIVATE":
            print("canvas hit:", event.target)

    window.close()
    print("PYNIX GUI ADV-04 macOS smoke: PASS")


if __name__ == "__main__":
    main()

# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Native resource/vector acceptance smoke."""

from pynix_gui import (
    GUIRuntime,
    canvas_rect,
    canvas_scene,
    column,
    resource_catalog,
    text,
    theme,
    vector_icon,
    vector_resource,
)
from pynix_gui.backends import default_backend


def main():
    backend = default_backend()
    if backend is None:
        raise SystemExit("No native PYNIX GUI backend is available.")

    runtime = GUIRuntime(backend)
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI backend is unavailable.")

    icon_scene = canvas_scene(
        24,
        24,
        [
            canvas_rect(
                3,
                3,
                18,
                18,
                stroke="accent",
                fill="accentMuted",
                line_width=2,
            )
        ],
    )
    catalog = resource_catalog([
        vector_resource("showcase.vector", icon_scene),
    ])

    window = runtime.open("PYNIX GUI — Resources", 520, 320)
    window.set_resources(catalog)
    window.render(
        theme(
            column([
                text("Logical vector resource", "title"),
                text("The square below is resolved by resource name.", "body"),
                vector_icon("showcase.vector", 96),
            ], 16),
            "system",
        )
    )

    while True:
        event = window.next_event()
        print("event:", event)
        if event.kind == "CLOSE":
            break

    window.close()
    print("PYNIX GUI resource smoke: PASS")


if __name__ == "__main__":
    main()

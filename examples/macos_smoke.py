# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Real-host standalone macOS smoke for PYNIX GUI.

Run from the PYNIX_GUI repository:

    python examples/macos_smoke.py
"""

from pynix_gui import (
    GUIRuntime,
    button,
    column,
    enabled,
    focused,
    panel,
    row,
    text,
    text_field,
    theme,
)
from pynix_gui.backends import MacOSGUIBackend


def build_root():
    content = column(
        [
            text("PYNIX GUI", "titleLarge"),
            text("Standalone macOS backend smoke", "body"),
            focused(text_field("name", "PYNIX", "Project name"), True),
            row(
                [
                    button("primary", "Primary", "primary"),
                    button("secondary", "Secondary", "secondary"),
                    button("danger", "Danger", "danger"),
                ],
                8,
            ),
            enabled(button("disabled", "Disabled", "secondary"), False),
        ],
        12,
    )
    return theme(panel(content, "workspace"), "system")


def main():
    runtime = GUIRuntime(MacOSGUIBackend())

    if not runtime.is_available():
        raise SystemExit("PYNIX GUI macOS backend is unavailable on this host.")

    window = runtime.open("PYNIX GUI — Standalone Smoke", 720, 420)
    window.render(build_root())

    while True:
        event = window.next_event()
        print(
            "event:",
            event.kind,
            event.target,
            event.text,
            event.index,
            event.number,
            event.checked,
        )

        if event.kind == "CLOSE":
            break

    window.close()
    print("PYNIX GUI standalone macOS smoke: PASS")


if __name__ == "__main__":
    main()

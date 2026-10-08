# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Standalone ADV-01 native macOS smoke.

Run:

    python examples/adv_01_commands_smoke.py
"""

from pynix_gui import (
    GUIRuntime,
    button,
    collapsible,
    column,
    context_menu,
    dialog,
    dialog_action,
    group,
    menu,
    menu_bar,
    menu_item,
    menu_separator,
    panel,
    row,
    shortcut,
    text,
    theme,
    tooltip,
)
from pynix_gui.backends import MacOSGUIBackend


def app_menu_bar():
    return menu_bar([
        menu("File", [
            menu_item(
                "new",
                "New",
                shortcut("n", ["primary"]),
            ),
            menu_item(
                "open-dialog",
                "Show Dialog…",
                shortcut("d", ["primary"]),
            ),
            menu_separator(),
            menu_item(
                "quit",
                "Close Window",
                shortcut("w", ["primary"]),
            ),
        ]),
        menu("View", [
            menu_item(
                "toggle-details",
                "Expanded Details",
                checked=True,
            ),
        ]),
    ])


def build_root(expanded):
    actions = group(
        column([
            text("ADV-01 Commands & Transients", "title"),
            text(
                "Native menu bar, context menu, tooltip, disclosure and dialog.",
                "body",
            ),
            row([
                tooltip(
                    button("open-dialog", "Show Dialog", "primary"),
                    "Open a native modal dialog",
                ),
                button("toggle-details", "Toggle Details", "secondary"),
            ], 8),
        ], 12),
        "section",
    )

    context = menu("Context", [
        menu_item("context-copy", "Context Action"),
        menu_item("open-dialog", "Show Dialog"),
    ])

    details = collapsible(
        "details",
        "Advanced details",
        expanded,
        context_menu(
            panel(
                column([
                    text("Context-menu area", "bodyStrong"),
                    text(
                        "Right-click this panel to inspect native context commands.",
                        "body",
                    ),
                ], 8),
                "workspace",
            ),
            context,
        ),
    )

    return theme(
        panel(
            column([
                actions,
                details,
            ], 16),
            "workspace",
        ),
        "system",
    )


def main():
    runtime = GUIRuntime(MacOSGUIBackend())
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI macOS backend is unavailable.")

    window = runtime.open("PYNIX GUI — ADV-01 Smoke", 760, 520)
    window.set_menu_bar(app_menu_bar())

    expanded = True
    window.render(build_root(expanded))

    while True:
        event = window.next_event()
        print("event:", event)

        if event.kind == "CLOSE":
            break

        if event.kind == "CHANGE" and event.target == "details":
            expanded = bool(event.checked)
            window.render(build_root(expanded))
            continue

        if event.kind != "ACTIVATE":
            continue

        if event.target == "quit":
            break

        if event.target == "toggle-details":
            expanded = not expanded
            window.render(build_root(expanded))
            continue

        if event.target == "open-dialog":
            window.present_dialog(
                dialog(
                    "sample-dialog",
                    "PYNIX GUI Dialog",
                    column([
                        text("Native modal dialog", "titleSmall"),
                        text(
                            "The dialog body is ordinary GUIView content.",
                            "body",
                        ),
                    ], 12),
                    [
                        dialog_action(
                            "dialog-cancel",
                            "Cancel",
                            "secondary",
                        ),
                        dialog_action(
                            "dialog-ok",
                            "Continue",
                            "primary",
                            default=True,
                        ),
                    ],
                )
            )
            continue

        if event.target in {"dialog-ok", "dialog-cancel"}:
            print("dialog result:", event.target)

    window.close()
    print("PYNIX GUI ADV-01 macOS smoke: PASS")


if __name__ == "__main__":
    main()

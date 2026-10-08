# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Native macOS smoke for GUI-ADV-03 Drag/Drop and Docking."""

from pynix_gui import (
    GUIRuntime,
    column,
    dock_panel,
    dock_placement,
    dock_state,
    dock_target,
    dock_workspace,
    drag_payload,
    draggable,
    group,
    row,
    text,
    theme,
)
from pynix_gui.backends import MacOSGUIBackend


PANELS = [
    dock_panel("project", "Project", group(text("Project files", "body"), "section")),
    dock_panel("inspector", "Inspector", group(text("Inspector", "body"), "section")),
    dock_panel("output", "Output", group(text("Build output", "body"), "section")),
    dock_panel("editor", "Editor", group(text("Editor workspace", "body"), "section"), closable=False),
]


def make_state(regions):
    placements = [
        dock_placement(panel.panel_id, regions[panel.panel_id])
        for panel in PANELS
    ]

    active = {"left": None, "right": None, "bottom": None, "center": None}
    for panel_id, region in regions.items():
        active[region] = panel_id

    return dock_state(
        placements,
        active_left=active["left"],
        active_right=active["right"],
        active_bottom=active["bottom"],
        active_center=active["center"],
        left_width=220,
        right_width=240,
        bottom_height=180,
    )


def drag_handle(panel_id, label):
    return draggable(
        group(text(label, "bodyStrong"), "section"),
        f"drag-{panel_id}",
        drag_payload("pynix/dock-panel", panel_id, ["move"]),
    )


def zone(workspace, region):
    return dock_target(
        group(text(f"Drop to {region}", "caption"), "section"),
        workspace,
        region,
    )


def build(regions):
    state = make_state(regions)
    workspace = dock_workspace("main-workspace", PANELS, state)

    return theme(
        column([
            text("ADV-03 Drag & Dock", "title"),
            text(
                "Drag a panel handle onto a dock zone. The app rebuilds GUIDockState.",
                "body",
            ),
            row([
                drag_handle("project", "Drag Project"),
                drag_handle("inspector", "Drag Inspector"),
                drag_handle("output", "Drag Output"),
            ], 8),
            row([
                zone("main-workspace", "left"),
                zone("main-workspace", "right"),
                zone("main-workspace", "bottom"),
                zone("main-workspace", "center"),
            ], 8),
            workspace,
        ], 14),
        "system",
    )


def main():
    runtime = GUIRuntime(MacOSGUIBackend())
    if not runtime.is_available():
        raise SystemExit("PYNIX GUI macOS backend is unavailable.")

    window = runtime.open("PYNIX GUI — ADV-03 Drag & Dock", 1100, 760)

    regions = {
        "project": "left",
        "inspector": "right",
        "output": "bottom",
        "editor": "center",
    }
    window.render(build(regions))

    while True:
        event = window.next_event()
        print("event:", event)

        if event.kind == "CLOSE":
            break

        if event.kind == "DOCK" and event.target == "main-workspace":
            panel_id = event.item_id
            destination = event.region

            # Keep one visible active panel per region in this smoke.
            displaced = next(
                (
                    current
                    for current, region in regions.items()
                    if region == destination and current != panel_id
                ),
                None,
            )
            old_region = regions[panel_id]
            regions[panel_id] = destination
            if displaced is not None:
                regions[displaced] = old_region

            window.render(build(regions))

    window.close()
    print("PYNIX GUI ADV-03 macOS smoke: PASS")


if __name__ == "__main__":
    main()

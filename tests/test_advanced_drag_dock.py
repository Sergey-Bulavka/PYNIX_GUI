# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import pytest

from pynix_gui import (
    GUIError,
    GUIEvent,
    column,
    dock_panel,
    dock_placement,
    dock_state,
    dock_target,
    dock_workspace,
    drag_payload,
    draggable,
    drop_target,
    group,
    min_size,
    text,
    validate_view,
)
from pynix_gui.backends import MacOSGUIBackend
from pynix_gui.layout import layout, measure


def panels():
    return [
        dock_panel(
            "project",
            "Project",
            group(text("Project", "body"), "section"),
        ),
        dock_panel(
            "inspector",
            "Inspector",
            group(text("Inspector", "body"), "section"),
        ),
        dock_panel(
            "output",
            "Output",
            group(text("Output", "body"), "section"),
        ),
        dock_panel(
            "editor",
            "Editor",
            group(text("Editor", "body"), "section"),
            closable=False,
        ),
    ]


def state():
    return dock_state(
        [
            dock_placement("project", "left"),
            dock_placement("inspector", "right"),
            dock_placement("output", "bottom"),
            dock_placement("editor", "center"),
        ],
        active_left="project",
        active_right="inspector",
        active_bottom="output",
        active_center="editor",
        left_width=220,
        right_width=260,
        bottom_height=180,
    )


def test_adv03_drag_payload_is_logical_and_operation_limited():
    payload = drag_payload("file", "src/main.pnx", ["copy", "move"])

    assert payload.kind == "file"
    assert payload.value == "src/main.pnx"
    assert payload.operations == ("copy", "move")

    with pytest.raises(GUIError) as failure:
        drag_payload("file", "src/main.pnx", ["link"])
    assert failure.value.code == "PYNIX-GUI-010"


def test_adv03_drag_and_drop_wrappers_are_geometry_neutral():
    content = text("Drag me", "body")
    source = draggable(
        content,
        "source",
        drag_payload("file", "main.pnx"),
    )
    target = drop_target(
        content,
        "destination",
        ["file"],
        ["move"],
    )

    assert measure(source) == measure(content)
    assert measure(target) == measure(content)
    validate_view(source)
    validate_view(target)


def test_adv03_drop_event_contains_only_logical_payload():
    event = GUIEvent(
        "DROP",
        target="destination",
        source_id="source",
        payload_kind="file",
        payload_value="main.pnx",
        operation="move",
    )

    assert event.target == "destination"
    assert event.payload_value == "main.pnx"

    with pytest.raises(GUIError):
        GUIEvent(
            "DROP",
            target="destination",
            source_id="source",
            payload_kind="file",
            payload_value="main.pnx",
            operation="link",
        )


def test_adv03_dock_state_requires_every_panel_once():
    all_panels = panels()

    with pytest.raises(GUIError) as failure:
        dock_workspace(
            "workspace",
            all_panels,
            dock_state(
                [
                    dock_placement("project", "left"),
                    dock_placement("inspector", "right"),
                ],
                active_left="project",
                active_right="inspector",
            ),
        )

    assert failure.value.code == "PYNIX-GUI-010"


def test_adv03_dock_state_rejects_active_panel_in_wrong_region():
    with pytest.raises(GUIError):
        dock_state(
            [
                dock_placement("project", "left"),
            ],
            active_right="project",
        )


def test_adv03_workspace_layout_is_deterministic_by_region():
    view = dock_workspace("workspace", panels(), state())
    measured = measure(view)

    assert measured.preferred.width >= 220 + 260
    assert measured.preferred.height >= 180

    calculated = layout(view, 1000, 700)
    assert len(calculated.children) == 4

    left, right, bottom, center = calculated.children
    assert left.rect.width == 220
    assert right.rect.width == 260
    assert bottom.rect.height == 180
    assert center.rect.width == 520
    assert center.rect.height == 520


def test_adv03_dock_target_is_geometry_neutral_and_typed():
    content = text("Right", "body")
    target = dock_target(content, "workspace", "right")

    assert measure(target) == measure(content)
    assert target.accepted_kinds == ("pynix/dock-panel",)
    assert target.accepted_operations == ("move",)
    assert target.dock_region == "right"
    validate_view(target)


def test_adv03_dock_event_carries_panel_identity_and_region():
    event = GUIEvent(
        "DOCK",
        target="workspace",
        item_id="project",
        region="right",
    )

    assert event.item_id == "project"
    assert event.region == "right"


class FakePasteboard:
    def __init__(self, raw):
        self.raw = raw

    def stringForType_(self, value):
        return self.raw


class FakeDragInfo:
    def __init__(self, raw):
        self.raw = raw

    def draggingPasteboard(self):
        return FakePasteboard(self.raw)


def test_adv03_backend_normalizes_generic_drop_event():
    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    window = object()
    target = SimpleNamespace(
        _pynix_target_id="destination",
        _pynix_accepted_kinds=("file",),
        _pynix_accepted_operations=("move",),
        _pynix_dock_region=None,
    )
    info = FakeDragInfo(
        '{"source_id":"source","kind":"file","value":"main.pnx","operations":["move"]}'
    )

    assert backend._queue_drop_from_info(window, target, info) is True
    assert backend._event_queue(window).popleft() == GUIEvent(
        "DROP",
        target="destination",
        source_id="source",
        payload_kind="file",
        payload_value="main.pnx",
        operation="move",
    )


def test_adv03_backend_normalizes_dock_drop_into_dock_event():
    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    window = object()
    target = SimpleNamespace(
        _pynix_target_id="workspace",
        _pynix_accepted_kinds=("pynix/dock-panel",),
        _pynix_accepted_operations=("move",),
        _pynix_dock_region="bottom",
    )
    info = FakeDragInfo(
        '{"source_id":"dock-project","kind":"pynix/dock-panel","value":"project","operations":["move"]}'
    )

    assert backend._queue_drop_from_info(window, target, info) is True
    assert backend._event_queue(window).popleft() == GUIEvent(
        "DOCK",
        target="workspace",
        item_id="project",
        region="bottom",
    )


def test_adv03_backend_rejects_unaccepted_payload_kind():
    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    target = SimpleNamespace(
        _pynix_accepted_kinds=("image",),
        _pynix_accepted_operations=("copy",),
    )
    info = FakeDragInfo(
        '{"source_id":"source","kind":"file","value":"main.pnx","operations":["copy"]}'
    )

    assert backend._drop_operation_for_info(target, info) == 0


def test_adv03_workspace_can_be_nested_in_normal_gui_composition():
    workspace = dock_workspace("workspace", panels(), state())
    root = column([
        text("Workspace", "title"),
        workspace,
    ], 12)

    validate_view(root)



def test_adv03_dock_target_layout_is_geometry_neutral():
    content = text("Bottom", "body")
    target = dock_target(content, "workspace", "bottom")

    calculated = layout(target, 320, 80)

    assert calculated.rect.width == 320
    assert calculated.rect.height == 80
    assert len(calculated.children) == 1
    assert calculated.children[0].rect == calculated.rect



def test_adv03_dock_requested_sizes_are_clamped_to_panel_minimums():
    custom_panels = [
        dock_panel(
            "left",
            "Left",
            min_size(text("Left", "body"), 180, 120),
        ),
        dock_panel(
            "right",
            "Right",
            min_size(text("Right", "body"), 300, 140),
        ),
        dock_panel(
            "bottom",
            "Bottom",
            min_size(text("Bottom", "body"), 200, 170),
        ),
        dock_panel(
            "center",
            "Center",
            min_size(text("Center", "body"), 260, 220),
        ),
    ]
    custom_state = dock_state(
        [
            dock_placement("left", "left"),
            dock_placement("right", "right"),
            dock_placement("bottom", "bottom"),
            dock_placement("center", "center"),
        ],
        active_left="left",
        active_right="right",
        active_bottom="bottom",
        active_center="center",
        left_width=80,
        right_width=90,
        bottom_height=60,
    )

    view = dock_workspace("workspace", custom_panels, custom_state)
    calculated = layout(view, 1000, 700)

    left, right, bottom, center = calculated.children
    assert left.rect.width >= 180
    assert right.rect.width >= 300
    assert bottom.rect.height >= 170
    assert center.rect.width >= 260
    assert center.rect.height >= 220


def test_adv03_dock_requested_sizes_shrink_surplus_without_breaking_minimums():
    custom_panels = [
        dock_panel(
            "left",
            "Left",
            min_size(text("Left", "body"), 180, 120),
        ),
        dock_panel(
            "right",
            "Right",
            min_size(text("Right", "body"), 220, 120),
        ),
        dock_panel(
            "center",
            "Center",
            min_size(text("Center", "body"), 300, 200),
        ),
    ]
    custom_state = dock_state(
        [
            dock_placement("left", "left"),
            dock_placement("right", "right"),
            dock_placement("center", "center"),
        ],
        active_left="left",
        active_right="right",
        active_center="center",
        left_width=500,
        right_width=500,
    )

    view = dock_workspace("workspace", custom_panels, custom_state)
    calculated = layout(view, 800, 500)

    left, right, center = calculated.children
    assert left.rect.width >= 180
    assert right.rect.width >= 220
    assert center.rect.width >= 300
    assert left.rect.width + right.rect.width + center.rect.width == pytest.approx(800)

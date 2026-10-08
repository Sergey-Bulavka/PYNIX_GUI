# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Platform-independent drag/drop and docking values."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from .core import GUIError, GUIView


_DRAG_OPERATIONS = {"copy", "move"}
_DOCK_REGIONS = {"left", "right", "bottom", "center"}


def _non_empty(value, label: str) -> str:
    if type(value) is not str or value == "":
        raise GUIError("PYNIX-GUI-010", f"{label} must be a non-empty String.")
    return value


def _sequence(value, label: str) -> tuple:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise GUIError("PYNIX-GUI-010", f"{label} must be a sequence.")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class GUIDragPayload:
    kind: str
    value: str
    operations: tuple[str, ...] = ("move",)

    def __post_init__(self):
        _non_empty(self.kind, "GUI drag payload kind")
        _non_empty(self.value, "GUI drag payload value")
        if type(self.operations) is not tuple or not self.operations:
            raise GUIError("PYNIX-GUI-010", "GUI drag operations must be a non-empty tuple.")
        if len(set(self.operations)) != len(self.operations):
            raise GUIError("PYNIX-GUI-010", "GUI drag operations must be unique.")
        if any(operation not in _DRAG_OPERATIONS for operation in self.operations):
            raise GUIError("PYNIX-GUI-010", "GUI drag operation is invalid.")


@dataclass(frozen=True, slots=True)
class GUIDockPanel:
    panel_id: str
    title: str
    content: GUIView
    closable: bool = True

    def __post_init__(self):
        _non_empty(self.panel_id, "GUI dock panel id")
        if type(self.title) is not str:
            raise GUIError("PYNIX-GUI-010", "GUI dock panel title must be String.")
        if not isinstance(self.content, GUIView):
            raise GUIError("PYNIX-GUI-010", "GUI dock panel content must be GUIView.")
        if type(self.closable) is not bool:
            raise GUIError("PYNIX-GUI-010", "GUI dock panel closable must be Bool.")


@dataclass(frozen=True, slots=True)
class GUIDockPlacement:
    panel_id: str
    region: str
    order: int = 0

    def __post_init__(self):
        _non_empty(self.panel_id, "GUI dock placement panel id")
        if self.region not in _DOCK_REGIONS:
            raise GUIError("PYNIX-GUI-010", "GUI dock region is invalid.")
        if type(self.order) is not int or self.order < 0:
            raise GUIError("PYNIX-GUI-010", "GUI dock order must be a non-negative Int.")


@dataclass(frozen=True, slots=True)
class GUIDockState:
    placements: tuple[GUIDockPlacement, ...]
    active_left: str | None = None
    active_right: str | None = None
    active_bottom: str | None = None
    active_center: str | None = None
    left_width: int = 240
    right_width: int = 280
    bottom_height: int = 220

    def __post_init__(self):
        if type(self.placements) is not tuple or any(
            not isinstance(item, GUIDockPlacement) for item in self.placements
        ):
            raise GUIError("PYNIX-GUI-010", "GUI dock placements are invalid.")

        ids = [item.panel_id for item in self.placements]
        if len(set(ids)) != len(ids):
            raise GUIError("PYNIX-GUI-010", "A dock panel may appear only once.")

        for name, value in (
            ("left width", self.left_width),
            ("right width", self.right_width),
            ("bottom height", self.bottom_height),
        ):
            if type(value) is not int or value < 0:
                raise GUIError("PYNIX-GUI-010", f"GUI dock {name} must be non-negative Int.")

        by_region = {
            region: {
                item.panel_id
                for item in self.placements
                if item.region == region
            }
            for region in _DOCK_REGIONS
        }
        active_values = {
            "left": self.active_left,
            "right": self.active_right,
            "bottom": self.active_bottom,
            "center": self.active_center,
        }
        for region, active in active_values.items():
            if active is not None:
                _non_empty(active, f"GUI dock active {region} panel id")
                if active not in by_region[region]:
                    raise GUIError(
                        "PYNIX-GUI-010",
                        f"GUI dock active {region} panel must belong to that region.",
                    )


def drag_payload(kind: str, value: str, operations=("move",)) -> GUIDragPayload:
    values = _sequence(operations, "GUI drag operations")
    return GUIDragPayload(kind, value, values)


def dock_panel(
    panel_id: str,
    title: str,
    content: GUIView,
    *,
    closable=True,
) -> GUIDockPanel:
    return GUIDockPanel(panel_id, title, content, closable)


def dock_placement(panel_id: str, region: str, order=0) -> GUIDockPlacement:
    return GUIDockPlacement(panel_id, region, order)


def dock_state(
    placements,
    *,
    active_left=None,
    active_right=None,
    active_bottom=None,
    active_center=None,
    left_width=240,
    right_width=280,
    bottom_height=220,
) -> GUIDockState:
    values = _sequence(placements, "GUI dock placements")
    return GUIDockState(
        values,
        active_left,
        active_right,
        active_bottom,
        active_center,
        left_width,
        right_width,
        bottom_height,
    )


def validate_dock_workspace(panels, state: GUIDockState):
    panel_values = _sequence(panels, "GUI dock panels")
    if not panel_values:
        raise GUIError("PYNIX-GUI-010", "GUI dock workspace requires at least one panel.")
    if any(not isinstance(panel, GUIDockPanel) for panel in panel_values):
        raise GUIError("PYNIX-GUI-010", "GUI dock panels are invalid.")
    if not isinstance(state, GUIDockState):
        raise GUIError("PYNIX-GUI-010", "GUI dock state is invalid.")

    panel_ids = [panel.panel_id for panel in panel_values]
    if len(set(panel_ids)) != len(panel_ids):
        raise GUIError("PYNIX-GUI-010", "GUI dock panel ids must be unique.")

    placement_ids = {item.panel_id for item in state.placements}
    if placement_ids != set(panel_ids):
        raise GUIError(
            "PYNIX-GUI-010",
            "GUI dock state must place every panel exactly once.",
        )

    return panel_values, state


def active_dock_panels(panels, state: GUIDockState):
    panel_by_id = {panel.panel_id: panel for panel in panels}
    result = {}
    active = {
        "left": state.active_left,
        "right": state.active_right,
        "bottom": state.active_bottom,
        "center": state.active_center,
    }
    for region, panel_id in active.items():
        result[region] = None if panel_id is None else panel_by_id[panel_id]
    return result

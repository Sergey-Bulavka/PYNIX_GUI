# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Platform-independent immutable GUI values, constructors, and validation."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence

from .design import ICON_METRICS, TEXT_ROLES, THEMES
from .layout import measure


class GUIError(Exception):
    """Controlled toolkit-level GUI contract error."""

    __slots__ = ("code", "message")

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class GUIView:
    kind: str
    children: tuple = ()
    spacing: int = 0
    horizontal: int | str | None = None
    vertical: int | str | None = None
    width: int | None = None
    height: int | None = None
    columns: int | None = None
    column_spacing: int = 0
    row_spacing: int = 0
    split_id: str | None = None
    split_position: int | None = None
    role: str | None = None
    orientation: str | None = None
    container_id: str | None = None
    labels: tuple = ()
    selected: int | None = None
    target: str | None = None
    text: str | None = None
    overflow: str = "natural"
    value: str | None = None
    placeholder: str | None = None
    items: tuple = ()
    number: float | None = None
    minimum_number: float | None = None
    maximum_number: float | None = None
    checked: bool | None = None
    enabled: bool | None = None
    focused: bool | None = None
    resource: str | None = None
    icon_size: int | None = None
    theme: str | None = None
    menu: object | None = None
    tooltip_text: str | None = None
    data: object | None = None
    expanded_ids: tuple[str, ...] = ()
    selected_id: str | None = None
    drag_payload: object | None = None
    drag_source_id: str | None = None
    drop_target_id: str | None = None
    accepted_kinds: tuple[str, ...] = ()
    accepted_operations: tuple[str, ...] = ()
    dock_state: object | None = None
    dock_region: str | None = None
    canvas_scene: object | None = None
    selection_start: int | None = None
    selection_end: int | None = None
    spans: tuple = ()
    read_only: bool | None = None


@dataclass(frozen=True, slots=True)
class GUIEvent:
    kind: str
    target: str | None = None
    text: str | None = None
    index: int | None = None
    number: float | None = None
    checked: bool | None = None
    item_id: str | None = None
    source_id: str | None = None
    payload_kind: str | None = None
    payload_value: str | None = None
    operation: str | None = None
    region: str | None = None
    selection_start: int | None = None
    selection_end: int | None = None
    width: float | None = None
    height: float | None = None

    def __post_init__(self):
        payload_count = sum(
            value is not None
            for value in (
                self.text,
                self.index,
                self.number,
                self.checked,
                self.item_id,
                self.source_id,
                self.payload_kind,
                self.payload_value,
                self.operation,
                self.region,
                self.selection_start,
                self.selection_end,
            )
        )

        valid = (
            (
                self.kind == "RESIZE"
                and self.target is None
                and payload_count == 0
                and type(self.width) is float
                and type(self.height) is float
                and math.isfinite(self.width)
                and math.isfinite(self.height)
                and self.width >= 0
                and self.height >= 0
            )
            or (self.kind == "CLOSE" and self.target is None and payload_count == 0)
            or (
                self.kind == "ACTIVATE"
                and _is_non_empty_string(self.target)
                and payload_count == 0
            )
            or (
                self.kind == "CHANGE"
                and _is_non_empty_string(self.target)
                and payload_count == 1
                and (
                    type(self.text) is str
                    or type(self.number) is float
                    or type(self.checked) is bool
                )
            )
            or (
                self.kind == "OPEN"
                and _is_non_empty_string(self.target)
                and _is_non_empty_string(self.item_id)
                and payload_count == 1
            )
            or (
                self.kind == "SELECTION"
                and _is_non_empty_string(self.target)
                and payload_count == 1
                and (
                    type(self.index) is int
                    or _is_non_empty_string(self.item_id)
                )
            )
            or (
                self.kind == "EXPANSION"
                and _is_non_empty_string(self.target)
                and _is_non_empty_string(self.item_id)
                and type(self.checked) is bool
                and self.text is None
                and self.index is None
                and self.number is None
                and self.source_id is None
                and self.payload_kind is None
                and self.payload_value is None
                and self.operation is None
                and self.region is None
                and payload_count == 2
            )
            or (
                self.kind == "DROP"
                and _is_non_empty_string(self.target)
                and _is_non_empty_string(self.source_id)
                and _is_non_empty_string(self.payload_kind)
                and _is_non_empty_string(self.payload_value)
                and self.operation in {"copy", "move"}
                and self.text is None
                and self.index is None
                and self.number is None
                and self.checked is None
                and self.item_id is None
                and self.region is None
                and payload_count == 4
            )
            or (
                self.kind == "DOCK"
                and _is_non_empty_string(self.target)
                and _is_non_empty_string(self.item_id)
                and self.region in {"left", "right", "bottom", "center"}
                and self.text is None
                and self.index is None
                and self.number is None
                and self.checked is None
                and self.source_id is None
                and self.payload_kind is None
                and self.payload_value is None
                and self.operation is None
                and payload_count == 2
            )
            or (
                self.kind == "EDITOR_SELECTION"
                and _is_non_empty_string(self.target)
                and type(self.selection_start) is int
                and type(self.selection_end) is int
                and 0 <= self.selection_start <= self.selection_end
                and self.text is None
                and self.index is None
                and self.number is None
                and self.checked is None
                and self.item_id is None
                and self.source_id is None
                and self.payload_kind is None
                and self.payload_value is None
                and self.operation is None
                and self.region is None
                and payload_count == 2
            )
        )

        if self.kind != "RESIZE" and (self.width is not None or self.height is not None):
            valid = False

        if not valid:
            raise GUIError(
                "PYNIX-GUI-006",
                "GUI backend produced an invalid control event.",
            )


_PANEL_ROLES = {
    "panel", "sidebar", "workspace", "toolPanel", "dialog",
    "card", "hero", "navigation", "overlay",
    "mutedSurface", "successSurface", "warningSurface",
    "dangerSurface", "infoSurface", "accentSurface",
}
_GROUP_ROLES = {
    "group", "settings", "section", "card", "mutedSurface",
    "successSurface", "warningSurface", "dangerSurface",
    "infoSurface", "accentSurface",
}
_TEXT_ROLES = set(TEXT_ROLES)
_BUTTON_ROLES = {"primary", "secondary", "quiet", "danger"}
_FOCUSABLE_KINDS = {
    "button",
    "textField",
    "textArea",
    "checkBox",
    "radioButton",
    "comboBox",
    "slider",
    "list",
    "tree",
    "table",
    "collapsible",
    "richEditor",
}


def _is_non_empty_string(value) -> bool:
    return type(value) is str and value != ""


def _children(value, label="GUI layout children") -> tuple:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise GUIError("PYNIX-GUI-005", f"{label} must be a GUIView sequence.")
    result = tuple(value)
    if any(not isinstance(item, GUIView) for item in result):
        raise GUIError("PYNIX-GUI-005", f"{label} must contain only GUIView values.")
    return result


def _strings(value, label: str) -> tuple:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise GUIError("PYNIX-GUI-005", f"{label} must be a String sequence.")
    result = tuple(value)
    if any(type(item) is not str for item in result):
        raise GUIError("PYNIX-GUI-005", f"{label} must contain only String values.")
    return result


def _non_negative(value, label: str) -> int:
    if type(value) is not int or value < 0:
        raise GUIError("PYNIX-GUI-005", f"{label} must be a non-negative Int.")
    return value


def _target(value, label="GUI control target") -> str:
    if not _is_non_empty_string(value):
        raise GUIError("PYNIX-GUI-006", f"{label} must be a non-empty String.")
    return value


def _number(value, label: str) -> float:
    if type(value) not in {int, float}:
        raise GUIError("PYNIX-GUI-006", f"{label} must be numeric.")
    return float(value)


def empty() -> GUIView:
    return GUIView("empty")


def row(children, spacing=8) -> GUIView:
    return GUIView(
        "row",
        children=_children(children),
        spacing=_non_negative(spacing, "GUI row spacing"),
    )


def column(children, spacing=8) -> GUIView:
    return GUIView(
        "column",
        children=_children(children),
        spacing=_non_negative(spacing, "GUI column spacing"),
    )


def fill(view: GUIView) -> GUIView:
    return GUIView("fill", children=(view,))


def spacer() -> GUIView:
    return GUIView("spacer")


def padding(view: GUIView, *args) -> GUIView:
    if len(args) == 1:
        horizontal = vertical = _non_negative(args[0], "GUI padding")
    elif len(args) == 2:
        horizontal = _non_negative(args[0], "GUI horizontal padding")
        vertical = _non_negative(args[1], "GUI vertical padding")
    else:
        raise GUIError(
            "PYNIX-GUI-005",
            "GUI.padding requires all or horizontal/vertical padding.",
        )
    return GUIView(
        "padding",
        children=(view,),
        horizontal=horizontal,
        vertical=vertical,
    )


def _size_wrapper(kind: str, view: GUIView, width: int, height: int) -> GUIView:
    return GUIView(
        kind,
        children=(view,),
        width=_non_negative(width, f"GUI {kind} width"),
        height=_non_negative(height, f"GUI {kind} height"),
    )


def min_size(view: GUIView, width: int, height: int) -> GUIView:
    return _size_wrapper("minSize", view, width, height)


def preferred_size(view: GUIView, width: int, height: int) -> GUIView:
    return _size_wrapper("preferredSize", view, width, height)


def max_size(view: GUIView, width: int, height: int) -> GUIView:
    return _size_wrapper("maxSize", view, width, height)


def align(view: GUIView, horizontal: str, vertical: str) -> GUIView:
    roles = {"start", "center", "end", "stretch"}
    if horizontal not in roles or vertical not in roles:
        raise GUIError(
            "PYNIX-GUI-005",
            "GUI alignment must be start, center, end, or stretch.",
        )
    return GUIView(
        "align",
        children=(view,),
        horizontal=horizontal,
        vertical=vertical,
    )


def stack(children) -> GUIView:
    return GUIView("stack", children=_children(children))


def grid(columns: int, children, *args) -> GUIView:
    if type(columns) is not int or columns <= 0:
        raise GUIError("PYNIX-GUI-005", "GUI grid columns must be a positive Int.")

    if len(args) == 0:
        column_spacing = row_spacing = 8
    elif len(args) == 2:
        column_spacing = _non_negative(args[0], "GUI grid column spacing")
        row_spacing = _non_negative(args[1], "GUI grid row spacing")
    else:
        raise GUIError(
            "PYNIX-GUI-005",
            "GUI.grid requires columns/children or columns/children/columnSpacing/rowSpacing.",
        )

    return GUIView(
        "grid",
        children=_children(children),
        columns=columns,
        column_spacing=column_spacing,
        row_spacing=row_spacing,
    )


def _split(kind: str, *args) -> GUIView:
    if len(args) == 2:
        first, second = args
        return GUIView(kind, children=(first, second))

    if len(args) == 4:
        split_id, first, second, initial_position = args
        if not _is_non_empty_string(split_id):
            raise GUIError(
                "PYNIX-GUI-005",
                "Controlled GUI split id must be a non-empty String.",
            )
        if type(initial_position) is not int or initial_position <= 0:
            raise GUIError(
                "PYNIX-GUI-005",
                "Controlled GUI split initial position must be a positive Int.",
            )
        return GUIView(
            kind,
            children=(first, second),
            split_id=split_id,
            split_position=initial_position,
        )

    raise GUIError("PYNIX-GUI-005", "GUI split requires either 2 or 4 arguments.")


def horizontal_split(*args) -> GUIView:
    return _split("horizontalSplit", *args)


def vertical_split(*args) -> GUIView:
    return _split("verticalSplit", *args)


def panel(view: GUIView, role="panel") -> GUIView:
    if role not in _PANEL_ROLES:
        raise GUIError("PYNIX-GUI-005", "GUI panel role is invalid.")
    return GUIView("panel", children=(view,), role=role)


def group(view: GUIView, role="group") -> GUIView:
    if role not in _GROUP_ROLES:
        raise GUIError("PYNIX-GUI-005", "GUI group role is invalid.")
    return GUIView("group", children=(view,), role=role)


def separator(orientation="horizontal") -> GUIView:
    if orientation not in {"horizontal", "vertical"}:
        raise GUIError(
            "PYNIX-GUI-005",
            "GUI separator orientation must be horizontal or vertical.",
        )
    return GUIView("separator", orientation=orientation)


def toolbar(view: GUIView) -> GUIView:
    return GUIView("toolbar", children=(view,), role="toolbar")


def status_bar(view: GUIView) -> GUIView:
    return GUIView("statusBar", children=(view,), role="status")


def tabs(tab_id: str, labels, selected: int, children) -> GUIView:
    if not _is_non_empty_string(tab_id):
        raise GUIError("PYNIX-GUI-005", "GUI tabs id must be a non-empty String.")

    label_values = _strings(labels, "GUI tabs labels")
    child_values = _children(children, "GUI tabs children")
    if not child_values:
        raise GUIError("PYNIX-GUI-005", "GUI tabs require at least one child.")
    if len(label_values) != len(child_values):
        raise GUIError(
            "PYNIX-GUI-005",
            "GUI tabs labels and children must have equal length.",
        )
    if type(selected) is not int or not 0 <= selected < len(child_values):
        raise GUIError("PYNIX-GUI-005", "GUI tabs selected index is out of range.")

    return GUIView(
        "tabs",
        children=child_values,
        container_id=tab_id,
        labels=label_values,
        selected=selected,
    )


def scroll(view: GUIView) -> GUIView:
    return GUIView("scroll", children=(view,), role="surfaceSunken")


def context_menu(view: GUIView, menu_value) -> GUIView:
    from .commands import GUIMenu, validate_menu_targets

    if not isinstance(menu_value, GUIMenu):
        raise GUIError("PYNIX-GUI-008", "GUI context menu requires a GUIMenu.")
    validate_menu_targets(menu_value)
    return GUIView("contextMenu", children=(view,), menu=menu_value)


def tooltip(view: GUIView, value: str) -> GUIView:
    if not _is_non_empty_string(value):
        raise GUIError("PYNIX-GUI-008", "GUI tooltip text must be a non-empty String.")
    return GUIView("tooltip", children=(view,), tooltip_text=value)


def collapsible(target: str, label: str, expanded: bool, content: GUIView) -> GUIView:
    if type(label) is not str:
        raise GUIError("PYNIX-GUI-008", "GUI collapsible label must be String.")
    if type(expanded) is not bool:
        raise GUIError("PYNIX-GUI-008", "GUI collapsible expanded state must be Bool.")
    if not isinstance(content, GUIView):
        raise GUIError("PYNIX-GUI-008", "GUI collapsible content must be GUIView.")
    return GUIView(
        "collapsible",
        children=(content,),
        target=_target(target, "GUI collapsible target"),
        text=label,
        checked=expanded,
    )


def text(value: str, role="body", *, overflow="natural") -> GUIView:
    if type(value) is not str:
        raise GUIError("PYNIX-GUI-006", "GUI text value must be String.")
    if role not in _TEXT_ROLES:
        raise GUIError("PYNIX-GUI-006", "GUI text role is invalid.")
    if overflow not in ("natural", "ellipsis", "clip", "wrap"):
        raise GUIError("PYNIX-GUI-006", "GUI text overflow must be natural, ellipsis, clip or wrap.")
    return GUIView("text", text=value, role=role, overflow=overflow)


def button(target: str, label: str, role="secondary") -> GUIView:
    if type(label) is not str:
        raise GUIError("PYNIX-GUI-006", "GUI button label must be String.")
    if role not in _BUTTON_ROLES:
        raise GUIError("PYNIX-GUI-006", "GUI button role is invalid.")
    return GUIView("button", target=_target(target), text=label, role=role)


def text_field(target: str, value: str, placeholder="") -> GUIView:
    if type(value) is not str or type(placeholder) is not str:
        raise GUIError(
            "PYNIX-GUI-006",
            "GUI text field value/placeholder must be String.",
        )
    return GUIView(
        "textField",
        target=_target(target),
        value=value,
        placeholder=placeholder,
    )


def text_area(target: str, value: str) -> GUIView:
    if type(value) is not str:
        raise GUIError("PYNIX-GUI-006", "GUI text area value must be String.")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return GUIView("textArea", target=_target(target), value=normalized)


def check_box(target: str, label: str, checked: bool) -> GUIView:
    if type(label) is not str or type(checked) is not bool:
        raise GUIError(
            "PYNIX-GUI-006",
            "GUI check box requires String label and Bool state.",
        )
    return GUIView("checkBox", target=_target(target), text=label, checked=checked)


def radio_button(target: str, label: str, selected: bool) -> GUIView:
    if type(label) is not str or type(selected) is not bool:
        raise GUIError(
            "PYNIX-GUI-006",
            "GUI radio button requires String label and Bool state.",
        )
    return GUIView("radioButton", target=_target(target), text=label, checked=selected)


def combo_box(target: str, items, selected: int) -> GUIView:
    values = _strings(items, "GUI combo box items")
    if not values:
        raise GUIError("PYNIX-GUI-006", "GUI combo box requires at least one item.")
    if type(selected) is not int or not 0 <= selected < len(values):
        raise GUIError("PYNIX-GUI-006", "GUI combo box selected index is out of range.")
    return GUIView("comboBox", target=_target(target), items=values, selected=selected)


def _range_control(kind: str, target: str | None, value, minimum, maximum) -> GUIView:
    current = _number(value, f"GUI {kind} value")
    low = _number(minimum, f"GUI {kind} minimum")
    high = _number(maximum, f"GUI {kind} maximum")

    if not low < high:
        raise GUIError("PYNIX-GUI-006", f"GUI {kind} requires minimum < maximum.")
    if not low <= current <= high:
        raise GUIError("PYNIX-GUI-006", f"GUI {kind} value is outside its range.")

    return GUIView(
        kind,
        target=None if target is None else _target(target),
        number=current,
        minimum_number=low,
        maximum_number=high,
    )


def slider(target: str, value, minimum, maximum) -> GUIView:
    return _range_control("slider", target, value, minimum, maximum)


def progress_bar(value, minimum, maximum) -> GUIView:
    return _range_control("progressBar", None, value, minimum, maximum)


def list_view(target: str, items, selected: int) -> GUIView:
    values = _strings(items, "GUI list items")
    if type(selected) is not int:
        raise GUIError("PYNIX-GUI-006", "GUI list selected index must be Int.")
    if not values:
        if selected != -1:
            raise GUIError("PYNIX-GUI-006", "Empty GUI list requires selected = -1.")
    elif not 0 <= selected < len(values):
        raise GUIError("PYNIX-GUI-006", "GUI list selected index is out of range.")
    return GUIView("list", target=_target(target), items=values, selected=selected)




def tree(target: str, nodes, expanded_ids=(), selected_id=None) -> GUIView:
    from .structured import validate_tree_state

    node_values, expanded_values, selected_value = validate_tree_state(
        nodes,
        expanded_ids,
        selected_id,
    )
    return GUIView(
        "tree",
        target=_target(target),
        data=node_values,
        expanded_ids=expanded_values,
        selected_id=selected_value,
    )


def table(target: str, columns, rows, selected_id=None) -> GUIView:
    from .structured import validate_table_state

    column_values, row_values, selected_value = validate_table_state(
        columns,
        rows,
        selected_id,
    )
    return GUIView(
        "table",
        target=_target(target),
        data=(column_values, row_values),
        selected_id=selected_value,
    )

def draggable(view: GUIView, source_id: str, payload) -> GUIView:
    from .interaction import GUIDragPayload

    if not isinstance(view, GUIView):
        raise GUIError("PYNIX-GUI-010", "GUI draggable content must be GUIView.")
    if not _is_non_empty_string(source_id):
        raise GUIError("PYNIX-GUI-010", "GUI drag source id must be a non-empty String.")
    if not isinstance(payload, GUIDragPayload):
        raise GUIError("PYNIX-GUI-010", "GUI drag payload is invalid.")
    return GUIView(
        "draggable",
        children=(view,),
        drag_source_id=source_id,
        drag_payload=payload,
    )


def drop_target(
    view: GUIView,
    target_id: str,
    accepted_kinds,
    accepted_operations=("copy", "move"),
) -> GUIView:
    if not isinstance(view, GUIView):
        raise GUIError("PYNIX-GUI-010", "GUI drop target content must be GUIView.")
    if not _is_non_empty_string(target_id):
        raise GUIError("PYNIX-GUI-010", "GUI drop target id must be a non-empty String.")

    kinds = _strings(accepted_kinds, "GUI drop target accepted kinds")
    operations = _strings(
        accepted_operations,
        "GUI drop target accepted operations",
    )
    if not kinds:
        raise GUIError("PYNIX-GUI-010", "GUI drop target requires at least one payload kind.")
    if any(operation not in {"copy", "move"} for operation in operations):
        raise GUIError("PYNIX-GUI-010", "GUI drop target operation is invalid.")
    if len(set(kinds)) != len(kinds) or len(set(operations)) != len(operations):
        raise GUIError("PYNIX-GUI-010", "GUI drop target values must be unique.")

    return GUIView(
        "dropTarget",
        children=(view,),
        drop_target_id=target_id,
        accepted_kinds=kinds,
        accepted_operations=operations,
    )


def dock_target(view: GUIView, workspace_target: str, region: str) -> GUIView:
    if not isinstance(view, GUIView):
        raise GUIError("PYNIX-GUI-010", "GUI dock target content must be GUIView.")
    if not _is_non_empty_string(workspace_target):
        raise GUIError("PYNIX-GUI-010", "GUI dock workspace target must be a non-empty String.")
    if region not in {"left", "right", "bottom", "center"}:
        raise GUIError("PYNIX-GUI-010", "GUI dock target region is invalid.")
    return GUIView(
        "dockTarget",
        children=(view,),
        drop_target_id=workspace_target,
        accepted_kinds=("pynix/dock-panel",),
        accepted_operations=("move",),
        dock_region=region,
    )


def dock_workspace(target: str, panels, state) -> GUIView:
    from .interaction import active_dock_panels, validate_dock_workspace

    if not _is_non_empty_string(target):
        raise GUIError("PYNIX-GUI-010", "GUI dock workspace target must be a non-empty String.")

    panel_values, state_value = validate_dock_workspace(panels, state)
    active = active_dock_panels(panel_values, state_value)
    children = tuple(
        active[region].content
        for region in ("left", "right", "bottom", "center")
        if active[region] is not None
    )
    return GUIView(
        "dockWorkspace",
        children=children,
        target=target,
        data=panel_values,
        dock_state=state_value,
    )


def rich_editor(
    target: str,
    text: str,
    selection_start: int,
    selection_end: int,
    spans=(),
    *,
    read_only=False,
) -> GUIView:
    from .editor import validate_editor_state

    if not _is_non_empty_string(target):
        raise GUIError("PYNIX-GUI-012", "GUI rich editor target must be a non-empty String.")
    if type(read_only) is not bool:
        raise GUIError("PYNIX-GUI-012", "GUI rich editor readOnly must be Bool.")

    text_value, start_value, end_value, span_values = validate_editor_state(
        text,
        selection_start,
        selection_end,
        spans,
    )
    return GUIView(
        "richEditor",
        target=target,
        value=text_value,
        selection_start=start_value,
        selection_end=end_value,
        spans=span_values,
        read_only=read_only,
    )


def canvas(target: str, scene) -> GUIView:
    from .canvas import GUICanvasScene

    if not _is_non_empty_string(target):
        raise GUIError("PYNIX-GUI-011", "GUI canvas target must be a non-empty String.")
    if not isinstance(scene, GUICanvasScene):
        raise GUIError("PYNIX-GUI-011", "GUI canvas scene is invalid.")
    return GUIView(
        "canvas",
        target=target,
        canvas_scene=scene,
    )


def icon(name: str, size=ICON_METRICS["iconStandard"]) -> GUIView:
    if not _is_non_empty_string(name):
        raise GUIError("PYNIX-GUI-006", "GUI icon name must be a non-empty String.")
    if type(size) is not int or size <= 0:
        raise GUIError("PYNIX-GUI-006", "GUI icon size must be a positive Int.")
    return GUIView("icon", resource=name, icon_size=size)


def vector_icon(name: str, size=ICON_METRICS["iconStandard"]) -> GUIView:
    if not _is_non_empty_string(name):
        raise GUIError("PYNIX-GUI-013", "GUI vector icon name must be a non-empty String.")
    if type(size) is not int or size <= 0:
        raise GUIError("PYNIX-GUI-013", "GUI vector icon size must be a positive Int.")
    return GUIView("vectorIcon", resource=name, icon_size=size)


def image(resource: str) -> GUIView:
    if not _is_non_empty_string(resource):
        raise GUIError(
            "PYNIX-GUI-006",
            "GUI image resource must be a non-empty String.",
        )
    return GUIView("image", resource=resource)


def enabled(view: GUIView, state: bool) -> GUIView:
    if type(state) is not bool:
        raise GUIError("PYNIX-GUI-006", "GUI enabled state must be Bool.")
    return GUIView("enabled", children=(view,), enabled=state)


def focused(view: GUIView, state: bool) -> GUIView:
    if type(state) is not bool:
        raise GUIError("PYNIX-GUI-006", "GUI focused state must be Bool.")
    return GUIView("focused", children=(view,), focused=state)


def theme(view: GUIView, theme_name: str) -> GUIView:
    if type(theme_name) is not str or theme_name not in THEMES:
        raise GUIError(
            "PYNIX-GUI-007",
            "GUI theme must be system, light, or dark.",
        )
    return GUIView("theme", children=(view,), theme=theme_name)


def validate_view(view: GUIView) -> None:
    split_ids = set()
    tab_ids = set()
    control_targets = set()
    focused_requests = []

    def invalid(message="GUI render received a malformed GUIView."):
        raise GUIError("PYNIX-GUI-005", message)

    def invalid_control(message="GUI control contract is invalid."):
        raise GUIError("PYNIX-GUI-006", message)

    def visit(node):
        if not isinstance(node, GUIView):
            invalid("GUI render requires a valid GUIView tree.")

        kind = node.kind

        if kind in {
            "empty", "spacer", "separator", "text", "button", "textField",
            "textArea", "checkBox", "radioButton", "comboBox", "slider",
            "progressBar", "list", "tree", "table", "richEditor", "canvas", "icon", "vectorIcon", "image",
        }:
            valid = node.children == ()
        elif kind in {
            "fill", "minSize", "preferredSize", "maxSize", "align", "padding",
            "scroll", "panel", "group", "toolbar", "statusBar", "enabled",
            "focused", "theme", "contextMenu", "tooltip", "collapsible",
            "draggable", "dropTarget", "dockTarget",
        }:
            valid = len(node.children) == 1
        elif kind in {"row", "column", "stack", "grid", "tabs", "dockWorkspace"}:
            valid = type(node.children) is tuple
        elif kind in {"horizontalSplit", "verticalSplit"}:
            valid = len(node.children) == 2
        else:
            valid = False

        if not valid:
            invalid()

        if kind in {"row", "column"}:
            _non_negative(node.spacing, "GUI spacing")
        if kind == "padding":
            _non_negative(node.horizontal, "GUI horizontal padding")
            _non_negative(node.vertical, "GUI vertical padding")
        if kind in {"minSize", "preferredSize", "maxSize"}:
            _non_negative(node.width, f"GUI {kind} width")
            _non_negative(node.height, f"GUI {kind} height")
        if kind == "align":
            if node.horizontal not in {"start", "center", "end", "stretch"}:
                invalid("GUI horizontal alignment is invalid.")
            if node.vertical not in {"start", "center", "end", "stretch"}:
                invalid("GUI vertical alignment is invalid.")
        if kind == "grid":
            if type(node.columns) is not int or node.columns <= 0:
                invalid("GUI grid columns must be positive.")
            _non_negative(node.column_spacing, "GUI grid column spacing")
            _non_negative(node.row_spacing, "GUI grid row spacing")
        if kind == "panel" and node.role not in _PANEL_ROLES:
            invalid("GUI panel role is invalid.")
        if kind == "group" and node.role not in _GROUP_ROLES:
            invalid("GUI group role is invalid.")
        if kind == "separator" and node.orientation not in {"horizontal", "vertical"}:
            invalid("GUI separator orientation is invalid.")
        if kind == "toolbar" and node.role != "toolbar":
            invalid("GUI toolbar role is invalid.")
        if kind == "statusBar" and node.role != "status":
            invalid("GUI status bar role is invalid.")

        if kind == "tabs":
            if not _is_non_empty_string(node.container_id):
                invalid("GUI tabs id must be a non-empty String.")
            if node.container_id in tab_ids:
                invalid(f"GUI tabs id '{node.container_id}' must be unique.")
            tab_ids.add(node.container_id)
            if type(node.labels) is not tuple or len(node.labels) != len(node.children):
                invalid("GUI tabs labels and children must have equal length.")
            if not node.children:
                invalid("GUI tabs require at least one child.")
            if any(type(label) is not str for label in node.labels):
                invalid("GUI tabs labels must contain only String values.")
            if type(node.selected) is not int or not 0 <= node.selected < len(node.children):
                invalid("GUI tabs selected index is out of range.")

        if kind in _FOCUSABLE_KINDS:
            if not _is_non_empty_string(node.target):
                invalid_control("GUI interactive control target must be a non-empty String.")
            if node.target in control_targets:
                invalid_control(f"GUI control target '{node.target}' must be unique.")
            control_targets.add(node.target)

        if kind == "text":
            if type(node.text) is not str or node.role not in _TEXT_ROLES:
                invalid_control("GUI text contract is invalid.")
        if kind == "button":
            if type(node.text) is not str or node.role not in _BUTTON_ROLES:
                invalid_control("GUI button contract is invalid.")
        if kind == "textField":
            if type(node.value) is not str or type(node.placeholder) is not str:
                invalid_control("GUI text field contract is invalid.")
        if kind == "textArea" and type(node.value) is not str:
            invalid_control("GUI text area contract is invalid.")
        if kind in {"checkBox", "radioButton"}:
            if type(node.text) is not str or type(node.checked) is not bool:
                invalid_control("GUI boolean control contract is invalid.")
        if kind == "comboBox":
            if not node.items or any(type(item) is not str for item in node.items):
                invalid_control("GUI combo box items are invalid.")
            if type(node.selected) is not int or not 0 <= node.selected < len(node.items):
                invalid_control("GUI combo box selection is invalid.")
        if kind in {"slider", "progressBar"}:
            if (
                type(node.number) is not float
                or type(node.minimum_number) is not float
                or type(node.maximum_number) is not float
                or not node.minimum_number < node.maximum_number
                or not node.minimum_number <= node.number <= node.maximum_number
            ):
                invalid_control("GUI numeric control range is invalid.")
        if kind == "list":
            if any(type(item) is not str for item in node.items):
                invalid_control("GUI list items are invalid.")
            if type(node.selected) is not int:
                invalid_control("GUI list selection is invalid.")
            if (not node.items and node.selected != -1) or (
                node.items and not 0 <= node.selected < len(node.items)
            ):
                invalid_control("GUI list selected index is invalid.")
        if kind == "icon":
            if not _is_non_empty_string(node.resource):
                invalid_control("GUI icon resource is invalid.")
            if type(node.icon_size) is not int or node.icon_size <= 0:
                invalid_control("GUI icon size is invalid.")
        if kind == "image" and not _is_non_empty_string(node.resource):
            invalid_control("GUI image resource is invalid.")
        if kind == "enabled" and type(node.enabled) is not bool:
            invalid_control("GUI enabled wrapper requires Bool state.")
        if kind == "focused":
            if type(node.focused) is not bool:
                invalid_control("GUI focused wrapper requires Bool state.")
            if node.focused:
                focused_requests.append(node)
        if kind == "theme":
            if type(node.theme) is not str or node.theme not in THEMES:
                raise GUIError(
                    "PYNIX-GUI-007",
                    "GUI theme must be system, light, or dark.",
                )

        if kind == "contextMenu":
            from .commands import GUIMenu, validate_menu_targets

            if not isinstance(node.menu, GUIMenu):
                raise GUIError("PYNIX-GUI-008", "GUI context menu requires a GUIMenu.")
            validate_menu_targets(node.menu)

        if kind == "tooltip":
            if not _is_non_empty_string(node.tooltip_text):
                raise GUIError("PYNIX-GUI-008", "GUI tooltip text must be a non-empty String.")

        if kind == "collapsible":
            if type(node.text) is not str or type(node.checked) is not bool:
                raise GUIError("PYNIX-GUI-008", "GUI collapsible contract is invalid.")

        if kind == "tree":
            from .structured import validate_tree_state

            validate_tree_state(
                node.data,
                node.expanded_ids,
                node.selected_id,
            )

        if kind == "table":
            from .structured import validate_table_state

            if (
                type(node.data) is not tuple
                or len(node.data) != 2
            ):
                raise GUIError("PYNIX-GUI-009", "GUI table data is invalid.")
            validate_table_state(
                node.data[0],
                node.data[1],
                node.selected_id,
            )

        if kind == "richEditor":
            from .editor import validate_editor_state

            if not _is_non_empty_string(node.target):
                raise GUIError("PYNIX-GUI-012", "GUI rich editor target is invalid.")
            if type(node.read_only) is not bool:
                raise GUIError("PYNIX-GUI-012", "GUI rich editor readOnly is invalid.")
            validate_editor_state(
                node.value,
                node.selection_start,
                node.selection_end,
                node.spans,
            )

        if kind == "canvas":
            from .canvas import GUICanvasScene

            if not _is_non_empty_string(node.target):
                raise GUIError("PYNIX-GUI-011", "GUI canvas target is invalid.")
            if not isinstance(node.canvas_scene, GUICanvasScene):
                raise GUIError("PYNIX-GUI-011", "GUI canvas scene is invalid.")

        if kind == "draggable":
            from .interaction import GUIDragPayload

            if not _is_non_empty_string(node.drag_source_id):
                raise GUIError("PYNIX-GUI-010", "GUI drag source id is invalid.")
            if not isinstance(node.drag_payload, GUIDragPayload):
                raise GUIError("PYNIX-GUI-010", "GUI drag payload is invalid.")

        if kind == "dropTarget":
            if not _is_non_empty_string(node.drop_target_id):
                raise GUIError("PYNIX-GUI-010", "GUI drop target id is invalid.")
            if not node.accepted_kinds:
                raise GUIError("PYNIX-GUI-010", "GUI drop target kinds are invalid.")
            if any(
                operation not in {"copy", "move"}
                for operation in node.accepted_operations
            ):
                raise GUIError("PYNIX-GUI-010", "GUI drop target operation is invalid.")

        if kind == "dockTarget":
            if not _is_non_empty_string(node.drop_target_id):
                raise GUIError("PYNIX-GUI-010", "GUI dock target workspace id is invalid.")
            if node.dock_region not in {"left", "right", "bottom", "center"}:
                raise GUIError("PYNIX-GUI-010", "GUI dock target region is invalid.")
            if node.accepted_kinds != ("pynix/dock-panel",):
                raise GUIError("PYNIX-GUI-010", "GUI dock target kind is invalid.")
            if node.accepted_operations != ("move",):
                raise GUIError("PYNIX-GUI-010", "GUI dock target operation is invalid.")

        if kind == "dockWorkspace":
            from .interaction import validate_dock_workspace

            validate_dock_workspace(node.data, node.dock_state)

        if kind in {"horizontalSplit", "verticalSplit"}:
            unmanaged = node.split_id is None and node.split_position is None
            controlled = (
                _is_non_empty_string(node.split_id)
                and type(node.split_position) is int
                and node.split_position > 0
            )
            if not (unmanaged or controlled):
                invalid("GUI split identity/position is malformed.")
            if node.split_id is not None:
                if node.split_id in split_ids:
                    invalid(f"GUI split id '{node.split_id}' must be unique.")
                split_ids.add(node.split_id)

        for child in node.children:
            visit(child)

    visit(view)

    if len(focused_requests) > 1:
        invalid_control("Only one GUI focused=true request is allowed per rendered tree.")

    def focusable_count(node):
        count = 1 if node.kind in _FOCUSABLE_KINDS else 0
        return count + sum(focusable_count(child) for child in node.children)

    if focused_requests and focusable_count(focused_requests[0].children[0]) != 1:
        invalid_control("GUI focused=true subtree must contain exactly one focusable control.")

    try:
        measure(view)
    except ValueError as error:
        raise GUIError("PYNIX-GUI-005", str(error)) from None

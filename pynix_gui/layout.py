# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Platform-independent geometry engine for PYNIX GUI."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .design import CONTROL_METRICS, ICON_METRICS, SPACING, TYPOGRAPHY


@dataclass(frozen=True, slots=True)
class GUISize:
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class GUIRect:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class GUIConstraints:
    minimum: GUISize
    preferred: GUISize
    maximum: GUISize


@dataclass(frozen=True, slots=True)
class GUILayoutNode:
    view: object
    rect: GUIRect
    children: tuple["GUILayoutNode", ...] = ()


INF = math.inf
PANEL_PADDING = float(SPACING["space3"])
PANEL_BORDER = 1.0
GROUP_PADDING = float(SPACING["space3"])
GROUP_BORDER = 1.0
TOOLBAR_HEIGHT = float(CONTROL_METRICS["toolbar"])
STATUS_HEIGHT = float(CONTROL_METRICS["statusBar"])
BAR_PADDING_X = float(SPACING["space2"])
BAR_PADDING_Y = float(SPACING["space1"])
SEPARATOR_THICKNESS = 1.0
TAB_STRIP_HEIGHT = 32.0
COLLAPSIBLE_HEADER_HEIGHT = float(CONTROL_METRICS["standardControl"])
COLLAPSIBLE_CONTENT_GAP = float(SPACING["space2"])



def _max_size(left: GUISize, right: GUISize) -> GUISize:
    return GUISize(max(left.width, right.width), max(left.height, right.height))


def _sum_axis(values, spacing: float) -> float:
    values = tuple(values)
    if not values:
        return 0.0
    return sum(values) + spacing * (len(values) - 1)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def _constraint_value(base: float, override: int | None) -> float:
    return base if override is None else float(override)


def _apply_size_wrapper(view, child: GUIConstraints) -> GUIConstraints:
    minimum = child.minimum
    preferred = child.preferred
    maximum = child.maximum

    if view.kind == "minSize":
        minimum = GUISize(
            max(minimum.width, float(view.width)),
            max(minimum.height, float(view.height)),
        )
        preferred = GUISize(
            max(preferred.width, minimum.width),
            max(preferred.height, minimum.height),
        )
    elif view.kind == "preferredSize":
        preferred = GUISize(float(view.width), float(view.height))
    elif view.kind == "maxSize":
        maximum = GUISize(
            min(maximum.width, float(view.width)),
            min(maximum.height, float(view.height)),
        )
        preferred = GUISize(
            min(preferred.width, maximum.width),
            min(preferred.height, maximum.height),
        )

    if (
        minimum.width > preferred.width
        or minimum.height > preferred.height
        or preferred.width > maximum.width
        or preferred.height > maximum.height
    ):
        raise ValueError("unsatisfiable GUI size constraints")

    return GUIConstraints(minimum, preferred, maximum)


def measure(view) -> GUIConstraints:
    """Return platform-independent intrinsic constraints for a GUIView tree."""
    kind = view.kind

    if kind in {"empty", "spacer"}:
        return GUIConstraints(
            GUISize(0.0, 0.0),
            GUISize(0.0, 0.0),
            GUISize(INF, INF),
        )

    if kind == "text":
        font_size, weight = TYPOGRAPHY[view.role]
        factor = 0.56 if weight != "monospace" else 0.62
        width = max(1.0, len(view.text)) * font_size * factor
        height = max(18.0, font_size * 1.45)
        size = GUISize(width, height)
        return GUIConstraints(size, size, GUISize(INF, height))

    if kind == "button":
        width = max(80.0, len(view.text) * 8.0 + 24.0)
        minimum = GUISize(width, float(CONTROL_METRICS["standardControl"]))
        return GUIConstraints(minimum, minimum, GUISize(INF, INF))

    if kind == "textField":
        return GUIConstraints(
            GUISize(80.0, float(CONTROL_METRICS["standardControl"])),
            GUISize(160.0, float(CONTROL_METRICS["standardControl"])),
            GUISize(INF, INF),
        )

    if kind == "textArea":
        return GUIConstraints(
            GUISize(120.0, 80.0),
            GUISize(320.0, 160.0),
            GUISize(INF, INF),
        )

    if kind == "richEditor":
        return GUIConstraints(
            GUISize(240.0, 160.0),
            GUISize(640.0, 420.0),
            GUISize(INF, INF),
        )

    if kind in {"checkBox", "radioButton"}:
        width = max(80.0, len(view.text) * 8.0 + 28.0)
        return GUIConstraints(
            GUISize(width, float(CONTROL_METRICS["compactControl"])),
            GUISize(width, float(CONTROL_METRICS["compactControl"])),
            GUISize(INF, INF),
        )

    if kind == "comboBox":
        return GUIConstraints(
            GUISize(100.0, float(CONTROL_METRICS["standardControl"])),
            GUISize(160.0, float(CONTROL_METRICS["standardControl"])),
            GUISize(INF, INF),
        )

    if kind == "slider":
        return GUIConstraints(
            GUISize(100.0, 32.0),
            GUISize(160.0, 32.0),
            GUISize(INF, INF),
        )

    if kind == "progressBar":
        return GUIConstraints(
            GUISize(100.0, 16.0),
            GUISize(160.0, 16.0),
            GUISize(INF, INF),
        )

    if kind == "list":
        return GUIConstraints(
            GUISize(120.0, 80.0),
            GUISize(240.0, 180.0),
            GUISize(INF, INF),
        )

    if kind == "tree":
        return GUIConstraints(
            GUISize(180.0, 120.0),
            GUISize(280.0, 260.0),
            GUISize(INF, INF),
        )

    if kind == "table":
        return GUIConstraints(
            GUISize(260.0, 140.0),
            GUISize(520.0, 280.0),
            GUISize(INF, INF),
        )

    if kind in {"icon", "vectorIcon"}:
        size = float(view.icon_size)
        exact = GUISize(size, size)
        return GUIConstraints(exact, exact, exact)

    if kind == "image":
        return GUIConstraints(
            GUISize(0.0, 0.0),
            GUISize(0.0, 0.0),
            GUISize(INF, INF),
        )

    if kind == "canvas":
        scene = view.canvas_scene
        preferred = GUISize(float(scene.width), float(scene.height))
        return GUIConstraints(
            GUISize(80.0, 60.0),
            preferred,
            GUISize(INF, INF),
        )

    if kind in {
        "fill", "align", "enabled", "focused", "theme",
        "contextMenu", "tooltip", "draggable", "dropTarget", "dockTarget",
    }:
        return measure(view.children[0])

    if kind == "collapsible":
        label_width = max(96.0, len(view.text or "") * 8.0 + 32.0)
        header = GUISize(label_width, COLLAPSIBLE_HEADER_HEIGHT)
        if not view.checked:
            return GUIConstraints(header, header, GUISize(INF, COLLAPSIBLE_HEADER_HEIGHT))

        child = measure(view.children[0])
        minimum = GUISize(
            max(header.width, child.minimum.width),
            COLLAPSIBLE_HEADER_HEIGHT + COLLAPSIBLE_CONTENT_GAP + child.minimum.height,
        )
        preferred = GUISize(
            max(header.width, child.preferred.width),
            COLLAPSIBLE_HEADER_HEIGHT + COLLAPSIBLE_CONTENT_GAP + child.preferred.height,
        )
        return GUIConstraints(minimum, preferred, GUISize(INF, INF))

    if kind == "dockWorkspace":
        from .interaction import active_dock_panels

        panels = tuple(view.data)
        state = view.dock_state
        active = active_dock_panels(panels, state)

        measured = {
            region: (
                None
                if panel is None
                else measure(panel.content)
            )
            for region, panel in active.items()
        }

        left = measured["left"]
        right = measured["right"]
        bottom = measured["bottom"]
        center = measured["center"]

        minimum_width = (
            (left.minimum.width if left else 0.0)
            + (right.minimum.width if right else 0.0)
            + (center.minimum.width if center else 0.0)
        )
        minimum_height = max(
            (left.minimum.height if left else 0.0),
            (right.minimum.height if right else 0.0),
            (
                (center.minimum.height if center else 0.0)
                + (bottom.minimum.height if bottom else 0.0)
            ),
        )

        preferred_width = max(
            minimum_width,
            float(state.left_width)
            + float(state.right_width)
            + (center.preferred.width if center else 320.0),
        )
        preferred_height = max(
            minimum_height,
            (center.preferred.height if center else 240.0)
            + float(state.bottom_height),
        )

        return GUIConstraints(
            GUISize(minimum_width, minimum_height),
            GUISize(preferred_width, preferred_height),
            GUISize(INF, INF),
        )

    if kind == "scroll":
        child = measure(view.children[0])
        return GUIConstraints(
            GUISize(0.0, 0.0),
            child.preferred,
            GUISize(INF, INF),
        )

    if kind in {"minSize", "preferredSize", "maxSize"}:
        return _apply_size_wrapper(view, measure(view.children[0]))

    if kind == "padding":
        child = measure(view.children[0])
        horizontal = float(view.horizontal)
        vertical = float(view.vertical)
        extra_w = horizontal * 2.0
        extra_h = vertical * 2.0
        return GUIConstraints(
            GUISize(child.minimum.width + extra_w, child.minimum.height + extra_h),
            GUISize(child.preferred.width + extra_w, child.preferred.height + extra_h),
            GUISize(
                INF if math.isinf(child.maximum.width) else child.maximum.width + extra_w,
                INF if math.isinf(child.maximum.height) else child.maximum.height + extra_h,
            ),
        )

    if kind in {"panel", "group"}:
        child = measure(view.children[0])
        inset = (
            PANEL_PADDING + PANEL_BORDER
            if kind == "panel"
            else GROUP_PADDING + GROUP_BORDER
        )
        extra = inset * 2.0
        return GUIConstraints(
            GUISize(child.minimum.width + extra, child.minimum.height + extra),
            GUISize(child.preferred.width + extra, child.preferred.height + extra),
            GUISize(
                INF if math.isinf(child.maximum.width) else child.maximum.width + extra,
                INF if math.isinf(child.maximum.height) else child.maximum.height + extra,
            ),
        )

    if kind == "toolbar":
        child = measure(view.children[0])
        minimum = GUISize(
            child.minimum.width + BAR_PADDING_X * 2.0,
            max(child.minimum.height + BAR_PADDING_Y * 2.0, TOOLBAR_HEIGHT),
        )
        preferred = GUISize(
            child.preferred.width + BAR_PADDING_X * 2.0,
            max(child.preferred.height + BAR_PADDING_Y * 2.0, TOOLBAR_HEIGHT),
        )
        return GUIConstraints(minimum, preferred, GUISize(INF, INF))

    if kind == "statusBar":
        child = measure(view.children[0])
        minimum = GUISize(
            child.minimum.width + BAR_PADDING_X * 2.0,
            max(child.minimum.height + BAR_PADDING_Y * 2.0, STATUS_HEIGHT),
        )
        preferred = GUISize(
            child.preferred.width + BAR_PADDING_X * 2.0,
            max(child.preferred.height + BAR_PADDING_Y * 2.0, STATUS_HEIGHT),
        )
        return GUIConstraints(minimum, preferred, GUISize(INF, INF))

    if kind == "separator":
        if view.orientation == "horizontal":
            return GUIConstraints(
                GUISize(0.0, SEPARATOR_THICKNESS),
                GUISize(0.0, SEPARATOR_THICKNESS),
                GUISize(INF, SEPARATOR_THICKNESS),
            )
        return GUIConstraints(
            GUISize(SEPARATOR_THICKNESS, 0.0),
            GUISize(SEPARATOR_THICKNESS, 0.0),
            GUISize(SEPARATOR_THICKNESS, INF),
        )

    if kind == "tabs":
        children = tuple(measure(child) for child in view.children)
        minimum = GUISize(
            max((item.minimum.width for item in children), default=0.0),
            max((item.minimum.height for item in children), default=0.0) + TAB_STRIP_HEIGHT,
        )
        preferred = GUISize(
            max((item.preferred.width for item in children), default=0.0),
            max((item.preferred.height for item in children), default=0.0) + TAB_STRIP_HEIGHT,
        )
        return GUIConstraints(minimum, preferred, GUISize(INF, INF))

    if kind in {"row", "column"}:
        children = tuple(measure(child) for child in view.children)
        spacing = float(view.spacing)
        if kind == "row":
            minimum = GUISize(
                _sum_axis((item.minimum.width for item in children), spacing),
                max((item.minimum.height for item in children), default=0.0),
            )
            preferred = GUISize(
                _sum_axis((item.preferred.width for item in children), spacing),
                max((item.preferred.height for item in children), default=0.0),
            )
            maximum = GUISize(INF, INF)
        else:
            minimum = GUISize(
                max((item.minimum.width for item in children), default=0.0),
                _sum_axis((item.minimum.height for item in children), spacing),
            )
            preferred = GUISize(
                max((item.preferred.width for item in children), default=0.0),
                _sum_axis((item.preferred.height for item in children), spacing),
            )
            maximum = GUISize(INF, INF)
        return GUIConstraints(minimum, preferred, maximum)

    if kind == "stack":
        children = tuple(measure(child) for child in view.children)
        minimum = GUISize(
            max((item.minimum.width for item in children), default=0.0),
            max((item.minimum.height for item in children), default=0.0),
        )
        preferred = GUISize(
            max((item.preferred.width for item in children), default=0.0),
            max((item.preferred.height for item in children), default=0.0),
        )
        return GUIConstraints(minimum, preferred, GUISize(INF, INF))

    if kind == "grid":
        children = tuple(measure(child) for child in view.children)
        columns = view.columns
        rows = (len(children) + columns - 1) // columns if children else 0
        column_min = [0.0] * columns
        column_pref = [0.0] * columns
        row_min = [0.0] * rows
        row_pref = [0.0] * rows

        for index, item in enumerate(children):
            column = index % columns
            row = index // columns
            column_min[column] = max(column_min[column], item.minimum.width)
            column_pref[column] = max(column_pref[column], item.preferred.width)
            row_min[row] = max(row_min[row], item.minimum.height)
            row_pref[row] = max(row_pref[row], item.preferred.height)

        minimum = GUISize(
            _sum_axis(column_min, float(view.column_spacing)),
            _sum_axis(row_min, float(view.row_spacing)),
        )
        preferred = GUISize(
            _sum_axis(column_pref, float(view.column_spacing)),
            _sum_axis(row_pref, float(view.row_spacing)),
        )
        return GUIConstraints(minimum, preferred, GUISize(INF, INF))

    if kind in {"horizontalSplit", "verticalSplit"}:
        first = measure(view.children[0])
        second = measure(view.children[1])
        if kind == "horizontalSplit":
            minimum = GUISize(
                first.minimum.width + second.minimum.width,
                max(first.minimum.height, second.minimum.height),
            )
            preferred = GUISize(
                first.preferred.width + second.preferred.width,
                max(first.preferred.height, second.preferred.height),
            )
        else:
            minimum = GUISize(
                max(first.minimum.width, second.minimum.width),
                first.minimum.height + second.minimum.height,
            )
            preferred = GUISize(
                max(first.preferred.width, second.preferred.width),
                first.preferred.height + second.preferred.height,
            )
        return GUIConstraints(minimum, preferred, GUISize(INF, INF))

    raise ValueError(f"unsupported GUI layout kind: {kind}")


def _is_fill_participant(view) -> bool:
    return view.kind in {"fill", "spacer"}


def _axis_values(constraints: GUIConstraints, horizontal: bool):
    if horizontal:
        return (
            constraints.minimum.width,
            constraints.preferred.width,
            constraints.maximum.width,
        )
    return (
        constraints.minimum.height,
        constraints.preferred.height,
        constraints.maximum.height,
    )


def _allocate_tracks(minimums, preferreds, available: float, spacing: float):
    minimums = list(minimums)
    preferreds = list(preferreds)

    if not minimums:
        return []

    spacing_total = spacing * max(0, len(minimums) - 1)
    content_available = max(0.0, available - spacing_total)
    total_minimum = sum(minimums)

    if total_minimum > content_available + 1e-9:
        raise ValueError("available GUI grid extent is smaller than minimum track extent")

    sizes = list(minimums)
    remaining = content_available - total_minimum

    growths = [
        max(0.0, preferreds[index] - sizes[index])
        for index in range(len(sizes))
    ]
    total_growth = sum(growths)

    if total_growth > 1e-9:
        if remaining >= total_growth:
            sizes = [
                size + growth
                for size, growth in zip(sizes, growths)
            ]
            remaining -= total_growth
        else:
            ratio = remaining / total_growth
            sizes = [
                size + growth * ratio
                for size, growth in zip(sizes, growths)
            ]
            remaining = 0.0

    if remaining > 1e-9:
        share = remaining / len(sizes)
        sizes = [size + share for size in sizes]

    return sizes


def _allocate_linear(children, available: float, spacing: float, horizontal: bool):
    measured = [measure(child) for child in children]
    minimums = []
    preferreds = []
    maximums = []

    for item in measured:
        minimum, preferred, maximum = _axis_values(item, horizontal)
        minimums.append(minimum)
        preferreds.append(preferred)
        maximums.append(maximum)

    spacing_total = spacing * max(0, len(children) - 1)
    content_available = max(0.0, available - spacing_total)
    total_minimum = sum(minimums)

    if total_minimum > content_available + 1e-9:
        raise ValueError("available GUI extent is smaller than minimum layout extent")

    sizes = list(minimums)
    remaining = content_available - total_minimum

    # Move all children from minimum toward preferred fairly before any fill
    # participant receives surplus.
    growths = [
        max(0.0, preferreds[index] - sizes[index])
        for index in range(len(sizes))
    ]
    total_growth = sum(growths)

    if total_growth > 1e-9:
        if remaining >= total_growth:
            sizes = [
                size + growth
                for size, growth in zip(sizes, growths)
            ]
            remaining -= total_growth
        else:
            ratio = remaining / total_growth
            sizes = [
                size + growth * ratio
                for size, growth in zip(sizes, growths)
            ]
            remaining = 0.0

    eligible = {
        index
        for index, child in enumerate(children)
        if _is_fill_participant(child) and sizes[index] < maximums[index]
    }

    # Equal surplus distribution with max-size clamping and redistribution.
    while remaining > 1e-9 and eligible:
        share = remaining / len(eligible)
        consumed = 0.0
        saturated = set()

        for index in eligible:
            room = maximums[index] - sizes[index]
            delta = min(share, room)
            sizes[index] += delta
            consumed += delta
            if room <= share + 1e-9:
                saturated.add(index)

        remaining -= consumed
        eligible -= saturated

        if consumed <= 1e-9:
            break

    return sizes


def _aligned_rect(view, rect: GUIRect, constraints: GUIConstraints) -> GUIRect:
    if view.kind != "align":
        return rect

    width = rect.width
    height = rect.height

    if view.horizontal != "stretch":
        width = _clamp(
            constraints.preferred.width,
            constraints.minimum.width,
            min(constraints.maximum.width, rect.width),
        )
    if view.vertical != "stretch":
        height = _clamp(
            constraints.preferred.height,
            constraints.minimum.height,
            min(constraints.maximum.height, rect.height),
        )

    if view.horizontal in {"start", "stretch"}:
        x = rect.x
    elif view.horizontal == "center":
        x = rect.x + (rect.width - width) / 2.0
    else:
        x = rect.x + rect.width - width

    if view.vertical in {"start", "stretch"}:
        y = rect.y
    elif view.vertical == "center":
        y = rect.y + (rect.height - height) / 2.0
    else:
        y = rect.y + rect.height - height

    return GUIRect(x, y, width, height)


def layout(view, width: float, height: float, *, split_positions=None) -> GUILayoutNode:
    """Calculate deterministic logical rectangles for one GUIView tree."""
    if width < 0 or height < 0:
        raise ValueError("GUI layout dimensions must be non-negative")

    split_positions = {} if split_positions is None else split_positions
    return _layout(view, GUIRect(0.0, 0.0, float(width), float(height)), split_positions)


def _layout(view, rect: GUIRect, split_positions) -> GUILayoutNode:
    constraints = measure(view)

    if (
        rect.width + 1e-9 < constraints.minimum.width
        or rect.height + 1e-9 < constraints.minimum.height
    ):
        raise ValueError("available GUI rectangle violates minimum constraints")

    kind = view.kind

    if kind in {
        "empty",
        "spacer",
        "separator",
        "text",
        "button",
        "textField",
        "textArea",
        "richEditor",
        "checkBox",
        "radioButton",
        "comboBox",
        "slider",
        "progressBar",
        "list",
        "tree",
        "table",
        "canvas",
        "icon",
        "vectorIcon",
        "image",
    }:
        return GUILayoutNode(view, rect)

    if kind in {
        "fill", "minSize", "preferredSize", "enabled", "focused", "theme",
        "contextMenu", "tooltip", "draggable", "dropTarget", "dockTarget",
    }:
        child = _layout(view.children[0], rect, split_positions)
        return GUILayoutNode(view, rect, (child,))

    if kind == "collapsible":
        if not view.checked:
            return GUILayoutNode(view, rect)

        child_rect = GUIRect(
            rect.x,
            rect.y + COLLAPSIBLE_HEADER_HEIGHT + COLLAPSIBLE_CONTENT_GAP,
            rect.width,
            max(
                0.0,
                rect.height - COLLAPSIBLE_HEADER_HEIGHT - COLLAPSIBLE_CONTENT_GAP,
            ),
        )
        child = _layout(view.children[0], child_rect, split_positions)
        return GUILayoutNode(view, rect, (child,))

    if kind == "maxSize":
        child_constraints = measure(view.children[0])
        child_rect = GUIRect(
            rect.x,
            rect.y,
            min(rect.width, float(view.width), child_constraints.maximum.width),
            min(rect.height, float(view.height), child_constraints.maximum.height),
        )
        child = _layout(view.children[0], child_rect, split_positions)
        return GUILayoutNode(view, rect, (child,))

    if kind == "scroll":
        child_constraints = measure(view.children[0])
        child_rect = GUIRect(
            rect.x,
            rect.y,
            max(rect.width, child_constraints.minimum.width, child_constraints.preferred.width),
            max(rect.height, child_constraints.minimum.height, child_constraints.preferred.height),
        )
        child = _layout(view.children[0], child_rect, split_positions)
        return GUILayoutNode(view, rect, (child,))

    if kind == "dockWorkspace":
        from .interaction import active_dock_panels

        panels = tuple(view.data)
        state = view.dock_state
        active = active_dock_panels(panels, state)

        left_width = (
            min(float(state.left_width), max(0.0, rect.width * 0.45))
            if active["left"] is not None
            else 0.0
        )
        right_width = (
            min(
                float(state.right_width),
                max(0.0, rect.width * 0.45),
                max(0.0, rect.width - left_width),
            )
            if active["right"] is not None
            else 0.0
        )
        center_width = max(0.0, rect.width - left_width - right_width)

        bottom_height = (
            min(float(state.bottom_height), max(0.0, rect.height * 0.45))
            if active["bottom"] is not None
            else 0.0
        )
        center_height = max(0.0, rect.height - bottom_height)

        region_rects = {
            "left": GUIRect(rect.x, rect.y, left_width, rect.height),
            "right": GUIRect(
                rect.x + rect.width - right_width,
                rect.y,
                right_width,
                rect.height,
            ),
            "bottom": GUIRect(
                rect.x + left_width,
                rect.y + center_height,
                center_width,
                bottom_height,
            ),
            "center": GUIRect(
                rect.x + left_width,
                rect.y,
                center_width,
                center_height,
            ),
        }

        nodes = []
        for region in ("left", "right", "bottom", "center"):
            panel = active[region]
            if panel is None:
                continue
            nodes.append(
                _layout(
                    panel.content,
                    region_rects[region],
                    split_positions,
                )
            )

        return GUILayoutNode(view, rect, tuple(nodes))

    if kind == "align":
        child_constraints = measure(view.children[0])
        child_rect = _aligned_rect(view, rect, child_constraints)
        child = _layout(view.children[0], child_rect, split_positions)
        return GUILayoutNode(view, rect, (child,))

    if kind == "padding":
        inner = GUIRect(
            rect.x + view.horizontal,
            rect.y + view.vertical,
            max(0.0, rect.width - view.horizontal * 2.0),
            max(0.0, rect.height - view.vertical * 2.0),
        )
        child = _layout(view.children[0], inner, split_positions)
        return GUILayoutNode(view, rect, (child,))

    if kind in {"panel", "group"}:
        inset = (
            PANEL_PADDING + PANEL_BORDER
            if kind == "panel"
            else GROUP_PADDING + GROUP_BORDER
        )
        inner = GUIRect(
            rect.x + inset,
            rect.y + inset,
            max(0.0, rect.width - inset * 2.0),
            max(0.0, rect.height - inset * 2.0),
        )
        child = _layout(view.children[0], inner, split_positions)
        return GUILayoutNode(view, rect, (child,))

    if kind in {"toolbar", "statusBar"}:
        inner = GUIRect(
            rect.x + BAR_PADDING_X,
            rect.y + BAR_PADDING_Y,
            max(0.0, rect.width - BAR_PADDING_X * 2.0),
            max(0.0, rect.height - BAR_PADDING_Y * 2.0),
        )
        child = _layout(view.children[0], inner, split_positions)
        return GUILayoutNode(view, rect, (child,))

    if kind == "tabs":
        page_rect = GUIRect(
            rect.x,
            rect.y + TAB_STRIP_HEIGHT,
            rect.width,
            max(0.0, rect.height - TAB_STRIP_HEIGHT),
        )
        nodes = tuple(
            _layout(child, page_rect, split_positions)
            for child in view.children
        )
        return GUILayoutNode(view, rect, nodes)

    if kind in {"row", "column"}:
        horizontal = kind == "row"
        available = rect.width if horizontal else rect.height
        sizes = _allocate_linear(
            view.children,
            available,
            float(view.spacing),
            horizontal,
        )
        cursor = rect.x if horizontal else rect.y
        nodes = []

        for child_view, size in zip(view.children, sizes):
            if horizontal:
                child_rect = GUIRect(cursor, rect.y, size, rect.height)
                cursor += size + view.spacing
            else:
                child_rect = GUIRect(rect.x, cursor, rect.width, size)
                cursor += size + view.spacing
            nodes.append(_layout(child_view, child_rect, split_positions))

        return GUILayoutNode(view, rect, tuple(nodes))

    if kind == "stack":
        return GUILayoutNode(
            view,
            rect,
            tuple(_layout(child, rect, split_positions) for child in view.children),
        )

    if kind == "grid":
        columns = view.columns
        count = len(view.children)
        rows = (count + columns - 1) // columns if count else 0

        if count == 0:
            return GUILayoutNode(view, rect)

        measured = [measure(child) for child in view.children]
        column_min = [0.0] * columns
        column_pref = [0.0] * columns
        row_min = [0.0] * rows
        row_pref = [0.0] * rows

        for index, item in enumerate(measured):
            column = index % columns
            row = index // columns
            column_min[column] = max(column_min[column], item.minimum.width)
            column_pref[column] = max(column_pref[column], item.preferred.width)
            row_min[row] = max(row_min[row], item.minimum.height)
            row_pref[row] = max(row_pref[row], item.preferred.height)

        column_widths = _allocate_tracks(
            column_min,
            column_pref,
            rect.width,
            float(view.column_spacing),
        )
        row_heights = _allocate_tracks(
            row_min,
            row_pref,
            rect.height,
            float(view.row_spacing),
        )

        column_offsets = []
        cursor = rect.x
        for width in column_widths:
            column_offsets.append(cursor)
            cursor += width + view.column_spacing

        row_offsets = []
        cursor = rect.y
        for height in row_heights:
            row_offsets.append(cursor)
            cursor += height + view.row_spacing

        nodes = []
        for index, child in enumerate(view.children):
            column = index % columns
            row = index // columns
            child_rect = GUIRect(
                column_offsets[column],
                row_offsets[row],
                column_widths[column],
                row_heights[row],
            )
            nodes.append(_layout(child, child_rect, split_positions))

        return GUILayoutNode(view, rect, tuple(nodes))

    if kind in {"horizontalSplit", "verticalSplit"}:
        first_view, second_view = view.children
        first_constraints = measure(first_view)
        second_constraints = measure(second_view)
        horizontal = kind == "horizontalSplit"

        total = rect.width if horizontal else rect.height
        first_min = first_constraints.minimum.width if horizontal else first_constraints.minimum.height
        first_max = first_constraints.maximum.width if horizontal else first_constraints.maximum.height
        second_min = second_constraints.minimum.width if horizontal else second_constraints.minimum.height

        default_position = view.split_position
        if default_position is None:
            default_position = total / 2.0

        position = split_positions.get(view.split_id, default_position)
        lower = first_min
        upper = total - second_min
        if not math.isinf(first_max):
            upper = min(upper, first_max)

        if lower > upper + 1e-9:
            raise ValueError("split pane minimum constraints cannot fit available extent")

        position = _clamp(float(position), lower, upper)

        if horizontal:
            first_rect = GUIRect(rect.x, rect.y, position, rect.height)
            second_rect = GUIRect(
                rect.x + position,
                rect.y,
                total - position,
                rect.height,
            )
        else:
            first_rect = GUIRect(rect.x, rect.y, rect.width, position)
            second_rect = GUIRect(
                rect.x,
                rect.y + position,
                rect.width,
                total - position,
            )

        return GUILayoutNode(
            view,
            rect,
            (
                _layout(first_view, first_rect, split_positions),
                _layout(second_view, second_rect, split_positions),
            ),
        )

    raise ValueError(f"unsupported GUI layout kind: {kind}")

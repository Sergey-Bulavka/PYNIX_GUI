# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Width-first, read-only height planning for text-bearing layout trees."""

from __future__ import annotations

import math

from .layout import (
    BAR_PADDING_X, BAR_PADDING_Y, GROUP_PADDING, GROUP_BORDER,
    PANEL_PADDING, PANEL_BORDER, TAB_STRIP_HEIGHT, GUIRect,
    _allocate_linear, _allocate_tracks, measure,
)


def height_for_width(view, width, *, measure_wrapped, text_metrics=None):
    """Return needed logical height after allocating the available width.

    This is the geometry preflight, not yet a replacement for layout().
    measure_wrapped(role, text, width) returns a GUIWrappedText record.
    """
    if not math.isfinite(width) or width <= 0:
        raise ValueError("height-for-width requires a positive finite width")

    kind = view.kind
    baseline = measure(view, text_metrics=text_metrics).minimum.height

    if kind == "text" and getattr(view, "overflow", "natural") == "wrap":
        return max(baseline, float(
            measure_wrapped(view.role, view.text, width).height
        ))

    if not view.children:
        return baseline

    if kind == "row":
        widths = _allocate_linear(
            view.children, width, float(view.spacing), True,
            text_metrics=text_metrics,
        )
        return max(
            (height_for_width(child, max(0.0001, child_width),
                              measure_wrapped=measure_wrapped,
                              text_metrics=text_metrics)
             for child, child_width in zip(view.children, widths)),
            default=0.0,
        )

    if kind == "column":
        return (
            sum(height_for_width(child, width,
                                 measure_wrapped=measure_wrapped,
                                 text_metrics=text_metrics)
                for child in view.children)
            + float(view.spacing) * max(0, len(view.children) - 1)
        )

    if kind == "grid":
        n = len(view.children)
        count = view.columns
        rows = (n + count - 1) // count
        measured = [measure(child, text_metrics=text_metrics)
                    for child in view.children]
        mins = [0.0] * count
        prefs = [0.0] * count
        for index, child in enumerate(measured):
            col = index % count
            mins[col] = max(mins[col], child.minimum.width)
            prefs[col] = max(prefs[col], child.preferred.width)
        tracks = _allocate_tracks(mins, prefs, width, float(view.column_spacing))
        heights = [0.0] * rows
        for index, child in enumerate(view.children):
            row = index // count
            child_width = tracks[index % count]
            heights[row] = max(
                heights[row],
                height_for_width(child, max(0.0001, child_width),
                                 measure_wrapped=measure_wrapped,
                                 text_metrics=text_metrics),
            )
        return sum(heights) + max(0, rows - 1) * float(view.row_spacing)

    if kind in ("padding", "panel", "group", "toolbar", "statusBar"):
        if kind == "padding":
            inset_x, inset_y = float(view.horizontal), float(view.vertical)
        elif kind == "panel":
            inset_x = inset_y = PANEL_PADDING + PANEL_BORDER
        elif kind == "group":
            inset_x = inset_y = GROUP_PADDING + GROUP_BORDER
        else:
            inset_x, inset_y = BAR_PADDING_X, BAR_PADDING_Y
        return (
            height_for_width(
                view.children[0], max(0.0001, width - 2 * inset_x),
                measure_wrapped=measure_wrapped, text_metrics=text_metrics,
            )
            + 2 * inset_y
        )

    if kind == "tabs":
        return TAB_STRIP_HEIGHT + max(
            (height_for_width(child, width,
                              measure_wrapped=measure_wrapped,
                              text_metrics=text_metrics)
             for child in view.children),
            default=0.0,
        )

    if len(view.children) == 1:
        return height_for_width(
            view.children[0], width,
            measure_wrapped=measure_wrapped, text_metrics=text_metrics,
        )

    return max(baseline, *(height_for_width(
        child, width, measure_wrapped=measure_wrapped,
        text_metrics=text_metrics,
    ) for child in view.children))

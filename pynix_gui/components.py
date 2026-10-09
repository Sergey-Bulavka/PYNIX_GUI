# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""High-level commercial components composed from stable PYNIX GUI primitives."""

from __future__ import annotations

from collections.abc import Sequence

from .core import (
    GUIError,
    GUIView,
    button,
    column,
    empty,
    fill,
    group,
    padding,
    panel,
    row,
    text,
    text_field,
)


def _view(value, label: str) -> GUIView:
    if not isinstance(value, GUIView):
        raise GUIError("PYNIX-GUI-014", f"{label} must be GUIView.")
    return value


def _views(values, label: str) -> tuple[GUIView, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise GUIError("PYNIX-GUI-014", f"{label} must be a GUIView sequence.")
    result = tuple(values)
    if any(not isinstance(item, GUIView) for item in result):
        raise GUIError("PYNIX-GUI-014", f"{label} must contain only GUIView values.")
    return result


def _optional_text(value, label: str) -> str | None:
    if value is not None and type(value) is not str:
        raise GUIError("PYNIX-GUI-014", f"{label} must be String or null.")
    return value


def card(
    title: str,
    content: GUIView,
    subtitle: str | None = None,
    footer: GUIView | None = None,
    *,
    role: str = "card",
) -> GUIView:
    if type(title) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI card title must be String.")
    _optional_text(subtitle, "GUI card subtitle")
    _view(content, "GUI card content")
    if footer is not None:
        _view(footer, "GUI card footer")

    parts = [text(title, "titleSmall")]
    if subtitle:
        parts.append(text(subtitle, "caption"))
    parts.append(content)
    if footer is not None:
        parts.append(footer)
    return panel(column(parts, 12), role)


def hero(
    title: str,
    subtitle: str,
    actions=(),
) -> GUIView:
    if type(title) is not str or type(subtitle) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI hero title/subtitle must be String.")
    action_views = _views(actions, "GUI hero actions")
    body = [
        text("PYNIX GUI", "overline"),
        text(title, "display"),
        text(subtitle, "body"),
    ]
    if action_views:
        body.append(row(action_views, 8))
    return panel(column(body, 10), "hero")


def metric_card(
    label: str,
    value: str,
    detail: str = "",
    badge_view: GUIView | None = None,
) -> GUIView:
    if any(type(item) is not str for item in (label, value, detail)):
        raise GUIError("PYNIX-GUI-014", "GUI metric card text values must be String.")
    if badge_view is not None:
        _view(badge_view, "GUI metric card badge")

    top = [text(label, "caption"), fill(empty())]
    if badge_view is not None:
        top.append(badge_view)

    body = [
        row(top, 8),
        text(value, "metric"),
    ]
    if detail:
        body.append(text(detail, "caption"))
    return panel(column(body, 8), "card")


_BADGE_ROLES = {
    "neutral": "mutedSurface",
    "accent": "accentSurface",
    "success": "successSurface",
    "warning": "warningSurface",
    "danger": "dangerSurface",
    "info": "infoSurface",
}


def badge(label: str, tone: str = "neutral") -> GUIView:
    if type(label) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI badge label must be String.")
    role = _BADGE_ROLES.get(tone)
    if role is None:
        raise GUIError("PYNIX-GUI-014", "GUI badge tone is invalid.")
    return group(padding(text(label, "caption"), 8, 3), role)


def alert(title: str, message: str, tone: str = "info") -> GUIView:
    if type(title) is not str or type(message) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI alert title/message must be String.")
    role = _BADGE_ROLES.get(tone)
    if role is None or tone == "neutral":
        role = "infoSurface" if tone == "neutral" else None
    if role is None:
        raise GUIError("PYNIX-GUI-014", "GUI alert tone is invalid.")
    return group(
        column([
            text(title, "bodyStrong"),
            text(message, "body"),
        ], 4),
        role,
    )


def search_field(
    target: str,
    value: str = "",
    placeholder: str = "Search",
) -> GUIView:
    return text_field(target, value, placeholder)


def navigation_item(target: str, label: str, selected: bool = False) -> GUIView:
    if type(selected) is not bool:
        raise GUIError("PYNIX-GUI-014", "GUI navigation selected state must be Bool.")
    return fill(button(target, label, "primary" if selected else "quiet"))


def navigation_sidebar(
    title: str,
    items,
    footer: GUIView | None = None,
) -> GUIView:
    if type(title) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI navigation title must be String.")
    item_views = _views(items, "GUI navigation items")
    if footer is not None:
        _view(footer, "GUI navigation footer")

    body = [
        text(title, "heading"),
        column(item_views, 4),
        fill(empty()),
    ]
    if footer is not None:
        body.append(footer)
    return panel(column(body, 16), "navigation")


def section_header(
    title: str,
    subtitle: str | None = None,
    action: GUIView | None = None,
) -> GUIView:
    if type(title) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI section title must be String.")
    _optional_text(subtitle, "GUI section subtitle")
    if action is not None:
        _view(action, "GUI section action")

    heading = [text(title, "heading")]
    if subtitle:
        heading.append(text(subtitle, "body"))
    parts = [column(heading, 4), fill(empty())]
    if action is not None:
        parts.append(action)
    return row(parts, 12)


def form_row(
    label: str,
    control: GUIView,
    helper: str | None = None,
) -> GUIView:
    if type(label) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI form row label must be String.")
    _view(control, "GUI form row control")
    _optional_text(helper, "GUI form row helper")

    parts = [text(label, "label"), control]
    if helper:
        parts.append(text(helper, "caption"))
    return column(parts, 6)


def form_section(
    title: str,
    rows,
    description: str | None = None,
) -> GUIView:
    row_views = _views(rows, "GUI form section rows")
    return card(
        title,
        column(row_views, 16),
        subtitle=description,
    )


def property_row(
    label: str,
    value: str,
    detail: str | None = None,
) -> GUIView:
    if type(label) is not str or type(value) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI property row label/value must be String.")
    _optional_text(detail, "GUI property row detail")

    # Reserve native glyph overhang inside the property label column.\n    # The backend-independent text estimator is deliberately approximate;\n    # a local inset protects the complete label without changing other layouts.\n    left = [padding(text(label, "bodyStrong"), 6, 0)]\n    if detail:
        left.append(text(detail, "caption"))
    return row([
        column(left, 2),
        fill(empty()),
        text(value, "bodyStrong"),
    ], 12)


def empty_state(
    title: str,
    message: str,
    action: GUIView | None = None,
) -> GUIView:
    if type(title) is not str or type(message) is not str:
        raise GUIError("PYNIX-GUI-014", "GUI empty state title/message must be String.")
    if action is not None:
        _view(action, "GUI empty state action")

    parts = [
        text(title, "title"),
        text(message, "body"),
    ]
    if action is not None:
        parts.append(action)
    return group(padding(column(parts, 12), 24), "mutedSurface")


def button_group(buttons) -> GUIView:
    return row(_views(buttons, "GUI button group"), 8)

# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Immutable retained 2D canvas scene model."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from .core import GUIError


def _number(value, label):
    if type(value) not in {int, float}:
        raise GUIError("PYNIX-GUI-011", f"{label} must be numeric.")
    return float(value)


def _positive(value, label):
    result = _number(value, label)
    if result <= 0:
        raise GUIError("PYNIX-GUI-011", f"{label} must be positive.")
    return result


def _non_empty(value, label):
    if type(value) is not str or value == "":
        raise GUIError("PYNIX-GUI-011", f"{label} must be a non-empty String.")
    return value


def _optional_target(value):
    if value is None:
        return None
    return _non_empty(value, "GUI canvas hit target")


def _role(value):
    if type(value) is not str or value == "":
        raise GUIError("PYNIX-GUI-011", "GUI canvas color role must be non-empty String.")
    return value


@dataclass(frozen=True, slots=True)
class GUICanvasCommand:
    kind: str
    values: tuple
    stroke_role: str | None = None
    fill_role: str | None = None
    line_width: float = 1.0
    text_role: str | None = None
    resource: str | None = None
    hit_target: str | None = None
    children: tuple["GUICanvasCommand", ...] = ()

    def __post_init__(self):
        if self.kind not in {
            "line", "rect", "ellipse", "path", "text", "image",
            "clip", "transform",
        }:
            raise GUIError("PYNIX-GUI-011", "GUI canvas command kind is invalid.")
        if type(self.values) is not tuple:
            raise GUIError("PYNIX-GUI-011", "GUI canvas command values are invalid.")
        if type(self.line_width) not in {int, float} or self.line_width <= 0:
            raise GUIError("PYNIX-GUI-011", "GUI canvas line width must be positive.")
        if self.stroke_role is not None:
            _role(self.stroke_role)
        if self.fill_role is not None:
            _role(self.fill_role)
        if self.text_role is not None:
            _non_empty(self.text_role, "GUI canvas text role")
        if self.resource is not None:
            _non_empty(self.resource, "GUI canvas image resource")
        _optional_target(self.hit_target)
        if type(self.children) is not tuple or any(
            not isinstance(child, GUICanvasCommand) for child in self.children
        ):
            raise GUIError("PYNIX-GUI-011", "GUI canvas command children are invalid.")


@dataclass(frozen=True, slots=True)
class GUICanvasScene:
    commands: tuple[GUICanvasCommand, ...]
    width: float
    height: float

    def __post_init__(self):
        if type(self.commands) is not tuple or any(
            not isinstance(command, GUICanvasCommand)
            for command in self.commands
        ):
            raise GUIError("PYNIX-GUI-011", "GUI canvas scene commands are invalid.")
        if self.width <= 0 or self.height <= 0:
            raise GUIError("PYNIX-GUI-011", "GUI canvas scene size must be positive.")

        seen = set()

        def visit(commands):
            for command in commands:
                if command.hit_target is not None:
                    if command.hit_target in seen:
                        raise GUIError(
                            "PYNIX-GUI-011",
                            "GUI canvas hit targets must be unique.",
                        )
                    seen.add(command.hit_target)
                visit(command.children)

        visit(self.commands)


def canvas_scene(width, height, commands) -> GUICanvasScene:
    if isinstance(commands, (str, bytes)) or not isinstance(commands, Sequence):
        raise GUIError("PYNIX-GUI-011", "GUI canvas commands must be a sequence.")
    return GUICanvasScene(
        tuple(commands),
        _positive(width, "GUI canvas width"),
        _positive(height, "GUI canvas height"),
    )


def canvas_line(x1, y1, x2, y2, *, stroke="textPrimary", line_width=1, hit_target=None):
    return GUICanvasCommand(
        "line",
        tuple(_number(v, "GUI canvas line coordinate") for v in (x1, y1, x2, y2)),
        stroke_role=_role(stroke),
        line_width=_positive(line_width, "GUI canvas line width"),
        hit_target=_optional_target(hit_target),
    )


def canvas_rect(
    x, y, width, height, *,
    stroke="borderStrong",
    fill=None,
    line_width=1,
    hit_target=None,
):
    return GUICanvasCommand(
        "rect",
        (
            _number(x, "GUI canvas rectangle x"),
            _number(y, "GUI canvas rectangle y"),
            _positive(width, "GUI canvas rectangle width"),
            _positive(height, "GUI canvas rectangle height"),
        ),
        stroke_role=None if stroke is None else _role(stroke),
        fill_role=None if fill is None else _role(fill),
        line_width=_positive(line_width, "GUI canvas line width"),
        hit_target=_optional_target(hit_target),
    )


def canvas_ellipse(
    x, y, width, height, *,
    stroke="borderStrong",
    fill=None,
    line_width=1,
    hit_target=None,
):
    return GUICanvasCommand(
        "ellipse",
        (
            _number(x, "GUI canvas ellipse x"),
            _number(y, "GUI canvas ellipse y"),
            _positive(width, "GUI canvas ellipse width"),
            _positive(height, "GUI canvas ellipse height"),
        ),
        stroke_role=None if stroke is None else _role(stroke),
        fill_role=None if fill is None else _role(fill),
        line_width=_positive(line_width, "GUI canvas line width"),
        hit_target=_optional_target(hit_target),
    )


def canvas_path(points, *, closed=False, stroke="textPrimary", fill=None, line_width=1, hit_target=None):
    if isinstance(points, (str, bytes)) or not isinstance(points, Sequence):
        raise GUIError("PYNIX-GUI-011", "GUI canvas path points must be a sequence.")
    values = []
    for point in points:
        if (
            not isinstance(point, Sequence)
            or isinstance(point, (str, bytes))
            or len(point) != 2
        ):
            raise GUIError("PYNIX-GUI-011", "GUI canvas path point must be x/y pair.")
        values.extend([
            _number(point[0], "GUI canvas path x"),
            _number(point[1], "GUI canvas path y"),
        ])
    if len(values) < 4:
        raise GUIError("PYNIX-GUI-011", "GUI canvas path requires at least two points.")
    return GUICanvasCommand(
        "path",
        (bool(closed), *values),
        stroke_role=None if stroke is None else _role(stroke),
        fill_role=None if fill is None else _role(fill),
        line_width=_positive(line_width, "GUI canvas line width"),
        hit_target=_optional_target(hit_target),
    )


def canvas_text(x, y, value, *, role="body", color="textPrimary", hit_target=None):
    if type(value) is not str:
        raise GUIError("PYNIX-GUI-011", "GUI canvas text must be String.")
    return GUICanvasCommand(
        "text",
        (
            _number(x, "GUI canvas text x"),
            _number(y, "GUI canvas text y"),
            value,
        ),
        fill_role=_role(color),
        text_role=_non_empty(role, "GUI canvas text role"),
        hit_target=_optional_target(hit_target),
    )


def canvas_image(x, y, width, height, resource, *, hit_target=None):
    return GUICanvasCommand(
        "image",
        (
            _number(x, "GUI canvas image x"),
            _number(y, "GUI canvas image y"),
            _positive(width, "GUI canvas image width"),
            _positive(height, "GUI canvas image height"),
        ),
        resource=_non_empty(resource, "GUI canvas image resource"),
        hit_target=_optional_target(hit_target),
    )


def canvas_clip(x, y, width, height, commands):
    if isinstance(commands, (str, bytes)) or not isinstance(commands, Sequence):
        raise GUIError("PYNIX-GUI-011", "GUI canvas clip commands must be a sequence.")
    return GUICanvasCommand(
        "clip",
        (
            _number(x, "GUI canvas clip x"),
            _number(y, "GUI canvas clip y"),
            _positive(width, "GUI canvas clip width"),
            _positive(height, "GUI canvas clip height"),
        ),
        children=tuple(commands),
    )


def canvas_transform(commands, *, translate_x=0, translate_y=0, scale_x=1, scale_y=1, rotate=0):
    if isinstance(commands, (str, bytes)) or not isinstance(commands, Sequence):
        raise GUIError("PYNIX-GUI-011", "GUI canvas transform commands must be a sequence.")
    sx = _number(scale_x, "GUI canvas scale x")
    sy = _number(scale_y, "GUI canvas scale y")
    if sx == 0 or sy == 0:
        raise GUIError("PYNIX-GUI-011", "GUI canvas scale must be non-zero.")
    return GUICanvasCommand(
        "transform",
        (
            _number(translate_x, "GUI canvas translate x"),
            _number(translate_y, "GUI canvas translate y"),
            sx,
            sy,
            _number(rotate, "GUI canvas rotation"),
        ),
        children=tuple(commands),
    )

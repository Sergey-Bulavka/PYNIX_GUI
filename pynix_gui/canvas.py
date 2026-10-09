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



def _matrix_multiply(first, second):
    a1, b1, c1, d1, e1, f1 = first
    a2, b2, c2, d2, e2, f2 = second
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _matrix_inverse(value):
    a, b, c, d, e, f = value
    determinant = a * d - b * c
    if abs(determinant) < 1e-12:
        return None
    inv = 1.0 / determinant
    return (
        d * inv,
        -b * inv,
        -c * inv,
        a * inv,
        (c * f - d * e) * inv,
        (b * e - a * f) * inv,
    )


def _transform_point(matrix, x, y):
    a, b, c, d, e, f = matrix
    return (
        a * x + c * y + e,
        b * x + d * y + f,
    )


def _command_transform(command):
    import math

    tx, ty, sx, sy, rotation = command.values
    angle = math.radians(rotation)
    cos_value = math.cos(angle)
    sin_value = math.sin(angle)

    translate = (1.0, 0.0, 0.0, 1.0, tx, ty)
    scale = (sx, 0.0, 0.0, sy, 0.0, 0.0)
    rotate = (
        cos_value,
        sin_value,
        -sin_value,
        cos_value,
        0.0,
        0.0,
    )
    return _matrix_multiply(
        translate,
        _matrix_multiply(scale, rotate),
    )


def _distance_to_segment(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    length_squared = dx * dx + dy * dy
    if length_squared <= 1e-12:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = ((px - x1) * dx + (py - y1) * dy) / length_squared
    t = max(0.0, min(1.0, t))
    cx = x1 + t * dx
    cy = y1 + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def _point_in_polygon(x, y, points):
    inside = False
    count = len(points)
    if count < 3:
        return False
    previous = points[-1]
    for current in points:
        x1, y1 = previous
        x2, y2 = current
        intersects = (
            (y1 > y) != (y2 > y)
            and x
            < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1
        )
        if intersects:
            inside = not inside
        previous = current
    return inside


def _command_contains(command, x, y):
    if command.kind in {"rect", "image"}:
        rx, ry, width, height = command.values[:4]
        return rx <= x <= rx + width and ry <= y <= ry + height

    if command.kind == "ellipse":
        rx, ry, width, height = command.values
        cx = rx + width / 2.0
        cy = ry + height / 2.0
        nx = (x - cx) / (width / 2.0)
        ny = (y - cy) / (height / 2.0)
        return nx * nx + ny * ny <= 1.0

    if command.kind == "text":
        tx, ty, value = command.values
        approximate_width = max(12.0, len(value) * 8.0)
        approximate_height = 20.0
        return (
            tx <= x <= tx + approximate_width
            and ty - approximate_height <= y <= ty + 4.0
        )

    if command.kind == "line":
        x1, y1, x2, y2 = command.values
        tolerance = max(4.0, float(command.line_width) * 2.0)
        return _distance_to_segment(x, y, x1, y1, x2, y2) <= tolerance

    if command.kind == "path":
        closed = bool(command.values[0])
        values = command.values[1:]
        points = [
            (values[index], values[index + 1])
            for index in range(0, len(values), 2)
        ]
        if closed and _point_in_polygon(x, y, points):
            return True
        tolerance = max(4.0, float(command.line_width) * 2.0)
        for first, second in zip(points, points[1:]):
            if _distance_to_segment(
                x,
                y,
                first[0],
                first[1],
                second[0],
                second[1],
            ) <= tolerance:
                return True
        if closed and len(points) > 2:
            first = points[-1]
            second = points[0]
            return _distance_to_segment(
                x,
                y,
                first[0],
                first[1],
                second[0],
                second[1],
            ) <= tolerance
        return False

    return False


def canvas_viewport(scene, host_width, host_height):
    """Return uniform aspect-fit scale and centered host offset for a scene."""
    if not isinstance(scene, GUICanvasScene):
        raise GUIError("PYNIX-GUI-011", "GUI canvas viewport requires a scene.")
    width = float(host_width)
    height = float(host_height)
    if width <= 0 or height <= 0:
        return (0.0, 0.0, 0.0)

    scale = min(width / scene.width, height / scene.height)
    draw_width = scene.width * scale
    draw_height = scene.height * scale
    offset_x = (width - draw_width) / 2.0
    offset_y = (height - draw_height) / 2.0
    return (scale, offset_x, offset_y)


def hit_test_scene(scene, x, y, host_width, host_height):
    """Return the topmost semantic hit target at host-logical coordinates."""
    if not isinstance(scene, GUICanvasScene):
        raise GUIError("PYNIX-GUI-011", "GUI canvas hit test requires a scene.")
    if host_width <= 0 or host_height <= 0:
        return None

    scale, offset_x, offset_y = canvas_viewport(scene, host_width, host_height)
    if scale <= 0:
        return None

    local_host_x = float(x) - offset_x
    local_host_y = float(y) - offset_y
    draw_width = scene.width * scale
    draw_height = scene.height * scale
    if (
        local_host_x < 0
        or local_host_y < 0
        or local_host_x > draw_width
        or local_host_y > draw_height
    ):
        return None

    logical_x = local_host_x / scale
    logical_y = local_host_y / scale
    identity = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    def visit(commands, matrix):
        inverse = _matrix_inverse(matrix)
        if inverse is None:
            return None
        local_x, local_y = _transform_point(
            inverse,
            logical_x,
            logical_y,
        )

        for command in reversed(commands):
            if command.kind == "transform":
                child_matrix = _matrix_multiply(
                    matrix,
                    _command_transform(command),
                )
                found = visit(command.children, child_matrix)
                if found is not None:
                    return found
                continue

            if command.kind == "clip":
                cx, cy, width, height = command.values
                if (
                    cx <= local_x <= cx + width
                    and cy <= local_y <= cy + height
                ):
                    found = visit(command.children, matrix)
                    if found is not None:
                        return found
                continue

            if (
                command.hit_target is not None
                and _command_contains(command, local_x, local_y)
            ):
                return command.hit_target

        return None

    return visit(scene.commands, identity)

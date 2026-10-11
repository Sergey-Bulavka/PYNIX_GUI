# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
"""PYNIX IDE original 20×20 vector icon vocabulary, scaled for 16/20 px use.

Paths follow one stroke system and are not copies of third-party product icons.
All coordinates are in logical icon pixels. The renderer is backend-independent.
"""
from dataclasses import dataclass

GRID = 20
STROKE = 1.6
ICONS = {
    "explorer": (("rect", 3, 2.5, 14, 15, 2), ("line", 6, 7, 14, 7), ("line", 6, 10.5, 14, 10.5), ("line", 6, 14, 11, 14)),
    "search": (("circle", 8.5, 8.5, 5.6), ("line", 12.7, 12.7, 17.2, 17.2)),
    "run": (("poly", ((6, 3.8), (16, 10), (6, 16.2)), True),),
    "debug": (("circle", 10, 10, 5.5), ("line", 10, 4.5, 10, 2), ("line", 10, 15.5, 10, 18), ("line", 4.5, 10, 2, 10), ("line", 15.5, 10, 18, 10)),
    "settings": (("circle", 10, 10, 7), ("circle", 10, 10, 2.6), ("line", 10, 1, 10, 3), ("line", 10, 17, 10, 19), ("line", 1, 10, 3, 10), ("line", 17, 10, 19, 10)),
    "terminal": (("rect", 2.5, 3, 15, 14, 2), ("poly", ((5.5, 7), (9, 10), (5.5, 13)), False), ("line", 11, 13.3, 15.1, 13.3)),
    "folder": (("poly", ((2, 6), (2, 16), (18, 16), (18, 6), (9, 6), (7.4, 4), (2, 4)), True),),
    "folder-open": (("poly", ((2, 7), (4, 16), (17, 16), (19, 8), (8, 8), (6.5, 5), (2, 5)), True),),
    "file": (("poly", ((5, 2), (12, 2), (16, 6), (16, 18), (5, 18)), True), ("line", 12, 2, 12, 6), ("line", 12, 6, 16, 6)),
    "pnx": (("poly", ((5, 2), (12, 2), (16, 6), (16, 18), (5, 18)), True), ("line", 12, 2, 12, 6), ("line", 12, 6, 16, 6), ("poly", ((8, 9), (6.5, 11.5), (8, 14)), False), ("poly", ((12, 9), (13.5, 11.5), (12, 14)), False)),
    "chevron-right": (("poly", ((7, 5), (12, 10), (7, 15)), False),),
    "chevron-down": (("poly", ((5, 7), (10, 12), (15, 7)), False),),
    "close": (("line", 5, 5, 15, 15), ("line", 15, 5, 5, 15)),
    "more": (("dot", 4, 10, 1), ("dot", 10, 10, 1), ("dot", 16, 10, 1)),
    "problems": (("poly", ((10, 2), (19, 17), (1, 17)), True), ("line", 10, 7, 10, 12), ("dot", 10, 14.5, 0.9)),
    "output": (("rect", 3, 3, 14, 14, 2), ("line", 6, 7, 14, 7), ("line", 6, 10, 14, 10), ("line", 6, 13, 11, 13)),
    "split": (("rect", 2, 3, 16, 14, 2), ("line", 10, 3, 10, 17)),
    "panel": (("rect", 2, 3, 16, 14, 2), ("line", 2, 12, 18, 12)),
}


def draw_icon(appkit, x, y, name, color, size=20):
    """Stroke paths in AppKit, with unified scale, cap and join semantics."""
    if name not in ICONS:
        raise ValueError(f"unknown IDE icon: {name}")
    scale = size / GRID
    appkit.NSGraphicsContext.saveGraphicsState()
    try:
        transform = appkit.NSAffineTransform.transform()
        transform.translateXBy_yBy_(x, y)
        transform.scaleBy_(scale)
        transform.concat()
        color.setStroke()
        color.setFill()
        for command in ICONS[name]:
            kind = command[0]
            path = appkit.NSBezierPath.bezierPath()
            if kind == "line":
                _, x1, y1, x2, y2 = command
                path.moveToPoint_((x1, y1))
                path.lineToPoint_((x2, y2))
            elif kind == "poly":
                _, points, closed = command
                path.moveToPoint_(points[0])
                for point in points[1:]:
                    path.lineToPoint_(point)
                if closed:
                    path.closePath()
            elif kind == "rect":
                _, rx, ry, width, height, radius = command
                path = appkit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                    (rx, ry, width, height), radius, radius)
            elif kind == "circle":
                _, cx, cy, radius = command
                path = appkit.NSBezierPath.bezierPathWithOvalInRect_(
                    (cx-radius, cy-radius, radius*2, radius*2))
            elif kind == "dot":
                _, cx, cy, radius = command
                path = appkit.NSBezierPath.bezierPathWithOvalInRect_(
                    (cx-radius, cy-radius, radius*2, radius*2))
                path.fill()
                continue
            path.setLineWidth_(STROKE)
            path.setLineCapStyle_(appkit.NSRoundLineCapStyle)
            path.setLineJoinStyle_(appkit.NSRoundLineJoinStyle)
            path.stroke()
    finally:
        appkit.NSGraphicsContext.restoreGraphicsState()

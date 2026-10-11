# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Visual V4 icon assets. Raster-free filled silhouettes with crisp AppKit paint."""
from dataclasses import dataclass

ICON_NAMES = (
    "folder", "folder-open", "file", "pnx", "test", "toml",
    "explorer", "search", "git", "branch", "commit", "sync",
    "run", "debug", "terminal", "settings", "problems", "output",
)
PALETTE = {
    "folder": "#E1BA79", "folder-open": "#ECC88A",
    "file": "#B5C5D8", "pnx": "#7ABCF1", "test": "#8BCFAE",
    "toml": "#C3A7F5", "muted": "#B0BCCE", "active": "#86C4FA",
}


def _color(appkit, hexcode):
    hexcode = hexcode.lstrip("#")
    return appkit.NSColor.colorWithCalibratedRed_green_blue_alpha_(
        *(int(hexcode[i:i+2], 16)/255 for i in (0, 2, 4)), 1)


def paint_asset(appkit, x, y, name, size=16, selected=False):
    """Paint an original filled icon; delegate controls to existing vector set."""
    if name not in ICON_NAMES:
        raise ValueError(f"Unknown V4 icon: {name}")
    if name not in {"folder", "folder-open", "file", "pnx", "test", "toml"}:
        from pynix_gui.ide_iconography import draw_icon
        tint = _color(appkit, PALETTE["active" if selected else "muted"])
        return draw_icon(appkit, x, y, name, tint, size)

    scale = size/16
    def point(u, v):
        return appkit.NSMakePoint(x+u*scale, y+v*scale)
    def shape(points, color, close=True):
        path = appkit.NSBezierPath.bezierPath()
        path.moveToPoint_(point(*points[0]))
        for u, v in points[1:]:
            path.lineToPoint_(point(u, v))
        if close:
            path.closePath()
        _color(appkit, color).setFill()
        path.fill()

    if name.startswith("folder"):
        # Two-layer folder silhouette: clean tab and deliberately broader body.
        fill = PALETTE[name]
        shape([(1,4), (6.2,4), (7.8,5.7), (15,5.7),
               (15,13.7), (1,13.7)], fill)
        shape([(1,3), (6.5,3), (8,5.5), (1,5.5)], "#C99B57")
        if name == "folder-open":
            shape([(2,7), (15.7,7), (13.6,14.5), (0.8,14.5)],
                  "#F0CC90")
        return

    tint = PALETTE[name]
    # A solid document sheet and distinct inset/brand mark, not a wireframe.
    shape([(3,1.3), (10.2,1.3), (13.7,4.8), (13.7,15),
           (3,15)], tint)
    shape([(10.2,1.4), (10.2,4.9), (13.7,4.9)], "#51627A")
    if name == "pnx":
        shape([(6.4,7.5), (4.8,9.3), (6.4,11.1),
               (7.2,10.3), (6.4,9.3), (7.2,8.3)], "#192432")
        shape([(10.3,7.5), (11.9,9.3), (10.3,11.1),
               (9.5,10.3), (10.3,9.3), (9.5,8.3)], "#192432")
    elif name == "test":
        shape([(5,9.5), (7,11.2), (11.5,6.7),
               (12.4,7.5), (7,13), (4.2,10.3)], "#24364A")
    elif name == "toml":
        shape([(5.1,7.2),(11.4,7.2),(11.4,8.2),(5.1,8.2)], "#25334A")
        shape([(5.1,9.7),(10,9.7),(10,10.7),(5.1,10.7)], "#25334A")
    else:
        shape([(5.1,7.3),(11.1,7.3),(11.1,8.2),(5.1,8.2)], "#25334A")
        shape([(5.1,9.7),(10.2,9.7),(10.2,10.6),(5.1,10.6)], "#25334A")

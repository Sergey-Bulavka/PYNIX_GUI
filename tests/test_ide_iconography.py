# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui.ide_iconography import GRID, STROKE, ICONS, draw_icon


def test_icon_vocabulary_covers_ide_shell():
    assert GRID == 20
    assert 1.4 <= STROKE <= 1.8
    assert {"explorer", "search", "run", "debug", "settings",
            "terminal", "folder", "folder-open", "file", "pnx",
            "chevron-right", "chevron-down", "close", "more",
            "problems", "output", "split", "panel"} <= ICONS.keys()


@pytest.mark.parametrize("name", sorted(ICONS))
def test_icon_geometry_is_within_20px_grid(name):
    for primitive in ICONS[name]:
        assert primitive[0] in {"line", "poly", "rect", "circle", "dot"}
        if primitive[0] == "line":
            assert all(0 <= v <= GRID for v in primitive[1:])
        elif primitive[0] == "poly":
            assert len(primitive[1]) >= 2
            assert all(0 <= x <= GRID and 0 <= y <= GRID for x, y in primitive[1])
        elif primitive[0] == "rect":
            _, x, y, w, h, radius = primitive
            assert 0 <= x <= GRID and 0 <= y <= GRID
            assert w > 0 and h > 0 and radius >= 0
            assert x+w <= GRID and y+h <= GRID
        else:
            _, x, y, radius = primitive
            assert radius > 0
            assert 0 <= x-radius and x+radius <= GRID
            assert 0 <= y-radius and y+radius <= GRID


def test_unknown_icon_rejected_without_appkit():
    with pytest.raises(ValueError, match="unknown IDE icon"):
        draw_icon(None, 0, 0, "not-an-icon", None)


def test_vector_painter_executes_without_graphics_context_selectors():
    class Path:
        def moveToPoint_(self, value): pass
        def lineToPoint_(self, value): pass
        def closePath(self): pass
        def transformUsingAffineTransform_(self, value): pass
        def setLineWidth_(self, value): pass
        def stroke(self): pass
        def fill(self): pass

    class Bezier:
        @staticmethod
        def bezierPath(): return Path()
        @staticmethod
        def bezierPathWithRoundedRect_xRadius_yRadius_(*args): return Path()
        @staticmethod
        def bezierPathWithOvalInRect_(*args): return Path()

    class Transform:
        @staticmethod
        def transform(): return Transform()
        def translateXBy_yBy_(self, x, y): pass
        def scaleBy_(self, size): pass

    class FakeAppKit:
        NSBezierPath = Bezier
        NSAffineTransform = Transform
        NSMakePoint = staticmethod(lambda x, y: (x, y))
        NSMakeRect = staticmethod(lambda x, y, w, h: (x, y, w, h))

    class Color:
        def setStroke(self): pass
        def setFill(self): pass

    for name in ICONS:
        draw_icon(FakeAppKit, 10, 20, name, Color(), 18)


def test_folder_silhouettes_are_filled_but_document_code_detail_remains_visible():
    from pynix_gui.ide_iconography import FILLED_KINDS
    assert {"folder", "folder-open"} <= FILLED_KINDS
    assert "pnx" not in FILLED_KINDS
    assert "file" not in FILLED_KINDS

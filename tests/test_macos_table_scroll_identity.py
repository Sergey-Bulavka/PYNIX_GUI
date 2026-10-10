# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for stable semantic table identities during rerender."""

from pynix_gui import column, table, table_column, table_row
from pynix_gui.backends.macos import MacOSGUIBackend


def _screen(names):
    return column([
        table(
            "project-files",
            [table_column("name", "Name", 260)],
            [table_row(name, [name]) for name in names],
            selected_id=names[0] if names else None,
        ),
    ])


def test_table_identity_ignores_selection_but_not_listing():
    before = _screen(["a", "b"])
    after = _screen(["a", "b"])
    replaced = _screen(["c", "d"])
    ids = MacOSGUIBackend._table_id_sequences
    assert ids(before) == ids(after)
    assert ids(before) != ids(replaced)
    assert ids(before)["project-files"] == ("a", "b")


def test_table_identity_changes_when_rows_reorder():
    ids = MacOSGUIBackend._table_id_sequences
    assert ids(_screen(["a", "b"])) != ids(_screen(["b", "a"]))


class _Point:
    def __init__(self, x, y):
        self.x, self.y = x, y


class _Size:
    def __init__(self, width, height):
        self.width, self.height = width, height


class _Rect:
    def __init__(self, x=0, y=0, width=200, height=100):
        self.origin = _Point(x, y)
        self.size = _Size(width, height)


class _Clip:
    def __init__(self, y=0):
        self.rect = _Rect(y=y)
        self.calls = []

    def bounds(self):
        return self.rect

    def scrollToPoint_(self, point):
        self.calls.append(point)
        self.rect.origin = point


class _Native:
    def __init__(self, y):
        self.clip = _Clip(y)
        self.doc = type("Document", (), {"frame": lambda self: _Rect(width=200, height=1000)})()
        self.reflections = 0

    def contentView(self):
        return self.clip

    def documentView(self):
        return self.doc

    def reflectScrolledClipView_(self, clip):
        self.reflections += 1


class _BackendHarness:
    _table_id_sequences = staticmethod(MacOSGUIBackend._table_id_sequences)
    _capture_table_scroll = MacOSGUIBackend._capture_table_scroll
    _restore_table_scroll = MacOSGUIBackend._restore_table_scroll

    def __init__(self, previous, native):
        self._gui_views_by_window = {"window": previous}
        self._gui_controls_by_window = {"window": {"project-files": native}}

    @staticmethod
    def _load_appkit():
        return type("FakeAppKit", (), {"NSMakePoint": staticmethod(_Point)})


def test_capture_scroll_on_same_rows_across_selection_rerender():
    native = _Native(420)
    backend = _BackendHarness(_screen(["a", "b"]), native)
    assert backend._capture_table_scroll("window", _screen(["a", "b"])) == {
        "project-files": (0.0, 420.0)
    }
    assert backend._capture_table_scroll("window", _screen(["b", "a"])) == {}


def test_restore_scroll_clamps_outside_document():
    native = _Native(0)
    backend = _BackendHarness(_screen(["a"]), native)
    backend._restore_table_scroll("window", {"project-files": (2000, 1200)})
    assert len(native.clip.calls) == 1
    assert native.clip.calls[0].x == 0.0
    assert native.clip.calls[0].y == 900.0
    assert native.reflections == 1

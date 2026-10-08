# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import (
    GUIError,
    GUIEvent,
    layout,
    measure,
    rich_editor,
    text_span,
    validate_view,
)
from pynix_gui.backends import MacOSGUIBackend


SOURCE = "fn main() {\n    let answer = 42\n}\n"


def spans():
    return [
        text_span(0, 2, "keyword"),
        text_span(3, 7, "function"),
        text_span(17, 20, "keyword"),
        text_span(30, 32, "number"),
    ]


def test_adv05_editor_state_is_controlled_and_language_agnostic():
    view = rich_editor(
        "source",
        SOURCE,
        3,
        7,
        spans(),
    )

    assert view.value == SOURCE
    assert view.selection_start == 3
    assert view.selection_end == 7
    assert view.read_only is False
    validate_view(view)


def test_adv05_editor_rejects_selection_outside_text():
    with pytest.raises(GUIError) as failure:
        rich_editor("source", "abc", 0, 4)

    assert failure.value.code == "PYNIX-GUI-012"


def test_adv05_editor_rejects_overlapping_spans():
    with pytest.raises(GUIError):
        rich_editor(
            "source",
            "abcdef",
            0,
            0,
            [
                text_span(0, 4, "keyword"),
                text_span(3, 5, "string"),
            ],
        )


def test_adv05_editor_rejects_span_beyond_text():
    with pytest.raises(GUIError):
        rich_editor(
            "source",
            "abc",
            0,
            0,
            [text_span(0, 4, "keyword")],
        )


def test_adv05_editor_has_professional_intrinsic_geometry():
    constraints = measure(rich_editor("source", SOURCE, 0, 0, spans()))

    assert constraints.minimum.width == 240
    assert constraints.minimum.height == 160
    assert constraints.preferred.width == 640
    assert constraints.preferred.height == 420


def test_adv05_editor_layout_is_single_native_control():
    calculated = layout(
        rich_editor("source", SOURCE, 0, 0, spans()),
        900,
        600,
    )

    assert calculated.rect.width == 900
    assert calculated.rect.height == 600
    assert calculated.children == ()


def test_adv05_editor_selection_event_has_exact_range():
    event = GUIEvent(
        "EDITOR_SELECTION",
        target="source",
        selection_start=5,
        selection_end=12,
    )

    assert event.selection_start == 5
    assert event.selection_end == 12


def test_adv05_editor_selection_event_rejects_reversed_range():
    with pytest.raises(GUIError):
        GUIEvent(
            "EDITOR_SELECTION",
            target="source",
            selection_start=8,
            selection_end=3,
        )


def test_adv05_backend_normalizes_native_selection_range():
    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    window = object()

    class Sender:
        def selectedRange(self):
            return type("Range", (), {"location": 4, "length": 6})()

    sender = Sender()
    backend._gui_control_meta_by_window[window] = {
        sender: ("richEditor", "source"),
    }

    backend._queue_editor_selection(window, sender)
    event = backend._event_queue(window).popleft()

    assert event == GUIEvent(
        "EDITOR_SELECTION",
        target="source",
        selection_start=4,
        selection_end=10,
    )


def test_adv05_backend_normalizes_rich_editor_text_change():
    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    window = object()

    class Sender:
        def string(self):
            return "line1\r\nline2"

    sender = Sender()
    backend._gui_control_meta_by_window[window] = {
        sender: ("richEditor", "source"),
    }

    sender.selectedRange = lambda: type(
        "Range",
        (),
        {"location": 5, "length": 0},
    )()

    backend._queue_text_change(window, sender)
    selection = backend._event_queue(window).popleft()
    change = backend._event_queue(window).popleft()

    assert selection == GUIEvent(
        "EDITOR_SELECTION",
        target="source",
        selection_start=5,
        selection_end=5,
    )
    assert change == GUIEvent(
        "CHANGE",
        target="source",
        text="line1\nline2",
    )


def test_adv05_read_only_is_explicit_controlled_state():
    view = rich_editor(
        "log",
        "build complete",
        0,
        0,
        read_only=True,
    )

    assert view.read_only is True

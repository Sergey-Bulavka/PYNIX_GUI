# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui.core import GUIError, GUIEvent, button, empty
from pynix_gui.runtime import GUIRuntime, GUIRuntimeState


class FakeBackend:
    def __init__(self):
        self.available = True
        self.opened = []
        self.rendered = []
        self.events = []
        self.closed = []

    def is_available(self):
        return self.available

    def open(self, title, width, height):
        handle = object()
        self.opened.append((title, width, height, handle))
        return handle

    def render(self, handle, view):
        self.rendered.append((handle, view))

    def next_event(self, handle):
        if not self.events:
            return GUIEvent("CLOSE")
        return self.events.pop(0)

    def close(self, handle):
        self.closed.append(handle)


def test_runtime_capability_probe_and_unavailable_open():
    runtime = GUIRuntime(None)
    assert runtime.is_available() is False

    with pytest.raises(GUIError) as failure:
        runtime.open("Window", 640, 480)
    assert failure.value.code == "PYNIX-GUI-001"


def test_runtime_open_validates_title_and_dimensions():
    runtime = GUIRuntime(FakeBackend())

    with pytest.raises(GUIError) as failure:
        runtime.open(123, 640, 480)
    assert failure.value.code == "PYNIX-GUI-002"

    with pytest.raises(GUIError):
        runtime.open("Window", 0, 480)

    with pytest.raises(GUIError):
        runtime.open("Window", 640, -1)


def test_runtime_open_render_event_close_complete_lifecycle():
    backend = FakeBackend()
    runtime = GUIRuntime(backend)

    window = runtime.open("PYNIX", 800, 600)
    root = button("save", "Save")
    window.render(root)

    backend.events.append(GUIEvent("ACTIVATE", target="save"))
    event = window.next_event()

    assert event == GUIEvent("ACTIVATE", target="save")
    assert len(backend.rendered) == 1

    window.close()
    assert window.closed is True
    assert runtime.state.window is None
    assert len(backend.closed) == 1


def test_runtime_rejects_second_live_window_but_allows_new_after_close():
    backend = FakeBackend()
    runtime = GUIRuntime(backend)

    first = runtime.open("One", 400, 300)

    with pytest.raises(GUIError) as failure:
        runtime.open("Two", 400, 300)
    assert failure.value.code == "PYNIX-GUI-002"

    first.close()
    second = runtime.open("Two", 400, 300)
    assert second.closed is False


def test_window_close_is_idempotent():
    backend = FakeBackend()
    runtime = GUIRuntime(backend)
    window = runtime.open("Window", 400, 300)

    window.close()
    window.close()

    assert len(backend.closed) == 1


def test_closed_window_rejects_render_and_event_processing():
    backend = FakeBackend()
    runtime = GUIRuntime(backend)
    window = runtime.open("Window", 400, 300)
    window.close()

    with pytest.raises(GUIError) as render_failure:
        window.render(empty())
    assert render_failure.value.code == "PYNIX-GUI-002"

    with pytest.raises(GUIError) as event_failure:
        window.next_event()
    assert event_failure.value.code == "PYNIX-GUI-002"


def test_backend_failures_are_normalized_to_gui_diagnostics():
    class BrokenBackend(FakeBackend):
        def render(self, handle, view):
            raise RuntimeError("boom")

        def next_event(self, handle):
            raise RuntimeError("boom")

        def close(self, handle):
            raise RuntimeError("boom")

    runtime = GUIRuntime(BrokenBackend())
    window = runtime.open("Window", 400, 300)

    with pytest.raises(GUIError) as render_failure:
        window.render(empty())
    assert render_failure.value.code == "PYNIX-GUI-003"

    with pytest.raises(GUIError) as event_failure:
        window.next_event()
    assert event_failure.value.code == "PYNIX-GUI-004"

    with pytest.raises(GUIError) as close_failure:
        window.close()
    assert close_failure.value.code == "PYNIX-GUI-002"
    assert window.closed is False


def test_runtime_state_can_be_supplied_explicitly():
    state = GUIRuntimeState()
    backend = FakeBackend()
    runtime = GUIRuntime(backend, state=state)

    window = runtime.open("Window", 400, 300)

    assert state.window is window

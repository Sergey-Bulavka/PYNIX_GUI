# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from collections import deque

from pynix_gui.core import GUIEvent
from pynix_gui.backends._macos_host import MacOSHostBackend


class Event:
    def __init__(self, kind):
        self.kind = kind
    def type(self):
        return self.kind


class App:
    def __init__(self, backend, window, handled):
        self.backend = backend
        self.window = window
        self.handled = handled
        self.sent = []
        self.seen = []
    def nextEventMatchingMask_untilDate_inMode_dequeue_(self, *args):
        return Event(10)
    def mainMenu(self):
        return self
    def performKeyEquivalent_(self, event):
        self.seen.append(event)
        if self.handled:
            self.backend._event_queue(self.window).append(
                GUIEvent("ACTIVATE", target="nav-overview")
            )
        return self.handled
    def sendEvent_(self, event):
        self.sent.append(event)
        self.backend._event_queue(self.window).append(
            GUIEvent("ACTIVATE", target="native-control")
        )
    def updateWindows(self):
        pass


def test_manual_appkit_loop_routes_menu_shortcut_before_window():
    backend = MacOSHostBackend(platform_name="darwin")
    window = object()
    app = App(backend, window, True)
    backend._appkit_override = SimpleNamespace(
        NSApplication=SimpleNamespace(sharedApplication=lambda: app),
        NSEventMaskAny=1,
        NSEventTypeKeyDown=10,
        NSDate=SimpleNamespace(distantFuture=lambda: None),
        NSDefaultRunLoopMode="default",
    )
    assert backend.next_event(window) == GUIEvent("ACTIVATE", target="nav-overview")
    assert len(app.seen) == 1
    assert app.sent == []


def test_unhandled_shortcut_reaches_native_control():
    backend = MacOSHostBackend(platform_name="darwin")
    window = object()
    app = App(backend, window, False)
    backend._appkit_override = SimpleNamespace(
        NSApplication=SimpleNamespace(sharedApplication=lambda: app),
        NSEventMaskAny=1,
        NSEventTypeKeyDown=10,
        NSDate=SimpleNamespace(distantFuture=lambda: None),
        NSDefaultRunLoopMode="default",
    )
    assert backend.next_event(window) == GUIEvent("ACTIVATE", target="native-control")
    assert len(app.sent) == 1

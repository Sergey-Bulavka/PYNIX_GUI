# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Minimal Cocoa host boundary shared by the standalone macOS GUI backend."""

from __future__ import annotations

from collections import deque
import sys

from ..core import GUIEvent


class MacOSHostBackend:
    """Own AppKit loading, window lifecycle, and normalized event queue mechanics."""

    __slots__ = (
        "platform_name",
        "_appkit_override",
        "_bridges_by_window",
        "_event_queues_by_window",
    )

    def __init__(self, *, platform_name=None, appkit=None):
        self.platform_name = sys.platform if platform_name is None else platform_name
        self._appkit_override = appkit
        self._bridges_by_window = {}
        self._event_queues_by_window = {}

    def _load_appkit(self):
        if self._appkit_override is not None:
            return self._appkit_override

        if self.platform_name != "darwin":
            return None

        try:
            import AppKit
        except Exception:
            return None

        return AppKit

    def is_available(self) -> bool:
        if self.platform_name != "darwin":
            return False

        appkit = self._load_appkit()
        if appkit is None:
            return False

        try:
            return appkit.NSThread.isMainThread() is True
        except Exception:
            return False

    def open(self, title, width, height):
        appkit = self._load_appkit()
        if appkit is None:
            raise OSError("Cocoa GUI backend is unavailable.")

        application = appkit.NSApplication.sharedApplication()
        application.setActivationPolicy_(
            appkit.NSApplicationActivationPolicyRegular
        )

        style = (
            appkit.NSWindowStyleMaskTitled
            | appkit.NSWindowStyleMaskClosable
            | appkit.NSWindowStyleMaskMiniaturizable
            | appkit.NSWindowStyleMaskResizable
        )
        rect = appkit.NSMakeRect(0, 0, width, height)

        window = (
            appkit.NSWindow.alloc()
            .initWithContentRect_styleMask_backing_defer_(
                rect,
                style,
                appkit.NSBackingStoreBuffered,
                False,
            )
        )
        if window is None:
            raise OSError("Cocoa failed to create a GUI window.")

        window.setTitle_(title)
        window.center()
        window.makeKeyAndOrderFront_(None)
        application.activateIgnoringOtherApps_(True)
        return window

    def _event_queue(self, window):
        return self._event_queues_by_window.setdefault(window, deque())

    def _queue_close(self, window):
        self._event_queue(window).append(GUIEvent("CLOSE"))

    def next_event(self, window):
        queue = self._event_queue(window)
        if queue:
            return queue.popleft()

        appkit = self._load_appkit()
        if appkit is None:
            raise OSError("Cocoa GUI backend is unavailable.")

        application = appkit.NSApplication.sharedApplication()

        while not queue:
            native_event = (
                application
                .nextEventMatchingMask_untilDate_inMode_dequeue_(
                    appkit.NSEventMaskAny,
                    appkit.NSDate.distantFuture(),
                    appkit.NSDefaultRunLoopMode,
                    True,
                )
            )

            if native_event is None:
                continue

            # This host drives AppKit's event loop manually. Explicitly offer
            # key-down events to the application menu before window dispatch:
            # without an NSApplication.run() loop, platform menu equivalents
            # must not depend on implicit key routing by the active window.
            handled_by_menu = False
            if (
                hasattr(native_event, "type")
                and native_event.type() == getattr(appkit, "NSEventTypeKeyDown", 10)
            ):
                main_menu = application.mainMenu()
                if main_menu is not None:
                    handled_by_menu = bool(
                        main_menu.performKeyEquivalent_(native_event)
                    )
            if not handled_by_menu:
                application.sendEvent_(native_event)
            application.updateWindows()

        return queue.popleft()

    def close(self, window):
        bridge = self._bridges_by_window.get(window)
        detached_bridge = False

        if (
            bridge is not None
            and hasattr(window, "delegate")
            and hasattr(window, "setDelegate_")
            and window.delegate() is bridge
        ):
            window.setDelegate_(None)
            detached_bridge = True

        try:
            window.close()
        except Exception:
            if detached_bridge:
                window.setDelegate_(bridge)
            raise

        self._bridges_by_window.pop(window, None)
        self._event_queues_by_window.pop(window, None)

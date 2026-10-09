# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

from pynix_gui import GUIEvent, GUIRuntime, button
from pynix_gui.backends import MacOSGUIBackend


class FakeThread:
    @staticmethod
    def isMainThread():
        return True


class FakeApplication:
    def __init__(self):
        self.activation_policy = None
        self.activated = False

    def setActivationPolicy_(self, value):
        self.activation_policy = value

    def activateIgnoringOtherApps_(self, value):
        self.activated = value


class FakeApplicationType:
    instance = FakeApplication()

    @classmethod
    def sharedApplication(cls):
        return cls.instance


class FakeWindow:
    def __init__(self):
        self.title = None
        self.closed = False
        self.delegate_value = None
        self.content_views = []

    def setTitle_(self, value):
        self.title = value

    def center(self):
        pass

    def makeKeyAndOrderFront_(self, value):
        pass

    def close(self):
        self.closed = True

    def delegate(self):
        return self.delegate_value

    def setDelegate_(self, value):
        self.delegate_value = value

    def setContentView_(self, value):
        self.content_views.append(value)

    def firstResponder(self):
        return getattr(self, "first_responder", None)

    def makeFirstResponder_(self, value):
        self.first_responder = value
        return True


class FakeWindowAllocator:
    def initWithContentRect_styleMask_backing_defer_(self, rect, style, backing, defer):
        return FakeWindow()


class FakeWindowType:
    @classmethod
    def alloc(cls):
        return FakeWindowAllocator()


def fake_host_appkit():
    return SimpleNamespace(
        NSThread=FakeThread,
        NSApplication=FakeApplicationType,
        NSApplicationActivationPolicyRegular=1,
        NSWindowStyleMaskTitled=1,
        NSWindowStyleMaskClosable=2,
        NSWindowStyleMaskMiniaturizable=4,
        NSWindowStyleMaskResizable=8,
        NSBackingStoreBuffered=2,
        NSWindow=FakeWindowType,
        NSMakeRect=lambda x, y, width, height: (x, y, width, height),
    )


def test_macos_backend_is_standalone_and_available_with_fake_appkit():
    backend = MacOSGUIBackend(platform_name="darwin", appkit=fake_host_appkit())
    assert backend.is_available() is True


def test_macos_backend_open_is_consumable_by_standalone_runtime():
    backend = MacOSGUIBackend(platform_name="darwin", appkit=fake_host_appkit())
    runtime = GUIRuntime(backend)

    window = runtime.open("PYNIX GUI", 800, 600)

    assert window._handle.title == "PYNIX GUI"
    assert window.closed is False


def test_macos_host_close_event_is_native_gui_event():
    backend = MacOSGUIBackend(platform_name="darwin", appkit=fake_host_appkit())
    native_window = FakeWindow()

    backend._queue_close(native_window)

    assert backend.next_event(native_window) == GUIEvent("CLOSE")


def test_macos_runtime_close_uses_standalone_host_boundary():
    backend = MacOSGUIBackend(platform_name="darwin", appkit=fake_host_appkit())
    runtime = GUIRuntime(backend)
    window = runtime.open("PYNIX GUI", 800, 600)
    native = window._handle

    window.close()

    assert native.closed is True
    assert window.closed is True
    assert runtime.state.window is None


def test_macos_backend_module_has_no_compiler_or_desktop_dependency():
    assert MacOSGUIBackend.__module__ == "pynix_gui.backends.macos"
    assert all("compiler" not in cls.__module__ for cls in MacOSGUIBackend.__mro__)
    assert all("desktop" not in cls.__module__ for cls in MacOSGUIBackend.__mro__)


def test_macos_backend_preserves_rich_editor_focus_across_rerender():
    backend = MacOSGUIBackend(platform_name="darwin", appkit=fake_host_appkit())
    window = FakeWindow()
    old_editor = object()
    new_editor = object()

    backend._gui_control_meta_by_window[window] = {
        old_editor: ("richEditor", "source-editor"),
    }
    backend._gui_controls_by_window[window] = {
        "source-editor": old_editor,
    }
    window.first_responder = old_editor

    previous = backend._capture_focus(window)

    backend._gui_controls_by_window[window] = {
        "source-editor": new_editor,
    }
    backend._gui_control_meta_by_window[window] = {
        new_editor: ("richEditor", "source-editor"),
    }
    backend._restore_focus(window, None, previous)

    assert previous == ("control", "source-editor", None)
    assert window.first_responder is new_editor

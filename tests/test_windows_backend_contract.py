# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from pynix_gui.backends import (
    MacOSGUIBackend,
    WindowsGUIBackend,
    default_backend,
)


def test_default_backend_selects_macos_without_importing_windows_runtime():
    backend = default_backend(platform_name="darwin")
    assert isinstance(backend, MacOSGUIBackend)


def test_default_backend_selects_windows_without_importing_qt_eagerly():
    backend = default_backend(platform_name="win32")
    assert isinstance(backend, WindowsGUIBackend)
    assert backend.platform_name == "win32"


def test_default_backend_returns_none_for_unimplemented_linux_backend():
    assert default_backend(platform_name="linux") is None


def test_windows_backend_is_unavailable_off_windows():
    backend = WindowsGUIBackend(platform_name="darwin")
    assert backend.is_available() is False

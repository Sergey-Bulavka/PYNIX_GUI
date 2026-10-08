# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Platform backends for PYNIX GUI."""

import sys

from .macos import MacOSGUIBackend
from .windows import WindowsGUIBackend


def default_backend(*, platform_name=None):
    platform = sys.platform if platform_name is None else platform_name
    if platform == "darwin":
        return MacOSGUIBackend(platform_name=platform)
    if platform == "win32":
        return WindowsGUIBackend(platform_name=platform)
    return None


__all__ = [
    "MacOSGUIBackend",
    "WindowsGUIBackend",
    "default_backend",
]

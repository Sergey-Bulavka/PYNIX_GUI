# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Native macOS V4 design review window, displaying the approved SVG assets.

Unlike the older AppKit canvas, WKWebView renders the original Lucide/Octicons
SVG markup. This remains a visual acceptance prototype, not the IDE backend.

Run: python -m examples.ide_native_v4
"""
from __future__ import annotations

import sys
from pathlib import Path

PREVIEW_PATH = Path(__file__).with_name("icon_direction_preview.html")


def main() -> None:
    if sys.platform != "darwin":
        raise SystemExit("V4 native review requires macOS")
    if not PREVIEW_PATH.is_file():
        raise SystemExit(f"Missing V4 preview: {PREVIEW_PATH}")

    import AppKit
    import WebKit
    from Foundation import NSObject, NSURL

    class PreviewDelegate(NSObject):
        def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
            return True

    app = AppKit.NSApplication.sharedApplication()
    delegate = PreviewDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)

    window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        AppKit.NSMakeRect(90, 75, 1500, 950),
        AppKit.NSWindowStyleMaskTitled
        | AppKit.NSWindowStyleMaskClosable
        | AppKit.NSWindowStyleMaskMiniaturizable
        | AppKit.NSWindowStyleMaskResizable,
        AppKit.NSBackingStoreBuffered,
        False,
    )
    window.setTitle_("PYNIX IDE — Visual Shell V4")
    window.setMinSize_(AppKit.NSMakeSize(1030, 680))

    view = WebKit.WKWebView.alloc().initWithFrame_(window.contentView().bounds())
    view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
    url = NSURL.fileURLWithPath_(str(PREVIEW_PATH.resolve()))
    # Explicit local access scope; no network URLs or Git operations required.
    view.loadFileURL_allowingReadAccessToURL_(url, url.URLByDeletingLastPathComponent())
    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)
    app.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == "__main__":
    main()

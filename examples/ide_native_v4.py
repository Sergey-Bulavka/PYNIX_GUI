# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Native macOS V4 workspace window, displaying the approved SVG assets.

Unlike the older AppKit canvas, WKWebView renders the original Lucide/Octicons
SVG markup. This remains a visual acceptance prototype, not the IDE backend.

Run: python -m examples.ide_native_v4
"""
from __future__ import annotations

import sys
import argparse
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

    class FirstClickWebView(WebKit.WKWebView):
        """Forward the first click even when the macOS window is inactive."""

        def acceptsFirstMouse_(self, event):
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
    window.setTitle_("PYNIX IDE — Workspace V4")
    window.setMinSize_(AppKit.NSMakeSize(1030, 680))

    view = FirstClickWebView.alloc().initWithFrame_(window.contentView().bounds())
    view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
    url = NSURL.fileURLWithPath_(str(PREVIEW_PATH.resolve()))
    # Reuse the same approved vector artwork, but display a full-size IDE workspace
    # instead of a miniature IDE embedded inside the icon gallery.
    parser = argparse.ArgumentParser(description="PYNIX IDE V4 preview")
    parser.add_argument("--project", type=Path, help="Read-only source project to explore")
    args = parser.parse_args()
    document = PREVIEW_PATH.read_text(encoding="utf-8")
    document = document.replace("<body>", '<body class="workspace-mode">', 1)
    if args.project is not None:
        from pynix_gui.ide_workspace_session import WorkspaceSession
        from pynix_gui.ide_workspace_preview import attach_workspace, attach_git_snapshot
        from pynix_gui.ide_git_snapshot import read_git_snapshot
        session = WorkspaceSession(args.project)
        document = attach_workspace(document, session)
        document = attach_git_snapshot(document, read_git_snapshot(session.root))
    view.loadHTMLString_baseURL_(document, url.URLByDeletingLastPathComponent())
    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)
    window.makeFirstResponder_(view)
    app.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == "__main__":
    main()

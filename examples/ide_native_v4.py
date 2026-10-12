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
    from pynix_gui.ide_navigation_bridge import (
        attach_navigation_controls, validate_request, result_script,
    )

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
    parser.add_argument("--diagnostics", action="store_true", help="Read PYNIX compiler diagnostics on startup")
    parser.add_argument("--compiler-python", type=Path, help="Interpreter with the PYNIX compiler installed")
    parser.add_argument("--nav-command", choices=("definition", "references", "type-at"))
    parser.add_argument("--nav-source", help="Relative .pnx path for navigation")
    parser.add_argument("--nav-line", type=int, default=1)
    parser.add_argument("--nav-column", type=int, default=1)
    args = parser.parse_args()
    document = PREVIEW_PATH.read_text(encoding="utf-8")
    document = document.replace("<body>", '<body class="workspace-mode">', 1)
    project_path = args.project
    if project_path is None:
        candidate = PREVIEW_PATH.resolve().parents[2] / "PYNIX"
        if candidate.is_dir():
            project_path = candidate
        else:
            raise SystemExit("No project selected. Run with --project /path/to/PYNIX")
    if project_path is not None:
        from pynix_gui.ide_workspace_session import WorkspaceSession
        from pynix_gui.ide_workspace_preview import attach_workspace, attach_git_snapshot
        from pynix_gui.ide_git_snapshot import read_git_snapshot
        session = WorkspaceSession(project_path)
        document = attach_workspace(document, session)
        document = attach_git_snapshot(document, read_git_snapshot(session.root))
        if args.diagnostics:
            from pynix_gui.ide_tooling_diagnostics import read_diagnostics
            from pynix_gui.ide_workspace_preview import attach_diagnostics
            compiler_python = args.compiler_python or (session.root / ".venv" / "bin" / "python")
            document = attach_diagnostics(document, read_diagnostics(session.root, compiler_python))
        if args.nav_command:
            if not args.nav_source:
                parser.error("--nav-command requires --nav-source")
            from pynix_gui.ide_tooling_navigation import query_navigation
            from pynix_gui.ide_workspace_preview import attach_navigation
            compiler_python = args.compiler_python or (session.root / ".venv" / "bin" / "python")
            result = query_navigation(session.root, compiler_python, args.nav_command,
                                      args.nav_source, args.nav_line, args.nav_column)
            document = attach_navigation(document, result, args.nav_command)
    from pynix_gui.ide_tooling_navigation import query_navigation
    compiler_python = args.compiler_python or (session.root / ".venv" / "bin" / "python")
    available_sources = set(session.list_files(limit=5000))
    class NavigationHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            try:
                command, source, line, column = validate_request(
                    dict(message.body()), available_sources)
                result = query_navigation(session.root, compiler_python, command,
                                          source, line, column)
            except (ValueError, TypeError) as exc:
                command = "definition"
                result = {"error": str(exc)}
            view.evaluateJavaScript_completionHandler_(
                result_script(result, command), None)

    class FileOpenHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            from pynix_gui.ide_syntax_highlight import highlight_document
            request = message.body()
            source = request.get("source") if isinstance(request, dict) else None
            response = {"source": source}
            try:
                if not isinstance(source, str) or source not in available_sources:
                    raise ValueError("File is not part of the indexed project")
                file_path = session.resolve_file(source)
                if file_path.stat().st_size > 1_000_000:
                    raise ValueError("File is too large for this preview")
                text = file_path.read_text(encoding="utf-8")
                response["text"] = text
                response["tokens"] = highlight_document(text) if source.endswith(".pnx") else None
            except (OSError, UnicodeError, ValueError) as error:
                response["error"] = str(error)
            serialized = json.dumps(response, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixReceiveFile(" + serialized + ");", None)

    file_open_handler = FileOpenHandler.alloc().init()
    navigation_handler = NavigationHandler.alloc().init()
    controller = view.configuration().userContentController()
    controller.addScriptMessageHandler_name_(navigation_handler, "pynixNavigation")
    controller.addScriptMessageHandler_name_(file_open_handler, "pynixFileOpen")
    document = attach_navigation_controls(document)
    view.loadHTMLString_baseURL_(document, url.URLByDeletingLastPathComponent())
    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)
    window.makeFirstResponder_(view)
    app.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == "__main__":
    main()

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
        attach_navigation_controls, normalize_webkit_request, validate_request, result_script,
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
    parser.add_argument("--project", type=Path, help="Source project to explore")
    parser.add_argument("--ide-core", type=Path, help="Official PYNIX_IDE checkout for read-only Core snapshot")
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
    from pynix_gui.ide_core_read_bridge import CoreSnapshotError
    core_reader = None
    if args.ide_core:
        from pynix_gui.ide_core_persistent import PersistentCoreReader
        from html import escape
        compiler_for_core = args.compiler_python or (session.root / ".venv" / "bin" / "python")
        try:
            core_reader = PersistentCoreReader(args.ide_core, session.root, compiler_for_core)
            core_snapshot = core_reader.start()
            core_status = "IDE Core: connected (persistent, buffer sync)"
        except (CoreSnapshotError, OSError) as exc:
            core_reader = None
            core_status = "IDE Core: " + str(exc)[:180]
        indicator = '<div class="pynix-core-bridge-indicator" role="status" style="position:fixed;right:16px;bottom:30px;z-index:9000;background:#1c2939;color:#e5effc;border:1px solid #496782;padding:5px 10px;border-radius:6px;font:12px system-ui">' + escape(core_status) + '</div>'
        document = document.replace("</body>", indicator + "</body>", 1)
    from pynix_gui.ide_tooling_navigation import query_navigation
    compiler_python = args.compiler_python or (session.root / ".venv" / "bin" / "python")
    available_sources = set(session.list_files(limit=5000))
    class NavigationHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            try:
                command, source, line, column = validate_request(
                    normalize_webkit_request(message.body()), available_sources)
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
            try:
                request = dict(request)
            except (TypeError, ValueError):
                request = {}
            source = request.get("source")
            response = {"source": source, "revision": request.get("revision")}
            try:
                if not isinstance(source, str) or source not in available_sources:
                    raise ValueError("File is not part of the indexed project")
                file_path = session.resolve_file(source)
                if file_path.stat().st_size > 1_000_000:
                    raise ValueError("File is too large for this preview")
                if core_reader is not None and source.endswith(".pnx"):
                    core_reader.open_source(source)
                    state = core_reader.read_source(source)
                    text = state["content"]
                    response["revision"] = state["revision"]
                    response["dirty"] = state["dirty"]
                    if state["dirty"]:
                        response["savedText"] = file_path.read_text(encoding="utf-8")
                else:
                    text = file_path.read_text(encoding="utf-8")
                response["text"] = text
                response["tokens"] = highlight_document(text) if source.endswith(".pnx") else None
            except (OSError, UnicodeError, ValueError, CoreSnapshotError) as error:
                response["error"] = str(error)
            serialized = json.dumps(response, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixReceiveFile(" + serialized + ");", None)

    class CoreBufferHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            if core_reader is None:
                return
            import json
            request = {}
            reply = {"source": None, "revision": None, "ok": False}
            try:
                request = dict(message.body())
                source = request.get("source")
                content = request.get("text")
                revision = request.get("revision")
                # WKWebView exposes JSON numbers as Objective-C NSNumber on macOS.
                # Normalize at the boundary, before Python-side strict int validation.
                if not isinstance(revision, bool) and hasattr(revision, "integerValue"):
                    whole = int(revision.integerValue())
                    if float(revision) == whole:
                        revision = whole
                reply.update(source=source, revision=revision)
                if not isinstance(source, str) or source not in available_sources:
                    raise ValueError("Unindexed source")
                core_reader.update_source(source, content, revision)
                state = core_reader.read_source(source)
                if state["revision"] != revision or state["content"] != content:
                    raise CoreSnapshotError("Core readback differs from editor revision")
                reply["dirty"] = state["dirty"]
                reply["ok"] = True
            except (CoreSnapshotError, ValueError, OSError, TypeError) as exc:
                reply["error"] = str(exc)[:180]
                print("IDE Core buffer mirror:", exc, file=sys.stderr)
            serialized = json.dumps(reply, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixCoreBufferResult(" + serialized + ");", None)

    class CoreRecoveryHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            result = {"ok": False}
            try:
                if core_reader is None:
                    raise CoreSnapshotError("IDE Core was not connected at startup")
                payload = dict(message.body())
                entries = payload.get("buffers")
                if not isinstance(entries, (list, tuple)):
                    raise ValueError("Invalid recovery request")
                buffers = []
                for entry in entries:
                    entry = dict(entry)
                    revision = entry.get("revision")
                    if not isinstance(revision, bool) and hasattr(revision, "integerValue"):
                        whole = int(revision.integerValue())
                        if float(revision) == whole:
                            revision = whole
                    buffers.append({"source": entry.get("source"),
                                    "content": entry.get("content"), "revision": revision})
                result.update(core_reader.restart_with_buffers(buffers))
                result["ok"] = True
            except (CoreSnapshotError, ValueError, OSError, TypeError) as exc:
                result["error"] = str(exc)[:180]
                print("IDE Core recovery:", exc, file=sys.stderr)
            serialized = json.dumps(result, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixCoreRecoveryResult(" + serialized + ");", None)

    class CoreCloseHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            request = dict(message.body())
            source = request.get("source")
            discard = request.get("discard") is True
            response = {"source": source, "closed": False}
            try:
                if not isinstance(source, str) or source not in available_sources:
                    raise ValueError("Unindexed source")
                if core_reader is not None and source.endswith(".pnx"):
                    if discard:
                        core_reader.discard_source(source)
                    if not core_reader.close_source(source):
                        raise CoreSnapshotError("IDE Core refused to close dirty document")
                response["closed"] = True
            except (CoreSnapshotError, ValueError, OSError, TypeError) as exc:
                response["error"] = str(exc)[:180]
                print("IDE Core close:", exc, file=sys.stderr)
            serialized = json.dumps(response, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixCoreCloseResult(" + serialized + ");", None)

    class CoreDiscardHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            if core_reader is None:
                return
            try:
                source = dict(message.body()).get("source")
                if not isinstance(source, str) or source not in available_sources:
                    raise ValueError("Unindexed source")
                core_reader.discard_source(source)
            except (CoreSnapshotError, ValueError, OSError, TypeError) as exc:
                print("IDE Core discard mirror:", exc, file=sys.stderr)

    class FileSaveHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            request = dict(message.body())
            source = request.get("source")
            content = request.get("text")
            response = {"source": source}
            try:
                if not isinstance(source, str) or source not in available_sources:
                    raise ValueError("Source is outside the indexed project")
                if not isinstance(content, str) or len(content.encode("utf-8")) > 1_000_000:
                    raise ValueError("Source content exceeds the editor limit")
                # Core is the authoritative in-memory buffer for .pnx saves.
                # Reconcile this exact revision before the V4 atomic disk write.
                if core_reader is not None and source.endswith(".pnx"):
                    revision = request.get("revision")
                    if not isinstance(revision, bool) and hasattr(revision, "integerValue"):
                        whole = int(revision.integerValue())
                        if float(revision) == whole:
                            revision = whole
                    core_reader.update_source(source, content, revision)
                    core_state = core_reader.read_source(source)
                    if (core_state["content"] != content
                            or core_state["revision"] != revision):
                        raise CoreSnapshotError("Core source diverged before save")
                # Preserve the session's original disk snapshot for conflict checks.
                if source not in session.documents:
                    session.open(source)
                session.update(source, content)
                session.save(source)
                response["saved"] = True
                response["savedText"] = content
                if core_reader is not None and source.endswith(".pnx"):
                    try:
                        core_reader.acknowledge_saved_source(source, content)
                    except CoreSnapshotError as exc:
                        print("IDE Core save baseline mirror:", exc, file=sys.stderr)
                from pynix_gui.ide_tooling_diagnostics import read_diagnostics
                snapshot = read_diagnostics(session.root, compiler_python)
                response["diagnostics"] = [
                    {"source": problem.source, "line": problem.line,
                     "column": problem.column, "code": problem.code,
                     "message": problem.message}
                    for problem in snapshot.problems
                ]
                response["diagnostic_error"] = snapshot.error
            except (OSError, UnicodeError, ValueError, CoreSnapshotError) as error:
                response["error"] = str(error)
            serialized = json.dumps(response, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixSaveResult(" + serialized + ");", None)

    class ProjectSearchHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            try:
                request = dict(message.body())
                query = request.get("query", "")
                if not isinstance(query, str) or not 0 < len(query) <= 200:
                    raise ValueError("Search query must be 1–200 characters")
                matches = []
                needle = query.casefold()
                for source in sorted(available_sources):
                    if len(matches) >= 300:
                        break
                    if not source.endswith((".pnx", ".py", ".html", ".css", ".js", ".json", ".md")):
                        continue
                    file_path = session.resolve_file(source)
                    if file_path.stat().st_size > 512_000:
                        continue
                    try:
                        content = file_path.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        continue
                    for lineno, line in enumerate(content.splitlines(), 1):
                        index = line.casefold().find(needle)
                        if index < 0:
                            continue
                        matches.append({"source": source, "line": lineno, "column": index + 1,
                                        "preview": line.strip()[:180]})
                        if len(matches) >= 300:
                            break
                response = {"query": query, "matches": matches, "truncated": len(matches) == 300}
            except (ValueError, OSError) as exc:
                response = {"error": str(exc), "matches": []}
            serialized = json.dumps(response, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixProjectSearchResult(" + serialized + ");", None)

    core_recovery_handler = CoreRecoveryHandler.alloc().init()
    core_close_handler = CoreCloseHandler.alloc().init()
    core_discard_handler = CoreDiscardHandler.alloc().init()
    core_buffer_handler = CoreBufferHandler.alloc().init()
    project_search_handler = ProjectSearchHandler.alloc().init()
    file_save_handler = FileSaveHandler.alloc().init()
    file_open_handler = FileOpenHandler.alloc().init()
    navigation_handler = NavigationHandler.alloc().init()
    controller = view.configuration().userContentController()
    controller.addScriptMessageHandler_name_(navigation_handler, "pynixNavigation")
    controller.addScriptMessageHandler_name_(file_open_handler, "pynixFileOpen")
    controller.addScriptMessageHandler_name_(core_buffer_handler, "pynixCoreBuffer")
    controller.addScriptMessageHandler_name_(core_discard_handler, "pynixCoreDiscard")
    controller.addScriptMessageHandler_name_(core_close_handler, "pynixCoreClose")
    controller.addScriptMessageHandler_name_(core_recovery_handler, "pynixCoreRecover")
    controller.addScriptMessageHandler_name_(file_save_handler, "pynixFileSave")
    controller.addScriptMessageHandler_name_(project_search_handler, "pynixProjectSearch")
    document = attach_navigation_controls(document)
    view.loadHTMLString_baseURL_(document, url.URLByDeletingLastPathComponent())
    window.setContentView_(view)
    from pynix_gui.ide_native_menu import install_native_workspace_menu
    menu_dispatcher = install_native_workspace_menu(app, view, AppKit)
    window.makeKeyAndOrderFront_(None)
    window.makeFirstResponder_(view)
    app.activateIgnoringOtherApps_(True)
    try:
        app.run()
    finally:
        if core_reader is not None:
            core_reader.close()


if __name__ == "__main__":
    main()

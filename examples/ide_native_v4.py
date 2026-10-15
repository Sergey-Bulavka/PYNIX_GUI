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

# A dedicated native drag surface tracks the actual EMPTY toolbar spacer.
# No page-wide AppKit dragging: all scrollbars and editor interactions remain WebKit-owned.
TOOLBAR_DRAG_SCRIPT = """<script>
(() => {
  const spacer = document.querySelector('.workspace-mode .workspace-toolbar > .toolbar-spacer');
  const toolbar = document.querySelector('.workspace-mode .workspace-toolbar');
  if (!spacer || !toolbar) return;
  // In narrow windows the flex spacer can collapse. The static PYNIX title
  // remains a safe drag target (unlike editor tabs or toolbar buttons).
  const title = toolbar.querySelector('strong');
  let last = '';
  const update = () => {
    const space = spacer.getBoundingClientRect();
    const bar = toolbar.getBoundingClientRect();
    const label = title?.getBoundingClientRect();
    const region = space.width >= 64 ? space : (label || space);
    // Keep clear of the macOS top resize edge and right resize corner.
    const area = {x:region.left+12, y:bar.top+10,
                  width:Math.max(0,region.width-24),
                  height:Math.max(0,bar.height-18)};
    const encoded = JSON.stringify(area);
    if(encoded===last)return;
    last=encoded;
    window.webkit?.messageHandlers?.pynixToolbarDragRegion?.postMessage(area);
  };
  const observer = new ResizeObserver(update);
  observer.observe(spacer);
  observer.observe(toolbar);
  if(title)observer.observe(title);
  // Native NSViewMinYMargin holds the drag view at the top when the height
  // changes; a resize event also refreshes horizontal spacer geometry.
  window.addEventListener('resize', update);
  requestAnimationFrame(update);
})();
</script>"""


def toolbar_drag_frame(bounds_width: float, bounds_height: float, area: dict):
    """Map WebKit top-left CSS coordinates to AppKit bottom-left view points.

    Only a sufficiently large region fully inside the top 44px toolbar is
    eligible; never let a malformed message cover a Project pane or scrollbar.
    """
    import math

    try:
        x, top, width, height = (
            float(area[key]) for key in ("x", "y", "width", "height")
        )
        bounds_width, bounds_height = float(bounds_width), float(bounds_height)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(v) for v in (x, top, width, height, bounds_width, bounds_height)):
        return None
    # Reserve the top border for resizing and never cover window corners.
    if (x < 86 or top < 8 or top > 16 or height < 16 or height > 30
            or top + height > 40 or width < 32 or bounds_width < 760):
        return None
    width = min(width, bounds_width - x - 18)
    if width < 32:
        return None
    return (x, bounds_height - top - height, width, height)



def title_drag_frame(bounds_width: float, bounds_height: float):
    """Always-available drag handle over the static PYNIX toolbar title.

    The title starts at x=86 in our 44-point native toolbar. This handle is
    deliberately inset from the window's resize borders and traffic lights.
    Unlike the optional flex-spacer handle, it never depends on WebKit layout.
    """
    if bounds_width < 760 or bounds_height < 520:
        return None
    return (92, bounds_height - 35, 62, 24)


def corner_resize_geometry(bounds_width: float, bounds_height: float):
    """Bottom-right 22pt native hit target, independent of WebKit loading."""
    return (max(0.0, float(bounds_width) - 24.0), 2.0, 22.0, 22.0)


def resized_window_frame(original, mouse_start, mouse_now, minimum=(760, 520)):
    """Resize from bottom-right, keeping the opposite (top-left) corner fixed.

    NSEvent.mouseLocation uses global screen coordinates; independent of
    NSView frame changes, pointer capture, the current screen and window scale.
    """
    import math

    try:
        x, y, width, height = (float(value) for value in original)
        start_x, start_y = (float(value) for value in mouse_start)
        now_x, now_y = (float(value) for value in mouse_now)
        min_width, min_height = (float(value) for value in minimum)
    except (ValueError, TypeError, OverflowError):
        return None
    if not all(math.isfinite(v) for v in
               (x, y, width, height, start_x, start_y, now_x, now_y,
                min_width, min_height)):
        return None
    if min_width <= 0 or min_height <= 0:
        return None
    new_width = max(min_width, width + now_x - start_x)
    new_height = max(min_height, height + start_y - now_y)
    return (x, y + height - new_height, new_width, new_height)


def main() -> None:
    if sys.platform != "darwin":
        raise SystemExit("V4 native review requires macOS")
    if not PREVIEW_PATH.is_file():
        raise SystemExit(f"Missing V4 preview: {PREVIEW_PATH}")

    import AppKit
    import WebKit
    import objc
    from Foundation import NSObject, NSURL
    from pynix_gui.ide_navigation_bridge import (
        attach_navigation_controls, normalize_webkit_request, validate_request, result_script,
    )

    drag_resize_callback = {"update": None}

    class PreviewDelegate(NSObject):
        def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
            return True

        def windowDidResize_(self, notification):
            # Reposition both drag handles in CURRENT AppKit coordinates on
            # every width/height change, even when JS geometry was unchanged.
            update = drag_resize_callback["update"]
            if update is not None:
                update()

    class FirstClickWebView(WebKit.WKWebView):
        """Forward the first click even when the macOS window is inactive."""

        def acceptsFirstMouse_(self, event):
            return True

    class ToolbarDragView(AppKit.NSView):
        """Small transparent NSView over the toolbar's empty flex spacer only."""

        def acceptsFirstMouse_(self, event):
            return True

        def mouseDown_(self, event):
            self.window().performWindowDragWithEvent_(event)

    resize_state = {"frame": None, "mouse": None}

    class CornerResizeView(AppKit.NSView):
        """An always-present native bottom-right resize handle.

        This bypasses intermittent window-border hit testing in a WKWebView
        hosted under NSWindowStyleMaskFullSizeContentView.
        """

        def acceptsFirstMouse_(self, event):
            return True

        def mouseDown_(self, event):
            window = self.window()
            if window is None:
                return
            frame = window.frame()
            mouse = AppKit.NSEvent.mouseLocation()
            resize_state["frame"] = (
                frame.origin.x, frame.origin.y, frame.size.width, frame.size.height
            )
            resize_state["mouse"] = (mouse.x, mouse.y)

        def mouseDragged_(self, event):
            if resize_state["frame"] is None:
                return
            mouse = AppKit.NSEvent.mouseLocation()
            frame = resized_window_frame(
                resize_state["frame"], resize_state["mouse"], (mouse.x, mouse.y)
            )
            if frame is not None:
                self.window().setFrame_display_(AppKit.NSMakeRect(*frame), True)

        def mouseUp_(self, event):
            resize_state["frame"] = None
            resize_state["mouse"] = None

        def drawRect_(self, dirty_rect):
            # Subtle diagonal grip inside the bottom-right corner.
            AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.6, 0.9).setStroke()
            for offset in (0.0, 5.0, 10.0):
                line = AppKit.NSBezierPath.bezierPath()
                line.setLineWidth_(1.0)
                line.moveToPoint_(AppKit.NSMakePoint(7.0 + offset, 3.0))
                line.lineToPoint_(AppKit.NSMakePoint(19.0, 15.0 - offset))
                line.stroke()

    app = AppKit.NSApplication.sharedApplication()
    delegate = PreviewDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)

    window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        AppKit.NSMakeRect(90, 75, 1500, 950),
        AppKit.NSWindowStyleMaskTitled
        | AppKit.NSWindowStyleMaskClosable
        | AppKit.NSWindowStyleMaskMiniaturizable
        | AppKit.NSWindowStyleMaskResizable
        | AppKit.NSWindowStyleMaskFullSizeContentView,
        AppKit.NSBackingStoreBuffered,
        False,
    )
    window.setTitle_("PYNIX IDE")
    window.setTitleVisibility_(AppKit.NSWindowTitleHidden)
    window.setTitlebarAppearsTransparent_(True)
    window.setMovableByWindowBackground_(False)
    window.setMinSize_(AppKit.NSMakeSize(760, 520))

    # Preserve AppKit's original content view: replacing it can interfere with
    # the border/corner resize hit-testing of full-size-content windows.
    content_view = window.contentView()
    view = FirstClickWebView.alloc().initWithFrame_(content_view.bounds())
    view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
    content_view.addSubview_(view)
    drag_area = ToolbarDragView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, 0, 0))
    # Flexible MIN-Y (bottom) margin pins the region to the TOP of its
    # superview through height-only resizes, even without a fresh JS message.
    drag_area.setAutoresizingMask_(AppKit.NSViewMinYMargin)
    drag_area.setHidden_(True)
    content_view.addSubview_(drag_area)  # Optional live toolbar spacer.
    title_drag_area = ToolbarDragView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, 0, 0))
    title_drag_area.setAutoresizingMask_(AppKit.NSViewMinYMargin)
    content_view.addSubview_(title_drag_area)  # Always active over static PYNIX title.
    # A dedicated grip guarantees resizing without relying on hidden AppKit
    # edge hit targets or WebKit's readiness during initial window startup.
    corner_resize = CornerResizeView.alloc().initWithFrame_(
        AppKit.NSMakeRect(*corner_resize_geometry(
            content_view.bounds().size.width, content_view.bounds().size.height
        ))
    )
    corner_resize.setAutoresizingMask_(
        AppKit.NSViewMinXMargin | AppKit.NSViewMaxYMargin
    )
    content_view.addSubview_(corner_resize)
    drag_geometry = {"area": None}

    def refresh_native_drag_areas():
        bounds = content_view.bounds().size
        frame = title_drag_frame(bounds.width, bounds.height)
        if frame is not None:
            title_drag_area.setFrame_(AppKit.NSMakeRect(*frame))
            title_drag_area.setHidden_(False)
        else:
            title_drag_area.setHidden_(True)
        area = drag_geometry["area"]
        frame = toolbar_drag_frame(bounds.width, bounds.height, area) if area is not None else None
        if frame is not None:
            drag_area.setFrame_(AppKit.NSMakeRect(*frame))
            drag_area.setHidden_(False)
        else:
            drag_area.setHidden_(True)

    drag_resize_callback["update"] = refresh_native_drag_areas
    refresh_native_drag_areas()
    window.setDelegate_(delegate)
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
            core_status = f"IDE Core: connected (PID {core_reader._process.pid}, buffer sync)"
        except (CoreSnapshotError, OSError) as exc:
            core_reader = None
            core_status = "IDE Core: " + str(exc)[:180]
        indicator = '<div class="pynix-core-bridge-indicator" role="status" style="position:fixed;right:16px;bottom:30px;z-index:9000;background:#1c2939;color:#e5effc;border:1px solid #496782;padding:5px 10px;border-radius:6px;font:12px system-ui">' + escape(core_status) + '</div>'
        document = document.replace("</body>", indicator + "</body>", 1)
    from pynix_gui.ide_tooling_navigation import query_navigation
    compiler_python = args.compiler_python or (session.root / ".venv" / "bin" / "python")
    available_sources = set(session.list_files(limit=5000))
    class SemanticRenameHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            from pynix_gui.ide_semantic_rename import plan_semantic_rename, RenamePlanError
            try:
                request = normalize_webkit_request(message.body())
                _, source, line, column = validate_request(
                    {**request, "command": "references"}, available_sources)
                new_name = request.get("newName")
                result = plan_semantic_rename(
                    session.root, compiler_python, source, line, column, new_name)
                if core_reader is None:
                    raise CoreSnapshotError("Connected IDE Core required for semantic rename")
                for entry in result["files"]:
                    core_reader.open_source(entry["source"])
                    state = core_reader.read_source(entry["source"])
                    if state["dirty"] or state["content"] != entry["before"]:
                        raise CoreSnapshotError("Core source changed; save and retry semantic rename")
                    entry["coreRevision"] = state["revision"]
            except (ValueError, TypeError, RenamePlanError, CoreSnapshotError, OSError) as exc:
                result = {"error": str(exc)}
            serialized = json.dumps(result, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixSemanticRenamePlan(" + serialized + ");", None)

    from pynix_gui.ide_project_runner import ProjectRunner, RunError
    import json as run_json
    import threading as run_threading
    from Foundation import NSOperationQueue
    project_runner = ProjectRunner(session.root, compiler_python)

    def publish_run_result(result):
        payload = run_json.dumps(result, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
        script = "window.pynixProjectRunResult(" + payload + ");"
        NSOperationQueue.mainQueue().addOperationWithBlock_(
            lambda: view.evaluateJavaScript_completionHandler_(script, None))

    run_generation = {"value": 0}

    def start_project_run(mode="run"):
        project_runner.start(mode=mode)
        run_generation["value"] += 1
        generation = run_generation["value"]
        publish_run_result({"state": "running"})
        def worker():
            def deliver(chunk):
                if run_generation["value"] == generation:
                    publish_run_result({"state": "output", "chunk": chunk})
            try:
                result = project_runner.collect(on_output=deliver)
                if run_generation["value"] == generation:
                    publish_run_result({"state": "finished", **result})
            except (RunError, OSError) as exc:
                if run_generation["value"] == generation:
                    publish_run_result({"state": "error", "error": str(exc)[:300]})
        run_threading.Thread(target=worker, daemon=True).start()

    from pynix_gui.ide_debug_process_client import DebugProcessClient
    debug_client = DebugProcessClient(session.root, compiler_python)

    class DebugCommandHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            try:
                request = dict(message.body())
                action = request.get("action")
                source = request.get("source")
                breakpoints = request.get("breakpoints")
                if action not in {"launch", "pause", "continue", "stepInto",
                                  "stepOver", "stepOut", "stack", "variables", "status", "stop", "setBreakpoints"}:
                    raise ValueError("Unknown debugger command")
                if action == "launch" and (not isinstance(source, str) or
                                            source not in available_sources):
                    raise ValueError("Unindexed debugger source")
            except (TypeError, ValueError) as exc:
                publish_debug_result({"event": "error", "message": str(exc)[:200]})
                return

            def job():
                try:
                    result = (debug_client.launch(source) if action == "launch" else
                              debug_client.set_breakpoints(breakpoints) if action == "setBreakpoints" else
                              debug_client.command(action))
                    publish_debug_result(result)
                except Exception as exc:
                    # A failed transport is not a protocol-level command rejection.
                    # Signal that the native session has been discarded only when
                    # the client no longer owns a worker.
                    disconnected = debug_client._worker is None
                    publish_debug_result({"event": "disconnected" if disconnected else "error",
                                          "message": str(exc)[:200]})
            run_threading.Thread(target=job, daemon=True).start()

    def publish_debug_result(result):
        payload = run_json.dumps(result, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
        NSOperationQueue.mainQueue().addOperationWithBlock_(
            lambda: view.evaluateJavaScript_completionHandler_(
                "window.pynixDebugResult(" + payload + ");", None))

    class ProjectRunHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            try:
                request = dict(message.body())
                action = request.get("action")
                if action == "run":
                    mode = request.get("mode", "run")
                    if mode not in ("run", "check"):
                        raise RunError("Unsupported run configuration")
                    start_project_run(mode)
                elif action in ("stop", "restart"):
                    mode = request.get("mode", "run")
                    if mode not in ("run", "check"):
                        raise RunError("Unsupported run configuration")
                    run_generation["value"] += 1
                    publish_run_result({"state": "stopping"})
                    def stop_or_restart():
                        try:
                            project_runner.stop()
                            if action == "restart":
                                start_project_run(mode)
                            else:
                                publish_run_result({"state": "idle"})
                        except (RunError, OSError) as exc:
                            publish_run_result({"state": "error", "error": str(exc)[:300]})
                    run_threading.Thread(target=stop_or_restart, daemon=True).start()
                else:
                    raise RunError("Unknown project run action")
            except (RunError, OSError, ValueError, TypeError) as exc:
                publish_run_result({"state": "error", "error": str(exc)[:300]})

    class ProjectFileActionHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            from pynix_gui.ide_workspace_session import WorkspaceError
            response = {"ok": False}
            try:
                request = dict(message.body())
                action = request.get("action")
                source = request.get("source")
                destination = request.get("destination")
                if action not in {"rename", "delete"} or not isinstance(source, str) or source not in available_sources:
                    raise WorkspaceError("Unknown project file action")
                if action == "rename" and (not isinstance(destination, str) or
                                           not destination.endswith(".pnx") or
                                           destination in available_sources):
                    raise WorkspaceError("Invalid destination for PYNIX source rename")
                if not source.endswith(".pnx"):
                    raise WorkspaceError("Only PYNIX source files can be modified")
                if core_reader is not None:
                    core_reader.open_source(source)
                    state = core_reader.read_source(source)
                    if state["dirty"]:
                        raise WorkspaceError("Save IDE Core changes before modifying this file")
                    if not core_reader.close_source(source):
                        raise WorkspaceError("IDE Core refused to close source")
                if action == "rename":
                    session.rename_file(source, destination)
                    available_sources.discard(source)
                    available_sources.add(destination)
                    response = {"ok": True, "action": action, "source": source,
                                "destination": destination}
                else:
                    session.delete_file(source)
                    available_sources.discard(source)
                    response = {"ok": True, "action": action, "source": source}
            except (ValueError, TypeError, WorkspaceError, CoreSnapshotError, OSError) as exc:
                response["error"] = str(exc)[:300]
            serialized = json.dumps(response, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixProjectFileActionResult(" + serialized + ");", None)

    class ProjectCreateHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            from pynix_gui.ide_workspace_session import WorkspaceError
            response = {"ok": False}
            try:
                request = dict(message.body())
                relative = request.get("source")
                if not isinstance(relative, str) or not relative.endswith(".pnx"):
                    raise WorkspaceError("Only PYNIX source creation is supported")
                if len(available_sources) >= 5000:
                    raise WorkspaceError("Project file index is full")
                doc = session.create_file(relative)
                available_sources.add(relative)
                response = {"ok": True, "source": relative, "text": doc.text}
            except (ValueError, TypeError, OSError, WorkspaceError) as exc:
                response["error"] = str(exc)
            serialized = json.dumps(response, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixProjectCreateResult(" + serialized + ");", None)

    class SymbolsHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            from pynix_gui.ide_tooling_symbols import read_symbols
            result = read_symbols(session.root, compiler_python)
            serialized = json.dumps(result, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixProjectSymbolsResult(" + serialized + ");", None)

    class DiagnosticsHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            import json
            from pynix_gui.ide_tooling_diagnostics import read_diagnostics
            snapshot = read_diagnostics(session.root, compiler_python)
            response = {
                "error": snapshot.error,
                "problems": [{"source": p.source, "line": p.line,
                              "column": p.column, "code": p.code, "message": p.message}
                             for p in snapshot.problems],
            }
            serialized = json.dumps(response, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            view.evaluateJavaScript_completionHandler_(
                "window.pynixLiveDiagnosticsResult(" + serialized + ");", None)

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
                # PyObjC may bridge a JavaScript Array as NSArray, not list/tuple.
                if isinstance(entries, (str, bytes, dict)) or not hasattr(entries, "__iter__"):
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
            response = {"source": source, "revision": request.get("revision")}
            try:
                if not isinstance(source, str) or source not in available_sources:
                    raise ValueError("Source is outside the indexed project")
                if not isinstance(content, str) or len(content.encode("utf-8")) > 1_000_000:
                    raise ValueError("Source content exceeds the editor limit")
                if args.ide_core is not None and source.endswith(".pnx") and core_reader is None:
                    raise CoreSnapshotError("IDE Core is unavailable; cannot save .pnx. Preserve editor text and restore Core.")
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
    semantic_rename_handler = SemanticRenameHandler.alloc().init()
    debug_command_handler = DebugCommandHandler.alloc().init()
    project_run_handler = ProjectRunHandler.alloc().init()
    project_file_action_handler = ProjectFileActionHandler.alloc().init()
    project_create_handler = ProjectCreateHandler.alloc().init()
    symbols_handler = SymbolsHandler.alloc().init()
    diagnostics_handler = DiagnosticsHandler.alloc().init()
    navigation_handler = NavigationHandler.alloc().init()
    class ToolbarDragRegionHandler(NSObject):
        def userContentController_didReceiveScriptMessage_(self, controller, message):
            drag_geometry["area"] = message.body()
            refresh_native_drag_areas()

    toolbar_drag_handler = ToolbarDragRegionHandler.alloc().init()
    controller = view.configuration().userContentController()
    controller.addScriptMessageHandler_name_(
        toolbar_drag_handler, "pynixToolbarDragRegion")
    controller.addScriptMessageHandler_name_(semantic_rename_handler, "pynixSemanticRename")
    controller.addScriptMessageHandler_name_(debug_command_handler, "pynixDebugCommand")
    controller.addScriptMessageHandler_name_(project_run_handler, "pynixProjectRun")
    controller.addScriptMessageHandler_name_(project_file_action_handler, "pynixProjectFileAction")
    controller.addScriptMessageHandler_name_(project_create_handler, "pynixProjectCreate")
    controller.addScriptMessageHandler_name_(symbols_handler, "pynixProjectSymbols")
    controller.addScriptMessageHandler_name_(diagnostics_handler, "pynixDiagnostics")
    controller.addScriptMessageHandler_name_(navigation_handler, "pynixNavigation")
    controller.addScriptMessageHandler_name_(file_open_handler, "pynixFileOpen")
    controller.addScriptMessageHandler_name_(core_buffer_handler, "pynixCoreBuffer")
    controller.addScriptMessageHandler_name_(core_discard_handler, "pynixCoreDiscard")
    controller.addScriptMessageHandler_name_(core_close_handler, "pynixCoreClose")
    controller.addScriptMessageHandler_name_(core_recovery_handler, "pynixCoreRecover")
    controller.addScriptMessageHandler_name_(file_save_handler, "pynixFileSave")
    controller.addScriptMessageHandler_name_(project_search_handler, "pynixProjectSearch")
    document = attach_navigation_controls(document)
    from pynix_gui.ide_icon_parity import apply_new_ui_icons
    document = apply_new_ui_icons(document)
    from pynix_gui.ide_edge_profile import apply_edge_profile
    document = apply_edge_profile(document)
    document = document.replace("</body>", TOOLBAR_DRAG_SCRIPT + "</body>", 1)
    view.loadHTMLString_baseURL_(document, url.URLByDeletingLastPathComponent())
    # The original content view remains window-owned and resizable.
    from pynix_gui.ide_native_menu import install_native_workspace_menu
    menu_dispatcher = install_native_workspace_menu(app, view, AppKit)
    window.makeKeyAndOrderFront_(None)
    window.makeFirstResponder_(view)
    app.activateIgnoringOtherApps_(True)
    try:
        app.run()
    finally:
        debug_client.close()
        project_runner.close()
        if core_reader is not None:
            core_reader.close()


if __name__ == "__main__":
    main()

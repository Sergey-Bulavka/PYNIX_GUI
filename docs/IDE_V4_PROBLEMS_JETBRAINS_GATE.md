# PYNIX IDE V4 — Problems tool window

Reference: [PyCharm 2026.2 Problems tool window](https://www.jetbrains.com/help/pycharm/problems-tool-window.html), [Get results and fix problems](https://www.jetbrains.com/help/pycharm/resolving-problems.html).

## Runtime contract

The bottom-left **Problems** icon toggles a real independent Problems tool view. It uses the same resizable dock shell as Run/Terminal/Debug but retains its own content. No compiler result replaces Terminal or Run output.

**File** lists the current editor file's compiler results, updated when switching sources. **Project Errors** groups all returned diagnostics by source file with expanding/collapsing sections. **AI Self-Review** explicitly says that it is not connected: no invented AI analysis.

The native IDE launches PYNIX compiler tooling V1 in a background worker using the explicit compiler Python interpreter and project root. The worker sends results through the existing PyObjC/WebKit bridge. Every result has a source, line, column, code, message and severity (error/warning). Refresh reruns analysis; saving source supplies an updated snapshot. Independent overlapping refresh requests use last-request-wins semantics.

**Known limitations:** The compiler analyzes the *saved* project on disk, not unsaved editor buffers. Its diagnostics require a PYNIX manifest and the compiler Python interpreter. On failure the UI shows an error, never a false "no problems". The current adapter shows at most 200 results. Quick fixes stay disabled until the public compiler tooling protocol supplies actionable fixes. Preview is read-only, with navigation to the real editor for changes.

## Functional acceptance on macOS

1. Click the left Problems tool icon. Confirm the tabs File / Project Errors / AI Self-Review. Refresh project diagnostics.
2. Switch between open source files. The File view must follow the active editor. Save a modified PYNIX file; the Problems snapshot must update.
3. Select a problem, navigate by double click, F4 or Enter. Use Up/Down to change selection and Cmd+C to copy its location/message.
4. Open Project Errors; expand/collapse grouped files, test severity filters and source-position ordering.
5. Enable Editor Preview: a real local code excerpt, not a fake editable buffer, appears for the selected issue.
6. Toggle Problems closed/open. Switch to Terminal and Run, then save a PYNIX file. Their console output must remain intact.
7. Confirm the original licensed JetBrains 16px toolbar SVG icons remain visible in default native V4 iconless mode and the separate 20px left-edge icon is not replaced.
8. AI Self-Review displays a truthful not-connected message. Quick-fix action remains disabled because there are no compiler-provided fixes.

## Tests

Focused command:

    python -m pytest -q tests/test_ide_problems_window.py tests/test_ide_tooling_diagnostics.py tests/test_ide_workspace_preview.py tests/test_ide_v4_separate_terminals.py

Native visual verification must run on a Mac with AppKit/WKWebView.

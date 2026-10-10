# Real Project Explorer V1 — acceptance and scope

## Purpose

Validate PYNIX GUI as a toolkit for real applications, not only static showcases.
The example application reads a user-selected local project directory and displays
a folder tree, direct-child table, and read-only .pnx source preview. PYNIX_GUI
does not own filesystem I/O or PYNIX_IDE source-buffer state.

## Run (macOS)

```bash
cd /Users/morphey/PycharmProjects/PYNIX_GUI
source .venv/bin/activate
python -m examples.real_project_app /Users/morphey/PycharmProjects/PYNIX
```

## Accepted semantics to verify interactively

1. Window opens at 1160×760; folders appear at left and root entries at right.
2. Select one table row: only selection changes, not the active folder.
3. Double-click a directory or select it and press Open: show its direct children.
4. Up returns to the parent directory, never above the selected project root.
5. Open a .pnx file: render its UTF-8 text in a read-only editor.
6. Refresh updates the right-side listing after an external file change.
7. Directory tree contains folders, not files; invalid expansion state is pruned.
8. Check text/row selections in both light and dark macOS appearance.
9. Opening unrelated binary or oversized files must not crash the application.

## Limitations / next Design Gate

- The folder tree intentionally limits deep traversal to four levels; the table
  can navigate below that depth. A proper lazy tree model is still needed.
- .pnx preview is not an IDE editor session and does not persist changes.
- No file creation/deletion/rename, search, watch service, or automatic reload.
- Backends require native keyboard / gesture acceptance; CI alone is insufficient.
- Source file handoff to PYNIX_IDE requires a separate application integration.

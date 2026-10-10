# File Manager Interaction V2 — Native Acceptance

## User-facing interaction contract

- **One click in Files:** select row, do not open a folder.
- **Double click in Files:** open selected folder, replacing the right-hand
  listing; opening a file records the requested file without navigating into it.
- **Enter on a focused Files row:** explicit open action.
- **Backspace on a focused Files row:** navigate to parent directory.
- **Right-click Files row:** Open and Up context actions.
- **Open / Up toolbar buttons:** accessible fallback for mouse and keyboard.
- **Left navigation Tree:** selecting a directory updates the right-hand list.
- **No descendant flattening:** the table displays direct children only.

The semantic `GUIEvent("OPEN", target=..., item_id=...)` preserves platform
independence. Existing ACTIVATE, SELECTION, EXPANSION contracts are unchanged.

## Validation

Automated tests cover selection vs opening, stale selection, parent navigation,
folder contents and OPEN event validation. CI does not prove AppKit gesture
recognition, context menu placement, Qt native key routing or actual visual
selection consistency.

Native macOS acceptance before merging:
1. Select a folder in Files: listing must not change.
2. Double-click the same folder: listing must change exactly once.
3. Enter on selected folder, Backspace to parent.
4. Right-click folder -> Open, and right-click -> Up.
5. Select a file and Open: directory listing stays unchanged.
6. Confirm selected row stays readable in dark and light themes.

Interactive Windows/Qt acceptance remains pending.

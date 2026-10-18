# Design Gate — compact PyCharm Tab Actions menu with real commands

## Real task and acceptance evidence
The user compared a screenshot of PYNIX IDE V4 (right) against PyCharm (left).
Four differences: PYNIX menu is stretched, shortcut glyphs are smaller,
three commands are inactive, and menu rows lack full-width highlight on hover.

## Reference comparison
- PyCharm: dense approximately 29px rows, constrained width, strong blue
  full-row highlight on mouse and keyboard, shortcut keys aligned right,
  bookmarks/preview configuration/minimap menu commands with real meaning.
- VS Code: bounded action lists and Command Palette, editor tab preferences,
  editor minimap and reusable file-navigation history.
- Legacy PYNIX: 32px+ rows with excessive margins, disabled menu actions,
  low-contrast 12px shortcuts, and hover on the nested button but not the row.

## Native PYNIX design
1. Keep the existing PYNIX V4 tab model as the single source of file identity,
   modified buffers, close confirmation and source navigation.
2. Match compact spacing with a final, high-specificity CSS layer: 228px
   popup target width, 27px row hitboxes, 13px labels, 13.5px
   shortcut glyphs, 17px file icons, 4px separators. Apply hover/focus/
   selection highlight to the entire row with `!important` to override old
   layers. Allow Arrow Up/Down, Home/End and Escape keyboard interaction.
3. Implement `Bookmark Open Tabs...` as **named groups of source paths**
   persisted under a per-project localStorage key, bounded to 20 groups ×
   100 paths each, with safe in-memory operation when storage is unavailable.
   `Open Bookmarked Tabs...` appears only after a group exists and restores
   only paths still in the actual file index. Delete group is an explicit
   separate action.
4. `Configure Editor Tabs...` opens compact, deterministic settings for
   density, file-icon visibility, and close-button visibility. All settings
   apply to the real tab strip and persist per project.
5. `Show Minimap` toggles a **real source overview canvas**, derived from
   the currently active editor buffer or read-only source. The viewport
   indicator follows scroll position, clicking the minimap scrolls the
   code. Rendering is capped at 5000 sampled lines for responsiveness.
   No second editable buffer or separate minimap data model.
6. Advertised macOS shortcuts for Recent Files, Recent Locations and Go To
   File now have the same event dispatch handlers as the visible menu.
7. Invalid or non-indexed bookmarked paths are skipped. Dirty buffers
   preserve existing save/close semantics; no force close or hidden writes.

## Limits and follow-up
A mini-map overview is a new V4 feature, not a replacement syntax renderer.
Its small visual marks are simplified, but derive from real source text.
WKWebView localStorage persistence may vary with origin; the tab commands
remain usable for the active session if storage is unavailable. Native
persistent settings may eventually live in IDE Core.
The configuration is intentionally small rather than copying JetBrains
hundreds of tab flags.

## Verification
```bash
python -m pytest tests/test_ide_editor_tab_controls.py \
  tests/test_ide_editor_tab_menu_complete.py -q
python -m pytest -q
git diff --check
```
Manually check menu comparison side-by-side on Mac, including hover/keyboard,
bookmark restore after reopening the project, tab icon visibility, and
minimap scrolling with both a short .pnx and large .py file.

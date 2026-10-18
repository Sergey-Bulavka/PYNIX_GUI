# Design Gate — PyCharm-like Editor Tab Overflow and Actions (native V4)

## Real user task
In the **actual native IDE V4 editor**, add (1) a down-chevron that appears
only when tabs cannot all fit and displays the hidden tabs with native file
icons, selection and close controls, and (2) a persistent three-dot menu
labelled "Recent Files, Tab Actions, and More", matching the provided PyCharm
references.

## Reference and shortcomings
- JetBrains PyCharm hides excess tabs and exposes a hidden-tabs selector plus
  a menu for navigation, closing and editor actions.
- VS Code supports constrained editor tab groups, history navigation and
  overflow menus.
- The previous PYNIX editor used `overflow-x:auto` on the entire header:
  no dedicated hidden-tabs list, and no persistent tab-actions control.
- A second tab model or decorative menu would diverge from real editor state.
  Opening and closing `.pnx` must retain the IDE Core close acknowledgement,
  unsaved confirmation and native save bridge.

## Native PYNIX solution
- Use the real `openTabs` list and `current` variable as the only source of
  truth. A new `pynix-tabs-strip` is the width-limited region, with a
  right-hand `pynix-tabs-actions` container that is **always visible**.
- A pure overflow planner measures actual tab widths, keeps the active tab
  visible, and hides excess tabs **without deleting/reordering them**.
  Recalculate on open/close/edit and ResizeObserver of the editor tab bar.
- A chevron appears only on actual overflow. Its menu shows exactly hidden
  source paths, file icons, modified markers, active highlighting, file
  selection and close button using existing handlers.
- The three-dot button is always present with native tooltip
  "Recent Files, Tab Actions, and More" and a real menu outside the
  clipped tab container.
- Functional actions:
  - Recent Files: session-level navigation history.
  - Recent Locations: session-level source/line history from the real editor
    caret and source location navigation.
  - Go to File: delegates to existing Search Everywhere.
  - Close All Tabs: serializes close requests, honoring the existing Save,
    Don't Save, Cancel and IDE Core asynchronous close results.
  - Close Unmodified Tabs: same safe close path, filtered by dirty state.
  - Reopen Closed Tab: restores a known source through the real file-opening
    path, not stale discarded buffer bytes.
- Unimplemented actions (Bookmark Open Tabs, Configure Editor Tabs, Show
  Minimap) are **clearly disabled**, rather than performing no action or
  pretending the corresponding subsystem exists. They require separate
  implementation/Design Gates.
- Popups live in the document body to avoid clipping. Hover, keyboard Escape,
  outside click, menu roles and tooltip integration work in the existing V4.
- Preserve tabs, existing JetBrains icon bridge, tab-specific navigation
  keys, editor resize and source persistence.

## Verification
```bash
python -m pytest tests/test_ide_editor_tab_controls.py \
 tests/test_ide_dirty_tab_close.py tests/test_ide_workspace_preview.py -q
python -m pytest -q
git diff --check
```

Native macOS manual acceptance: open 6+ mixed `.pnx/.py/.md` tabs and
resize the IDE and Explorer rapidly. Ensure hidden tabs appear/disappear only
as necessary, active file stays visible, hidden-file actions work, and there
are no overlaps. Open three-dot menu, use Recent Files/Locations, close clean
tabs, cancel a dirty close, and reopen a previously closed tab.

CI validates contracts and pure width planning but does not reproduce the
full WKWebView/AppKit window and all interactive mouse behaviors.

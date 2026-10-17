# Design Gate — Drag from every free topbar gap; pin Project header

## User's real need

1. On macOS PYNIX IDE V4, clicking and dragging any **empty part of the top
   toolbar** should move the window. Run, Debug, Project, Git, Search, Settings,
   tool-menu buttons and other inputs must keep their existing click/hover
   behavior.
2. The Project header, including the view selector and action icons, must
   remain stationary above the scrollable file tree, and align vertically with
   the editor tabs (the accepted 43px tab strip).

## Reference systems

- AppKit NSWindow's native `performWindowDragWithEvent:` is the supported
  way to start native dragging from a custom NSView under a real mouse event.
- JetBrains IDE tool-window headers and browser sticky positioning both
  separate a fixed header from scrolling tree content. CSS `position:sticky`
  requires neither a second tree nor JavaScript scroll repositioning.

## Root causes and rejected shortcuts

The previous native implementation accepted only the width of one flex
spacer, plus a hardcoded 62px drag region above the project button. After the
toolbar was reorganized into a single responsive flex row with TWO spacer
regions, the first spacer was an incomplete proxy for free pixels.

Do **not** overlay the whole topbar and blindly call `performWindowDrag...`:
an AppKit overlay placed above WKWebView would steal mouse events intended
for buttons, menus and editable controls. CSS `-webkit-app-region:drag`
alone is not relied upon for native AppKit NSWindow dragging.

## PYNIX implementation

- Measure **all** visible topbar interactive controls by their real DOM
  `getBoundingClientRect()`, independently of responsive breakpoints.
- Subtract their horizontal hitboxes with a 5px clearance, and exclude
  macOS traffic lights and outer window resize borders.
- Emit the resulting disjoint free rectangles through the existing
  `pynixToolbarDragRegion` WebKit bridge. AppKit maintains a pool of
  hidden/visible `ToolbarDragView` strips; only nonempty validated strips
  accept `mouseDown:` and initiate native dragging.
- Recalculate on toolbar/control resize, DOM mutations and browser resize.
  Never expose a speculative full-width region before the real controls
  have been initialized. The native geometry guard still enforces the
  44px toolbar boundary. No timer or second layout engine.
- Remove the old hardcoded title drag zone to prevent click interception.
- Keep the Project header in the **existing** scrolling tree and use
  `position:sticky; top:0; z-index:35`, a fixed 43px height and matching
  background/border. The editor tab strip remains 43px.

## Verification / acceptance

- Drag slowly and quickly from blank pixels between all three toolbar
  groups, before/after opening menu popups, at 760–1500px widths. No
  button should inadvertently initiate a window move.
- Drag and click each toolbar button and Project selector; no stale
  hit-testing or resizing regressions.
- Scroll a deep Project folder: the toolbar must stay visible, while file
  rows pass underneath. Compare its top and bottom edges with editor tabs.
- Verify after collapsing/reopening Project, opening multiple tabs and
  resizing the Explorer width.
- Both default V4 mode and `--with-icons`.
- CI should test the DOM gap-complement algorithm under simulated layout
  changes, AppKit bounds validation and CSS sticky contract.
- Native macOS visual and real pointer-drag acceptance is still necessary;
  a headless test cannot guarantee AppKit event routing.

## Tests

```bash
python -m pytest tests/test_ide_drag_all_free_toolbar_and_sticky_project.py \
 tests/test_ide_native_v4.py tests/test_ide_pycharm_chrome.py -q
python -m pytest -q
git diff --check
```

# Responsive Workspace, Visual System and Accessibility — Design Gate

## Scope and status

One engineering pass addresses (1) compact desktop navigation, (2) a shared
workspace spacing/size scale, and (3) keyboard navigation and native accessible
names. It does not imply full visual parity between AppKit and Qt.

## Responsive workspace

PYNIX GUI currently has no public portable window-size event in application
state. Automatic breakpoints would silently create separate navigation trees
while desktop resize is in progress. Instead, this release uses a discoverable
manual compact-navigation toggle visible in every workspace. It removes the
fixed-width sidebar from the semantic tree, leaving the main content in a fill
container. The toggle and native menu shortcut restore the sidebar.

The application preserves its current page and editable state across the
toggle. The default remains the familiar full-sidebar experience. Small
windows may still require scrolling for wide tables, grids and canvases:
these remain separate responsive work.

## Visual system

New WORKSPACE_METRICS in design.py holds the reusable sidebar range, page
inset and header/section gaps. A consistent page heading and navigation
disclosure form a stable top-level rhythm on every Gallery screen. Existing
PYNIX Standard palette and component semantic roles stay unchanged rather
than receiving unreviewed global restyling.

## Keyboard and accessibility

Native application menus expose shortcuts for Overview (primary+1), Start
Here (primary+2), Controls (primary+3), Data Views (primary+4), Dashboard
(primary+5), IDE (primary+6), and navigation toggle (primary+0).

Buttons carry their visible semantic label as an accessible name in Qt and
on supported AppKit APIs. This is groundwork, **not** an accessibility
certification. Full VoiceOver/Narrator, tab order, focus indicator contrast,
screen reader role/value and keyboard traversal still require native QA.

## Tests and acceptance

- Validate full and compact gallery trees; assert no navigation is lost.
- Validate all pages with compact mode, including editable screens.
- Check shared visual metrics and discoverable instructions.
- Run macOS, Windows and Ubuntu CI.
- Verify on a real Mac: toggle navigation, continue editing, switch pages,
  use menu shortcuts, resize window, test both light/dark.

## Follow-up requirements

True responsive breakpoints require a portable semantic RESIZE event or host
layout policy. Reflowing dashboard grids and inspector columns will require
constraint-aware child ordering. Cross-platform visual screenshots remain a
release gate.

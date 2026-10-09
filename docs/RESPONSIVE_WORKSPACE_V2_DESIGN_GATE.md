# Responsive Workspace V2 — Design Gate

Automatic navigation mode is driven by semantic `GUIEvent("RESIZE", width, height)`.
AppKit's resize delegate and Qt's main window notify the application; adjacent
resize events are coalesced. The gallery rerenders only when crossing its
1020-point breakpoint, not on each pixel during dragging.

## Invariants
- Default desktop opens the sidebar.
- Below the threshold it hides automatically, leaving a full-width viewport.
- Growing restores the desktop sidebar.
- A user toggling navigation creates an explicit override for that session.
- Page and editing state live independently of navigation selection.
- Existing buttons and keyboard menu commands remain available.
- Resize events are advisory: PYNIX layout still checks minimum extents.
- PYNIX app code owns responsive decisions; native backends only report size.

## Limitations and acceptance
- Desktop Gallery's wide Canvas, grids and inspector panels do not fully
  reflow at small widths. Hiding sidebar makes more space; it is not a
  complete narrow-window layout engine.
- Qt must be checked on a real Windows GUI. Headless CI is not pixel evidence.
- Mac acceptance: start with Overview, resize below/above threshold and
  verify sidebar collapse/reappear; check keyboard shortcuts, manual toggle,
  tab/controls content, no exceptions and no state loss.
- Assistive technology must see the navigation control in both modes.

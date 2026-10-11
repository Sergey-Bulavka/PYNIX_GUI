# PYNIX IDE Design System V2 — visual fidelity gate

Reference: the original compact IDE concept (left Explorer, center editor,
bottom tool window, pinned status bar), not the expanded gallery mockup.

## What is implemented in this branch
- Reusable `pynix_gui.ide_components` module with immutable chrome metrics.
- Shared command bar, tab-strip composition, tool window header and status.
- The shell showcase consumes those primitives; compiler integration stays frozen.
- Regression tests for widget contracts and initial-state presentation.

## Not yet accepted / missing platform work
- Tab strip is still composed from buttons. A true dedicated native tab-control
  skin and keyboard reordering are NOT implemented.
- Gutter is provisional and not attached to the native editor scrolling model.
- Activity rail currently uses simple text symbols, not licensed PYNIX SVG assets.
- Split resize/docking and native tool-window chrome need macOS-specific work.
- Preview only: no persistence, filesystem operations or compiler execution.

## Visual acceptance checklist
At 1440 × 900 and 1024 × 640 compare screenshot to the agreed concept:
- Explorer width about 256 logical pixels; centered disclosure arrows and icons
- Code editor is dominant region, not card-like; gutter scrolls with text
- Compact integrated title/toolbar and pinned status bar
- Tabs read visually as editor tabs, not generic pushbuttons
- Bottom panel default height around 190 px and collapsible
- No debug labels, decorative placeholders, clipping or dead action affordances
- State transitions after opening two tabs and toggling inspector/sidebar
- Native macOS menu and keyboard focus behavior

**Gate result:** pending user native acceptance. Automated tests are not
equivalent to approving screenshots. Do not merge until reviewed.

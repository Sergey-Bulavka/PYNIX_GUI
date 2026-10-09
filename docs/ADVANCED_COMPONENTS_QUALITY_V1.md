# Advanced Components Quality V1

This pass prioritizes reliable constrained windows over shrinking intrinsically
wide data or distorting a retained Canvas.

## Implemented
- Table and Tree screens (Data, Dashboard, IDE, File Manager) use local scroll
  viewports inside their cards.
- Rich Editor gets a local viewport boundary without changing its controlled
  text/selection IDs or intrinsic code area sizing.
- Canvas retains its logical scene size and hit coordinates and receives its
  own two-axis scroll viewport.
- Inspector/property rows retain existing native-glyph minimum constraints;
  inspector panels move below primary content through Responsive Content V1.

## Acceptance
On macOS test window at 1400, 1000, 690, and 560 logical points. Verify
table column visibility by scrolling locally, editor caret and selection,
canvas hit targets, and the inspector below primary content without missing
content. Check keyboard shortcuts and both scrollbar directions.

## Limits
- Scrollable wide content is not virtualized or column-priority reflow.
- Nested native scroll views need direct user testing for wheel routing.
- CI validates semantic trees, not true macOS/Windows visual interactions.

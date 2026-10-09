# Text Layout V2 — Native Pass Design Gate

## User need
Text must be fully readable and aligned in desktop GUI without application
developers manually tuning letter widths or platform-specific padding.

## Existing systems
AppKit uses NSString text extents and intrinsicContentSize; Qt uses
QFontMetricsF horizontalAdvance/height. Both work in logical coordinates, but
the exact font metrics vary between systems. Neither can guarantee that a text
label fits inside an arbitrarily constrained fixed-size parent.

## Native PYNIX solution
The existing V1 immutable snapshot is collected before a window/dialog layout.
The pure layout engine consumes that snapshot throughout one deterministic
geometry pass. Public GUI syntax remains unchanged.

For backward compatibility with existing hard max-size compositions, if
measured layout raises a size-constraint ValueError, the entire layout pass
uses the previously accepted deterministic fallback. The fallback is atomic:
no mixture of partially native and estimated geometry; other errors are
propagated. This is a safety mechanism, not proof that legacy text cannot clip.

## Current limit and next acceptance gate
Fixed-size compositions where native widths exceed allowed bounds need
first-class overflow policies (wrap, clip, ellipsize) and intrinsic-size
diagnostics. Until those exist, fallback cases can still show text clipping.
A future diagnostic should report affected text and limiting container.
Do not claim complete system-wide non-clipping from this milestone.

Mac hosts use native measurement only on actual macOS AppKit windows; fake
hosts retain the deterministic path. Windows Qt uses QFontMetricsF.
Native visual acceptance on macOS and Windows remains mandatory.

## Verification
Unit tests: success measured pass, fixed-size fallback, invalid constraints,
measurement failures, plus existing suite. GitHub CI on macOS, Windows, Linux.
Interactive smoke tests and screenshots catch pixel-level clipping.

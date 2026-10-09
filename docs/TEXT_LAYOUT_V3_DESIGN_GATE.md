# Text Layout V3 — Overflow Design Gate

## Goal
Native glyph widths must not force unrelated widgets outside a constrained
horizontal row. Product authors must choose overflow behavior explicitly.

## Public API
- `text(value, role, overflow="natural")`: existing intrinsic width guarantee.
- `overflow="ellipsis"`: minimum width is zero, preferred width is the
  full measured text. Native renderers show trailing ellipsis when clipped.
- `overflow="clip"`: same constraints, native renderers clip without ellipsis.
- Invalid overflow modes raise a GUI validation error.

## Native implementation
- AppKit labels use native NSLineBreakByTruncatingTail or
  NSLineBreakByClipping, no wrapping.
- Qt QLabel truncates using QFontMetrics.elidedText for each geometry pass
  based on *original* text; growing the window restores the full string.
- Fallback deterministic layout remains valid for synthetic tests.
- The full text stays in immutable GUIView. Truncation is rendering-only.

## Boundaries and deliberate deferrals
- This release does not implement multi-line `wrap`: correct wrapping
  requires width-first measurement, height-for-width negotiation, and
  vertical reflow across row/grid/split constraints.
- There is no global default truncation or implicit modification of current
  label contracts; callers opt in.
- Ellipsis may be invisible if the available width is smaller than the glyph.
- The native-first pass may still fall back on older fixed-size constraints.
- Visual verification is required for real macOS and Windows font rendering.

## Acceptance
Tests cover the default API, native preferred widths, shrinkable minimums,
neighbor boundaries, invalid policies, and resize/source-text invariance.
Existing smoke tests and GitHub CI must remain green.

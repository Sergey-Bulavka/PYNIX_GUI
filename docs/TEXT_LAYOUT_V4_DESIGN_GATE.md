# Text Layout V4 — Height-for-Width Design Gate

## Architectural finding

PYNIX's original Layout measures row and grid heights before assigning text
widths. Enabling native multi-line wrapping at render time alone would create
vertical overdraw: a text leaf grows visually, but the following row stays in
its old position. V3 truncation does not have this problem.

## Phase A: deterministic line measurement (implemented in this branch)

- `wrap_text` receives an explicit positive width, native-font width
  measurement function, and line height.
- Native AppKit/Qt adapters use NSString and QFontMetricsF to measure
  candidate strings, preserving platform-specific shaping decisions.
- The returned immutable `GUIWrappedText` contains the lines and total height.
- Explicit newlines, whitespace, oversized words and Unicode combining/ZWJ
  sequences are covered by isolated regression tests.
- The algorithm does not import a windowing framework or modify GUI widgets.

## Phase B: geometry integration (blocking production rollout)

Before exposing `overflow="wrap"` as a public accepted mode:

1. Determine child widths first; query height at *those exact widths*.
2. In Row, take the maximum child height; in Column, distribute recomputed
   heights sequentially; in Grid, use the maximum height per grid row.
3. Propagate height demands through padding, surfaces, tabs, align and
   scroll. Define overflow and impossibility behavior for constrained parents.
4. Ensure the text leaf has an actual multi-line native rendering frame
   with consistent line spacing. Re-layout on resize and font changes.
5. Test very long words, emoji grapheme clusters, embedded newlines,
   nested grids and rows, scrollable content and minimum/maximum bounds.
6. Confirm product gallery and native macOS/Windows renderers interactively.

No platform promises can be made based on headless line-breaking tests alone.

## Unicode caution

The grapheme splitter is a conservative approximation; it groups combining
marks, variation selectors and ZWJ sequences but is not full UAX #29 Unicode
grapheme segmentation. Production wrapping should defer to native line
breaking (CoreText/TextKit or Qt QTextLayout) for exact clusters, bidi and
complex scripts, with results materialized into an immutable snapshot.

## Decision

Do not prematurely connect the V4 measurement layer to product views or
change existing V3 overflow behavior until Phase B's geometry contract has
tests and macOS/Windows acceptance.

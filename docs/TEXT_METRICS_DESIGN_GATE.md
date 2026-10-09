# Text Metrics V1 — Design Gate

## Problem

The deterministic PYNIX GUI layout engine historically estimated text width
from character count. On macOS, `Commands` measured 58.24 logical points by
that estimator versus 71.5 points by the native NSTextField. Adding padding
to individual labels masked rather than solved the problem.

## Existing approaches

- **AppKit:** NSFont/NSString glyph metrics and intrinsicContentSize, tied to
  current font, locale, and native scale.
- **Qt:** QFontMetricsF provides horizontalAdvance and font height.
- **Typical retained layout engines:** derive constraints from text shaping and
  cache measurements for an immutable layout/render pass.

Neither platform-specific font objects nor mutable global caches should be
exposed through the PYNIX language.

## PYNIX design

1. A host collects distinct (typography role, text) pairs from a GUI tree.
2. It measures them with native font metrics on the UI thread.
3. It builds an immutable `GUITextMetrics` snapshot.
4. The pure `measure(view, text_metrics=...)` and
   `layout(view, width, height, text_metrics=...)` functions use that same
   snapshot for the entire pass. The snapshot can be reused, logged, tested,
   or replayed; no host GUI types enter the model.
5. Missing entries continue to use the accepted deterministic fallback.

Text extents are native logical points, not raw device pixels. A two-point
cell allowance is included in measured layout width for rounding. Font role,
content, and measured metrics are explicit. This means geometry is
deterministic **for a given snapshot**, not falsely identical across OS fonts.

## Acceptance and rollout gate

The snapshot contract is additive in this milestone. Existing runtime layout
calls retain their fallback path until native measured constraints can be
validated against existing max-size wrappers, viewport resizing, and both
platform hosts. A subsequent integration milestone must handle constrained
text through an explicit overflow policy, never by silently overflowing
parents, or raising minimums that make valid galleries impossible.

Tests require snapshot immutability, deduplication, fallback compatibility,
font-role differentiation, metric validation, and deterministic measured
geometry. Platform native glyph visual tests remain a separate acceptance
gate. Never declare pixel correctness from headless CI alone.

## Non-goals

Font shaping implementation, automatic line wrapping, text elision semantics,
changing the public PYNIX language, and replacing native fonts.

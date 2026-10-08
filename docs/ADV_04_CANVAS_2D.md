# GUI-ADV-04 — Canvas 2D

## Status

**IMPLEMENTATION COMPLETE — consolidated verification pending.**

The retained scene model, semantic hit testing, macOS rendering, Windows rendering,
logical image-resource resolution and focused regression coverage are staged. Acceptance
and the 0.1.4-dev bump require the consolidated verification pass.

Target version after acceptance: **PYNIX GUI 0.1.4-dev**.

## Contract

Canvas is an immutable retained scene, not an immediate-mode drawing callback.

```text
GUICanvasScene
GUICanvasCommand
canvas(...)
canvas_line(...)
canvas_rect(...)
canvas_ellipse(...)
canvas_path(...)
canvas_text(...)
canvas_image(...)
canvas_clip(...)
canvas_transform(...)
```

Coordinates live in logical canvas units. The backend scales them to the available view
without exposing device pixels or native graphics contexts.

Supported retained primitives:

- line;
- rectangle;
- ellipse;
- polyline/closed path;
- text;
- image resource;
- rectangular clipping;
- translate/scale/rotate transforms.

Colors use PYNIX Standard semantic color roles rather than raw host colors.

A primitive may carry a unique semantic `hit_target`. Clicking such a primitive emits the
existing `GUIEvent("ACTIVATE", target=...)`. Pointer coordinates and native mouse events
remain backend details.

Canvas 2D is deliberately distinct from future GPU/3D APIs.

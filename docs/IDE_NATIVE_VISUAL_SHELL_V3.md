# Native PYNIX IDE Visual Shell V3

## Purpose
Resolve the recurring mismatch between the approved compact IDE sketch and the
button-heavy GUI component demo. This branch adds an **independent native AppKit
appearance preview** to settle visual fidelity before any IDE wiring.

## Run (macOS)
```bash
python -m examples.ide_native_visual_shell
```

This does not replace `examples.ide_shell_showcase`; both remain in their
respective roles. The new preview uses native AppKit vector paths for file,
folder, explorer, search, play and settings symbols, instead of text-only
stand-ins. Content is demonstration data only.

## What should be visible
- Single compact window with dark chrome, one title row and one command row
- Narrow left activity rail with vector icons
- Explorer tree sized for practical file navigation
- Edge-to-edge editor with integrated file tabs, breadcrumbs, line-number gutter,
  active row treatment, and syntax-colored PYNIX sample
- Bottom tool window with Problems / Output / Terminal / Debug Console strip
- Pinned colored status bar

## Limits explicitly kept
- All controls are **visual only**, no click/typing handling yet.
- The gutter is drawn alongside the content in one native view, so appearance
  alignment can be accepted without prematurely deciding editor scrolling APIs.
- This is a macOS visual-only prototype, not public GUI controls, Windows
  parity, a working editor, or proof of render/performance correctness.
- After visual acceptance migrate accepted geometry/painting into reusable
  PYNIX_GUI primitives and implement editor and panel interaction separately.

## Acceptance
Review macOS screenshots at 1440×900, 1280×800 and 1024×640.
Compare visually to the originally proposed dense PyCharm/VS Code-inspired
sketch, checking chrome height, explorer width, baseline alignment, tab
treatment, icon quality and source/terminal proportions.

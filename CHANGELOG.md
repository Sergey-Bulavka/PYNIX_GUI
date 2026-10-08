# Changelog

All notable PYNIX GUI product milestones are recorded here.

A version is listed as released/accepted only after its documented verification gate passes.
Implemented-but-unverified work stays under **Unreleased**.

## Unreleased

Implementation staged; consolidated verification pending:

- ADV-04 retained Canvas 2D:
  - lines, rectangles, ellipses, paths, text and images;
  - clipping and affine transforms;
  - shared scale-aware semantic hit testing;
  - macOS AppKit and Windows Qt rendering.
- ADV-05 Rich Editor:
  - controlled text and selection;
  - language-agnostic semantic spans;
  - editable/read-only modes;
  - native scrolling, caret, selection and keyboard behavior;
  - macOS NSTextView and Windows QPlainTextEdit realizations.
- logical resource pipeline:
  - images;
  - retained vector scenes;
  - SVG resources;
  - logical vector icons;
  - Canvas image-resource resolution.
- macOS product polish:
  - synthesized standard application menu;
  - interactive controls inside dialog content;
  - focus/event routing preserved across rerender.
- Windows parity backend:
  - Qt/PySide6 host;
  - native controls, Tree/Table, menus/dialogs, context menus;
  - native Scroll/Split;
  - split-position persistence;
  - drag/drop and docking events;
  - Canvas, Rich Editor and resources;
  - system Light/Dark resolution;
  - focus persistence across declarative rerender.
- cross-platform Showcase.
- typed Python package marker and consolidated public API reference.
- three-OS CI matrix and prepared macOS/Windows verification runners.
- PYNIX language bindings staged in the PYNIX repository.

Planned acceptance progression:

```text
0.1.4-dev  ADV-04 Canvas 2D accepted
0.1.5-dev  ADV-05 Rich Editor accepted
0.1.6-dev  resources + macOS product polish accepted
0.2.0-dev  Windows parity accepted
```

These version bumps must not be made until their verification evidence exists.

## 0.1.3-dev — ADV-03 accepted

- logical drag payloads;
- generic drag source/drop target wrappers;
- normalized DROP events;
- deterministic application-owned docking state;
- left/right/bottom/center docking regions;
- semantic dock targets and DOCK events;
- native macOS drag/drop acceptance.

## 0.1.2-dev — ADV-02 accepted

- Tree with stable node identity;
- controlled expansion and selection;
- Table with semantic columns and stable row identity;
- normalized identity-based selection events;
- native scrolling;
- macOS keyboard navigation;
- focus persistence after controlled rerender.

Acceptance evidence: 54 standalone tests plus native macOS Tree/Table smoke and keyboard gate.

## 0.1.1-dev — ADV-01 accepted

- MenuBar/Menu/MenuItem;
- semantic shortcuts;
- ContextMenu;
- Tooltip;
- Collapsible;
- Dialog lifecycle;
- command/transient event normalization.

Acceptance evidence: 39 standalone tests plus native macOS command/transient smoke.

## 0.1.0-dev — standalone foundation accepted

Five-layer architecture extracted from PYNIX:

1. Window/Core
2. Layout
3. Containers/Surfaces
4. Controls
5. PYNIX Standard Visual/Design System

The standalone runtime, geometry engine, design system and reference macOS backend became
the source of truth for GUI runtime ownership.

# Changelog

All notable PYNIX GUI product milestones are recorded here.

A version is listed as released/accepted only after its documented verification gate passes.
Implemented-but-unverified work stays under **Unreleased**.

## Unreleased

Pending acceptance work:

- native Windows parity verification;
- three-OS CI confirmation;
- PYNIX language-integration regression and real .pnx smoke.

## 0.1.6-dev — resources and macOS product polish accepted

- logical image resources;
- retained vector scenes;
- SVG resources;
- logical vector icons;
- Canvas image-resource resolution;
- synthesized standard macOS application menu;
- interactive controls inside dialog content;
- focus/event routing preserved across rerender;
- integrated commercial Showcase layout/polish acceptance.

Acceptance evidence: full standalone regression, resource/vector native smoke, integrated
Showcase PASS, and visual macOS product review.

## 0.1.5-dev — ADV-05 accepted

- controlled text and selection;
- language-agnostic semantic spans;
- editable/read-only modes;
- native caret, selection, scrolling and keyboard behavior;
- controlled rerender/selection restoration;
- native macOS Rich Editor realization.

Acceptance evidence: full standalone regression, native Rich Editor smoke and integrated
Showcase editor PASS.

## 0.1.4-dev — ADV-04 accepted

- retained lines, rectangles, ellipses, paths, text and images;
- clipping and affine transforms;
- scale-aware rendering;
- semantic hit targets;
- shared backend-neutral hit testing;
- native macOS Canvas realization.

Acceptance evidence: full standalone regression, native Canvas smoke and integrated
Showcase Canvas PASS.

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

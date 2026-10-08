# PYNIX GUI Advanced Phase

## Status

Design Gate for capabilities intentionally postponed until after the five core GUI layers.

GUI-01 through GUI-05 remain the complete foundational architecture:

1. Window / Core
2. Layout
3. Containers / Surfaces
4. Controls
5. Visual / Design System

This document does not create a sixth foundational layer. It defines higher-level desktop
capabilities built on the accepted five-layer base.

## Why this phase exists

The core GUI is now stable enough that advanced controls no longer need to invent their own
geometry, event, focus, theme, or native-host contracts.

That means advanced features can now be added as ordinary semantic GUI components instead
of becoming framework architecture.

## Priority order

### 1. Menus and transient UI

Highest priority because they are universal desktop concepts and immediately useful to
PYNIX_IDE and ordinary applications.

Target public concepts:

- MenuBar
- Menu
- MenuItem
- ContextMenu
- Dialog
- Tooltip
- Collapsible

Required semantics:

- logical command targets;
- ACTIVATE events through existing GUIEvent;
- keyboard shortcuts represented semantically, not as raw host key events;
- modal/non-modal dialog lifecycle without exposing native window handles;
- context menu attachment to a logical subtree;
- tooltip text/content without application-managed hover timers.

### 2. Tree and Table

Second priority because List is intentionally insufficient for hierarchical and tabular
data.

Tree must support:

- stable node identity;
- labels;
- child hierarchy;
- expanded identity set;
- selected identity;
- expansion and selection events;
- keyboard navigation;
- scrolling;
- deterministic rerender.

Table must support:

- semantic columns;
- row identity;
- cell text/value presentation;
- selected row identity;
- headers;
- column sizing;
- scrolling;
- keyboard navigation;
- deterministic rerender.

Neither API may expose NSTableView/NSOutlineView objects.

### 3. Drag/drop and docking

These are large interaction systems and are intentionally after Tree/Table because their
real requirements are easier to prove against structured views.

Drag/drop public semantics must describe:

- source identity;
- payload kind/logical value;
- destination identity;
- allowed operation;
- drop result.

Do not expose NSPasteboard, NSDraggingInfo, Win32 OLE, or toolkit-specific MIME mechanics.

Docking public semantics must describe logical regions and persisted layout state rather
than raw child windows.

### 4. Rich editor/content

A richer editor control is allowed only after general requirements are documented.

The target should be suitable for:

- source code;
- logs;
- structured plain text;
- potentially other text-heavy applications.

Do not make the public API PYNIX-language-specific.

## Explicitly not automatic next work

The following remain behind independent Design Gates even though they were listed as
deferred capabilities:

- animation framework;
- GPU/custom canvas;
- 3D;
- browser/web view;
- arbitrary CSS;
- raw native handles;
- deep accessibility customization.

The reason is not technical inability. Their public contracts are expensive and can distort
the otherwise disciplined GUI API if introduced without concrete pressure.

## First milestone

The first implementation milestone is:

```text
GUI-ADV-01 — Menus and transient UI
```

Planned capability set:

```text
MenuBar
Menu
MenuItem
ContextMenu
Dialog
Tooltip
Collapsible
```

It must reuse:

- accepted GUIView composition;
- existing layout rules;
- GUIEvent ACTIVATE;
- semantic targets;
- PYNIX Standard Light/Dark/System;
- existing enabled/focus concepts;
- native accessibility behavior.

No raw native handles or new event model are justified by this milestone.

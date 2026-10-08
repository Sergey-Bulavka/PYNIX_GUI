# PYNIX GUI Product Scope

## Product position

PYNIX GUI is a first-class product of the PYNIX ecosystem.

It is not an IDE-specific compatibility layer and it is not considered complete merely
when PYNIX_IDE can be assembled from it.

The product goal is a complete, commercially credible desktop GUI toolkit whose public API,
internal architecture, default appearance, documentation, testing, examples and platform
backends are strong enough to represent the PYNIX language publicly.

## Completion principle

PYNIX_IDE development remains paused until the GUI product reaches its own completion gate.

The GUI must be finished both:

- externally: coherent commercial-grade visual design, complete control family, predictable
  interaction, themes, accessibility defaults, documentation and showcase;
- internally: deterministic layout, event normalization, state/reconciliation contracts,
  resource handling, backend boundaries, tests, versioning and portability architecture.

IDE convenience is never an excuse for an IDE-specific primitive.

## Product layers already accepted

The foundational architecture remains five layers:

1. Window / Core
2. Layout
3. Containers / Surfaces
4. Controls
5. Visual / Design System

These are the stable base, not the entire final product.

## Full desktop capability target

### Structural and data controls

- Tree
- Table
- List
- Tabs
- Scroll
- Collapsible

### Commands and transient UI

- MenuBar
- Menu
- MenuItem
- ContextMenu
- Dialog
- Tooltip
- command-oriented Toolbar
- structured StatusBar

### Workspace systems

- Split
- Dock / ToolPanel
- Drag & Drop
- reorder semantics
- persistent workspace state

### Drawing and custom presentation

- Canvas 2D
- paths/lines/rectangles/ellipses
- text/image drawing
- clipping
- transforms
- semantic hit targets
- scale-aware rendering

Canvas 2D is part of the product target and is distinct from a future GPU/3D subsystem.

### Text-heavy applications

- richer text/editor control
- caret and selection
- read-only and editable modes
- line/column navigation
- language-agnostic styling spans
- large-document behavior

The control must remain general-purpose and must not be tied specifically to PYNIX source
code.

### Media and resources

- raster images
- SVG/vector icons
- logical icon identities
- scale-aware assets
- deterministic packaged resource lookup

### Visual system

PYNIX Standard must remain the canonical cross-platform design language:

- Light
- Dark
- System
- semantic colors
- typography
- spacing
- radii
- borders
- focus
- selected
- disabled
- hover
- pressed
- success/warning/error/info

Applications must look professional without custom styling.

## Portability target

PYNIX GUI must have a platform-independent public contract.

Backend roadmap:

1. macOS / AppKit — reference and currently verified backend;
2. Windows — required before broad cross-platform completion claims;
3. Linux — planned after the Windows backend reaches parity.

Backend-specific objects are never public PYNIX values.

## Repository direction

The GUI has reached the point where independent repository ownership is justified.

Target repository:

```text
Sergey-Bulavka/PYNIX_GUI
```

The GUI repository owns:

- platform-independent GUI runtime/model;
- layout engine;
- design system;
- advanced controls;
- platform backends;
- GUI tests;
- GUI docs;
- showcase/examples;
- GUI component version.

The PYNIX language repository retains:

- language/compiler integration;
- `GUI.*` static typing/semantic declarations;
- stdlib binding/adapter layer;
- compatibility tests proving the external GUI runtime matches the language contract.

## Release model

PYNIX GUI is independently versioned.

Current development line begins from the already declared:

```text
PYNIX GUI 0.1.0-dev
```

Repository separation must not reset the component version or erase accepted milestone
history.

## Commercial-quality gate

PYNIX GUI is not considered complete until:

- foundational five-layer contract remains green;
- agreed advanced desktop controls are accepted;
- Canvas 2D is accepted;
- resource/vector pipeline is accepted;
- PYNIX Standard visual quality is accepted;
- macOS backend passes full showcase;
- Windows backend reaches defined parity;
- public documentation and examples are usable without reading compiler internals;
- full regression and integration contract with PYNIX is green.

Only then should PYNIX_IDE resume as a consumer of the finished toolkit.

## Still separate Design Gates

These are not required merely because the GUI is commercially complete:

- GPU rendering API;
- 3D scene system;
- browser/WebView;
- arbitrary CSS compatibility;
- raw native handles.

They are separate products/capabilities unless concrete requirements justify bringing them
into the GUI contract.

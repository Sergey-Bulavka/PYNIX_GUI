# PYNIX GUI Product Completion Gate

## Status

**macOS REFERENCE-BACKEND GATE ACCEPTED — PYNIX GUI 0.1.6-dev**

Standalone regression, native Advanced smokes, PYNIX language integration and the original
engineering Showcase passed on the reference macOS/AppKit backend. Three-OS CI is also
accepted. The Commercial Product Pass v1 is active before final real Windows parity.

The toolkit must not be called commercially complete until every required gate below is green.

## Accepted foundation

- GUI-01 Window/Core
- GUI-02 Layout
- GUI-03 Containers/Surfaces
- GUI-04 Controls
- GUI-05 PYNIX Standard Visual/Design System
- ADV-01 Commands/Transient UI
- ADV-02 Tree/Table
- ADV-03 Drag/Drop/Docking

## Accepted on macOS reference backend

- ADV-04 retained Canvas 2D
- ADV-05 Rich Editor
- logical image/retained-vector/SVG resource catalog
- macOS product polish
- integrated Showcase

## Accepted automated/integration evidence

- three-OS CI regression matrix;
- PYNIX language integration on macOS;
- real PYNIX-source AppKit smoke including continuous Rich Editor focus.

## Active commercial product pass

- Design System 2;
- high-level commercial composition components;
- navigable Product Gallery;
- richer AppKit/Qt semantic styling.

These changes require a new macOS visual/product acceptance pass after implementation.

## Implemented, verification pending

- real interactive Windows Qt/PySide6 parity acceptance.

## Commercial completion requirements

### API

- no native handle leaks;
- immutable retained application values where practical;
- controlled state for selection, expansion, editor state and docking;
- stable logical identities;
- semantic events;
- semantic design roles;
- diagnostics remain PYNIX-GUI-xxx rather than backend exceptions.

### Desktop interaction

- mouse;
- keyboard;
- focus preservation;
- scrolling;
- native menus and shortcuts;
- dialogs;
- drag/drop;
- context menus;
- tooltips;
- selection and editing.

### Advanced controls

- Tree;
- Table;
- Dock workspace;
- Canvas 2D;
- Rich Editor.

### Resources

- logical image names;
- vector resources;
- backend-side resolution;
- packaged application resources do not require native image objects in source code.

### Platforms

macOS/AppKit is the reference backend.

Windows parity must pass native acceptance before the product may claim Windows support.

Linux core/layout/tests may run in CI, but native Linux support remains a separate future
backend gate and is not implied by portable model tests.

### Quality

- full regression green;
- no unexpected warnings;
- all native smokes green;
- Showcase green;
- README/docs synchronized;
- component version bumped only after corresponding acceptance evidence exists.

## Version progression

Accepted versions:

```text
0.1.0-dev  five-layer standalone foundation
0.1.1-dev  ADV-01 Commands / Transients
0.1.2-dev  ADV-02 Tree / Table
0.1.3-dev  ADV-03 Drag / Drop / Docking
0.1.4-dev  ADV-04 Canvas 2D
0.1.5-dev  ADV-05 Rich Editor
0.1.6-dev  Resource pipeline + macOS product polish
```

Pending after verification:

```text
0.2.0-dev  Windows parity accepted
```

The exact later bump may be collapsed if a consolidated acceptance deliberately accepts
multiple pending product layers together, but accepted history must remain documented.

## IDE gate

PYNIX_IDE remains paused until the GUI product-completion gate is accepted.

Passing enough GUI features to build an IDE is not the same as finishing the GUI product.

# PYNIX GUI

Commercial-grade desktop GUI toolkit for the PYNIX programming language.

> **Status:** active extraction and independent product development.
>
> Component version: **0.1.0-dev**

PYNIX GUI is a first-class product of the PYNIX ecosystem. It owns the platform-independent
GUI model, deterministic layout engine, PYNIX Standard design system, advanced desktop
controls, platform backends, examples/showcase, documentation, and GUI-specific tests.

The PYNIX language continues to expose the simple public surface:

```pynix
GUI.button(...)
GUI.table(...)
GUI.canvas(...)
```

Repository separation is an internal engineering boundary. It must not make PYNIX source
code more complicated.

## Product principles

- **Complex ideas. Simple solutions.**
- **Complex inside. Simple outside.**
- Predictable geometry before decoration.
- Semantic styling before arbitrary per-widget paint.
- Native accessibility and platform integration without leaking native handles.
- Commercial-quality defaults without requiring application-authored styling.

## Architecture

The accepted foundation has five layers:

1. Window / Core
2. Layout
3. Containers / Surfaces
4. Controls
5. Visual / Design System

Advanced desktop capabilities are built on top of that foundation:

- Tree and Table
- MenuBar / Menu / ContextMenu
- Dialog and Tooltip
- advanced Toolbar / StatusBar
- Dock / ToolPanel
- Drag & Drop
- Canvas 2D
- richer editor/content controls

## Platform direction

- macOS / AppKit — current reference backend
- Windows — required parity target
- Linux — planned after Windows parity

## Repository extraction

The accepted GUI implementation is being migrated from
`Sergey-Bulavka/PYNIX` without a rewrite. During extraction both repositories retain
compatibility coverage until PYNIX can consume this package through a narrow adapter.

The component version remains **0.1.0-dev**; repository separation does not reset history or
milestone status.

## License

Apache-2.0.

# PYNIX GUI

Commercial-grade desktop GUI toolkit for the PYNIX programming language.

> **Status:** macOS reference backend and PYNIX language integration are accepted through
> 0.1.6-dev. The Commercial Product Pass v1 is active. Automated CI is green on macOS,
> Windows and Ubuntu; real interactive Windows acceptance remains pending.
>
> Component version: **0.1.6-dev**

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
- commercial composition components (card, hero, metrics, badge, alert, navigation, forms)
- Product Gallery for capability discovery and visual acceptance

## Platform direction

- macOS / AppKit — reference backend
- Windows / Qt (PySide6) — parity backend implemented, native verification pending
- Linux — core/layout regression target; native backend planned after Windows parity acceptance

## Repository extraction

The accepted GUI implementation is being migrated from
`Sergey-Bulavka/PYNIX` without a rewrite. During extraction both repositories retain
compatibility coverage until PYNIX can consume this package through a narrow adapter.

The accepted macOS reference-backend component version is **0.1.6-dev**:
ADV-04 Canvas 2D, ADV-05 Rich Editor, logical resources, macOS product polish and real
PYNIX-language integration are accepted. The active Commercial Product Pass adds Design
System 2, a high-level composition layer and the Product Gallery before the final Windows
native parity gate.

## License

Apache-2.0.


## Verification

Prepared runners:

```bash
bash scripts/verify_macos.sh tests
bash scripts/verify_macos.sh smokes
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_windows.ps1 -Mode All
```

See `docs/VERIFICATION_PLAN.md` and `docs/PRODUCT_COMPLETION_GATE.md`.

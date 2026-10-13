# PYNIX GUI

Commercial-grade desktop GUI toolkit for the PYNIX programming language.

> **Status:** macOS reference backend and PYNIX language integration are accepted through
> 0.1.6-dev. Text Layout V1–V4, Product Gallery, Responsive Workspace V2,
> Responsive Content V1 and Advanced Components Quality V1 are implemented and
> have macOS user acceptance. Automated CI runs on macOS, Windows and Ubuntu;
> interactive Windows/Qt parity remains pending.
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

## Active IDE workspace and prototype boundaries (2026-10-13)

The interactive **Workspace V4** currently lives on
`feature/icon-system-v4`, in `examples/ide_native_v4.py`. It is a macOS
WKWebView-based **integration/acceptance prototype**, not the shipped PYNIX_IDE
application or the public cross-platform GUI widget API. It uses
`examples/icon_direction_preview.html`, `pynix_gui/ide_workspace_session.py`,
`pynix_gui/ide_workspace_preview.py`, and the existing navigation/diagnostics
bridges. Opened files, editing, saving and compiler navigation have real
integrations, but remaining workspace panels may still be previews.

The native File/Edit/Navigate menu is installed by
`pynix_gui/ide_native_menu.py`; selections dispatch to the *existing* WebView
actions. The menu foundation in `pynix_gui/commands.py` remains the general
GUI toolkit contract and must not be replaced by an IDE-specific version.

Launch from this branch on macOS:

```bash
./.venv/bin/python -m examples.ide_native_v4 \
  --project /Users/morphey/PycharmProjects/PYNIX \
  --compiler-python /Users/morphey/PycharmProjects/PYNIX/.venv/bin/python
```

The old `examples/ide_native_visual_shell.py` is a historical visual
prototype; `examples/adv_01_commands_smoke.py` is an essential menu regression
smoke, **not** an IDE window. `PYNIX_IDE/src/gui.pnx` is an older standalone
Desktop frontend retained for compatibility and tests.

**Next engineering work:** verify the new V4 menu on macOS; preserve its
existing shortcuts and command behavior; add tests for enabled/disabled states,
menu/shortcut parity and save conflicts; then graduate V4 from prototype to a
single officially launched IDE application using the public GUI contract.
Do not delete historical branches or prototypes until unique commits,
dependency references and tests are audited.

See `docs/IDE_WORKSPACE_CONSOLIDATION_2026-10-13.md`.

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

See `docs/VERIFICATION_PLAN.md`, `docs/PRODUCT_COMPLETION_GATE.md`, and
`docs/STABILITY_RELEASE_READINESS_2026-10-10.md` for evidence and release blockers.

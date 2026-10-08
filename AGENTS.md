# PYNIX GUI Development Rules

These rules apply to the standalone PYNIX GUI toolkit.

1. PYNIX GUI is a first-class product, not an IDE-specific helper.
2. Preserve the five-layer foundation: Core, Layout, Surfaces, Controls, Design System.
3. Advanced capabilities must reuse accepted geometry/event/theme contracts instead of inventing parallel systems.
4. Never expose AppKit, WinUI, GTK, Qt, or other native handles as public PYNIX GUI semantics.
5. Prefer semantic roles and logical events over raw styling or platform events.
6. Commercial-quality defaults are required; applications should look professional without custom styling.
7. Public semantics must remain platform-independent. Backend differences are implementation details.
8. New substantial capabilities require a Design Gate before implementation.
9. Use coherent implementation batches with grouped focused tests, then subsystem regression and native acceptance.
10. Do not weaken the PYNIX language surface merely because runtime code now lives in a separate repository.
11. PYNIX and PYNIX_GUI version independently. Current GUI component version is 0.1.0-dev.
12. PYNIX_IDE remains paused until the GUI product completion gate is met.
13. Project mottos: "Complex ideas. Simple solutions." and "Complex inside. Simple outside."
14. Treat Tree, Table, menus, dialogs, tooltips, docking, drag/drop, Canvas 2D, richer editor/content, vector/raster resources, and cross-platform backend parity as product work, not IDE-specific hacks.
15. GPU/3D, WebView, arbitrary CSS, and raw native handles require separate Design Gates.

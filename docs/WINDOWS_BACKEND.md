# Windows Backend

## Status

Implementation complete enough for parity verification; native Windows acceptance pending.

## Host

The Windows backend is private Qt/PySide6 realization selected by:

```python
from pynix_gui.backends import default_backend
backend = default_backend()
```

On Windows this returns `WindowsGUIBackend`.

PySide6 is a conditional Windows dependency and does not affect macOS installations.

## Contract

The Windows backend implements the same public PYNIX GUI semantics as the AppKit backend:

- Window lifecycle and logical events;
- Row/Column/Grid/Stack and deterministic layout;
- controls;
- Tree/Table;
- MenuBar and Dialog;
- Tooltip and Collapsible;
- Drag/Drop and Dock semantic events;
- retained Canvas 2D;
- Rich Editor;
- logical image/vector resource catalog.

Qt objects remain private implementation details.

## Acceptance gate

Windows parity is not accepted merely because the module imports. Native Windows verification
must prove:

1. window opens and closes cleanly;
2. PYNIX Standard visuals remain coherent;
3. controls emit normalized events;
4. Tree/Table keyboard behavior works;
5. menu shortcuts work;
6. modal dialogs work;
7. drag/drop and docking work;
8. Canvas renders and semantic hit targets activate;
9. Rich Editor edits, selects and scrolls;
10. Light/Dark rendering remains readable;
11. no Qt object appears in the application-facing API.

Linux does not inherit this acceptance merely because Qt is portable. Linux remains a
separate future backend/product gate.

# macOS Native Acceptance

## Standalone smoke

The native macOS acceptance probe must be executed from the standalone PYNIX_GUI checkout,
without adding the PYNIX compiler repository to PYTHONPATH.

Command:

```bash
cd /Users/morphey/PycharmProjects/PYNIX_GUI
source .venv/bin/activate
python examples/macos_smoke.py
```

Expected behavior:

1. a native macOS window titled `PYNIX GUI — Standalone Smoke` opens;
2. PYNIX Standard System styling is applied;
3. title/body typography are visible;
4. focused text field is visible;
5. primary, secondary, danger, and disabled button states are distinct;
6. closing the window queues a logical `CLOSE` event;
7. the process prints:

```text
PYNIX GUI standalone macOS smoke: PASS
```

This proves the runtime path:

```text
PYNIX_GUI
→ GUIRuntime
→ MacOSGUIBackend
→ MacOSHostBackend
→ AppKit
```

without importing the PYNIX compiler or legacy Desktop runtime.

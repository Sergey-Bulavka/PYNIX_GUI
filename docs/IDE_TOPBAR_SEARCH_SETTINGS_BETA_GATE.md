# IDE top bar: Search Everywhere / Settings / Beta gate

## User task
Align the right portion of the PYNIX IDE title bar with the PyCharm reference:
a discoverable Search Everywhere control with its help tooltip, an IDE and
Project Settings control with an updates indicator, and a green outlined beta
status label instead of a trial-subscription button.

## Design Gate

Reference ideas:
- PyCharm/IntelliJ: one search entry point for files, symbols, actions,
  tool windows and settings; a compact settings gear with update status.
- VS Code: Quick Open and Command Palette route to the same actual editor
  and command targets rather than implementing duplicate behavior.

Avoid copying third-party icons, hard-coding availability signals, rendering
a paid-upgrade CTA in a beta IDE, or teaching the GUI toolkit IDE-specific
filesystem, compiler or update-service behavior.

## Implementation

The native macOS visual prototype shows the compact single-row geometry,
original vector magnifier and gear, demonstration update dot and a green
*outlined* `Beta Version · 1.1.26-dev` chip. It remains **visual-only**.

The existing interactive shell preview now has:
- Search Everywhere tooltip describing Classes, Files, Tool Windows,
  Actions and Settings, with search over known preview files and symbols.
- A shared target route: picking a result opens the relevant file, tool
  window, action or settings page (only if it is a currently offered result).
- Settings and updates tooltip. An update dot is displayed only when the
  `updates_available` state is true; it is false by default because no
  update provider is wired.
- A beta status indicator with the documented PYNIX_IDE version.
  PYNIX_GUI's package version is deliberately not substituted.
- Explicitly labelled preview behavior for debug, settings and update checks.

The toolkit's current semantic `badge` renders a filled success badge,
not a stroked pill, so the interactive showcase is **not yet pixel-identical**;
the native visual preview covers the requested outline geometry. A reusable
outlined-status control belongs to a separate public GUI control review.

## Non-goals
- JetBrains intellectual property/icon assets
- Production project indexing or arbitrary class lookup
- Actual remote updates or updater notifications
- Changing the IDE Core API or the PYNIX language

## Acceptance
- Native screenshots at 1024, 1280 and 1440 widths
- Tooltip behavior and search result routing in the interactive preview
- No update indication when update state is unknown
- Both IDE and GUI versions kept distinct
- No source execution implied by visual Run/Debug buttons

## Test commands
```bash
python -m pytest tests/test_ide_shell_showcase.py tests/test_ide_native_visual_shell.py -q
python -m pytest -q
git diff --check
```

# Workspace V4: Search Everywhere, IDE Settings and Beta Version

## Correct application

The supported ongoing macOS UI acceptance entry point is:

```bash
python -m examples.ide_native_v4 --project /path/to/PYNIX
```

It is **not** `examples.ide_native_visual_shell` or
`examples.ide_shell_showcase`, which are older, separate examples.
The active V4 development branch is `feature/icon-system-v4`; this
change is based on that branch. See
`docs/IDE_WORKSPACE_CONSOLIDATION_2026-10-13.md`.

## Design Gate

**Task:** match the supplied PyCharm toolbar search/settings/status treatments,
preserving the existing V4 project identity, live Git branch, Current File
selector and Run/Debug/More Actions behavior.

**Existing reference solutions:** JetBrains Search Everywhere unifies content
and commands; VS Code Quick Open and Command Palette unify navigation without
inserting a new file/editor backend.

**Avoid:** recreating the old visual mock, a second project/file index, fake
update availability, an irrelevant trial-subscription CTA, or replacing
existing run/debug listeners.

**Native V4 solution:**
- The existing search icon now opens a keyboard-navigable Search Everywhere
  overlay; double Shift opens it too.
- Search covers actual V4 files, simple class/function declarations from
  loaded in-memory buffers (including unsaved changes), and actions/tool
  windows already available in the running workspace.
- Selecting a file or declaration calls the real V4 source-opening API;
  declarations also request positioning at the definition line.
- The settings gear opens the PyCharm-like top-right **menu**. Its Settings…
  item (and macOS Command+,) opens a **separate native NSWindow**, not the old
  sixth rail tool window. Search Everywhere → Settings uses the same route.
- Native Settings V1 has functional Editor → Font size and line-height,
  persisted atomically in the current macOS user's Application Support/PYNIX.
  Other categories currently provide navigable structure and explicitly
  identify unimplemented controls; they do not pretend to work.
- The gear's yellow update dot appears only for
  `window.pynixIDEUpdatesAvailable === true`; no update provider is wired,
  and the default is no notification.
- The old trial-status position now holds a green **outlined** non-clickable
  `Beta Version · 1.1.26-dev` status. This is the documented
  PYNIX_IDE version, **not** the independent PYNIX_GUI package version.
- The delegated native tooltip supports multiline explanatory Search
  Everywhere content, while preserving hover/focus behavior.
- Default V4 mode retains both actual toolbar SVG glyphs.

## Boundaries and limitations

- Lightweight class/function declaration scanning is not full PYNIX semantic
  indexing. It omits unloaded files' symbols, scopes, inheritance and
  cross-language semantic resolution. Files still show in results.
- Run, Debug, Save, settings and tool windows delegate to existing handlers;
  this change does not broaden their backend capabilities.
- No automatic update service or version comparison is implied.
- This is acceptance work in PYNIX_GUI's temporary V4 host, not a new public
  generic toolkit API.

## Acceptance

1. Launch **V4**, not either old preview.
2. Inspect search/settings/beta top right in dark/light/compact layouts.
3. Hover search: categories and Shift shortcut appear.
4. Search by filename/function; activate by mouse and Enter; close by Escape;
   navigate results by arrow keys; double Shift opens the palette.
5. Search Settings, Run, Debug and Save: results dispatch existing controls.
6. Edit an in-memory file and confirm symbols search without saving.
7. No update dot is shown absent a genuine status signal.
8. Recheck project/branch/current file/Run/Debug/More Actions and dragging.
9. Run focused and complete regressions; perform manual macOS visual
   acceptance before merging.

## Commands

```bash
python -m pytest tests/test_ide_search_everywhere.py tests/test_ide_pycharm_chrome.py tests/test_ide_tooltips.py -q
python -m pytest -q
git diff --check
```

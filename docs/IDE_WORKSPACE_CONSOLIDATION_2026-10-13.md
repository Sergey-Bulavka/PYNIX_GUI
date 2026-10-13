# PYNIX ecosystem IDE consolidation — 2026-10-13

## Design Gate: the actual problem

The user expects a *single* evolving IDE, with its application menus and
keyboard shortcuts tied to the same real actions. Multiple experiments have
created confusing launchers, separate repository histories and stale docs.
The goal is to clarify ownership and consolidate without discarding work.

## Audited locations

| Project | Current role | Facts from repository |
| --- | --- | --- |
| PYNIX | language/compiler/public Desktop runtime | `compiler/desktop.py` does not yet expose the standalone ADV-01 native menu contract |
| PYNIX_GUI | reusable GUI toolkit | `pynix_gui/commands.py` exposes menu/shortcut model; macOS and Windows backends exist |
| PYNIX_GUI feature/icon-system-v4 | active Workspace V4 acceptance prototype | `examples/ide_native_v4.py` hosts WKWebView; `ide_workspace_preview.py` implements actual editor actions; `ide_native_menu.py` bridges system-menu entries to them |
| PYNIX_IDE main | legacy PYNIX-written Desktop Shell/TUI/GUI and IDE Core | `src/gui_main.pnx` launches an older UI; `src/ide_session.pnx` maintains independent IDE operations |

The older `examples/ide_native_visual_shell.py` is visual-only history, not
the production entry point. `adv_01_commands_smoke.py` demonstrates library
menus; retain it for regression evidence.

## Decision

1. Workspace V4 remains the **active macOS UX integration track** until
   native acceptance and migration decisions are complete.
2. PYNIX_GUI remains a general-purpose toolkit. Do not duplicate the
   `GUIMenuBar` domain model or embed IDE-specific business logic in it.
3. V4's raw WKWebView / AppKit adapter is a **temporary internal integration
   boundary**, not a new public PYNIX API. Menu commands delegate to existing
   browser actions.
4. `PYNIX_IDE` is the eventual IDE application owner; migration of V4
   interaction into a PYNIX-first application requires a separate Design Gate.
5. No claims that the legacy UI is obsolete in a technical sense until its
   test/compatibility responsibilities are accounted for.

## Work completed in the current branch

- Native menu adapter `pynix_gui/ide_native_menu.py`.
- V4 installation in `examples/ide_native_v4.py`.
- Existing JavaScript action reuse in `ide_workspace_preview.py`.
- Contract checks in `tests/test_ide_native_menu.py`.
- User screenshot confirms File/Edit/Navigate visible on macOS.
- **Automated tests for this change have not yet been reported by user.**

## Next milestones

### M1 — menu reliability
- Verify native menu actions and shortcuts on macOS (not only visibility).
- Preserve editor focus and ensure keyboard chords are not intercepted twice.
- Disable actions when unavailable or make no-op behavior explicit.
- Test dirty-save, save failure and navigation without active PYNIX source.
- No placeholder menu items pretending to be functional.

### M2 — converge command routing
- Introduce a single *application-level* command registry only if needed by
  two or more actual input surfaces; use existing toolkit event semantics.
- Avoid `PYNIX_IDE/src/gui.pnx` IDs being mistaken for V4's command registry.
- Validate menu/toolbar/shortcut behavior through shared tests.

### M3 — product launcher and ownership
- Design Gate for PYNIX-first ownership of Workspace V4.
- Add a supported IDE launch entry point, avoiding temporary manifest copies.
- Decide what legacy Desktop frontend must remain as a regression fixture.
- Update release/readiness documentation with real evidence.

### M4 — branch and code hygiene
- Compare every old branch against current main and active integration branch
  (merge-base, ahead/behind, unique commits, open PRs).
- Record branches in one of: **active**, **merged**, **historical archive**,
  **unique unmerged work**.
- Only remove remote branches that are merged/redundant and documented;
  preserve tags or archive refs for historical work. Deleting remote history
  before this check is prohibited.
- Treat source file deletions separately: inspect imports, smoke tests and
  compatibility contracts before removal.

## Validation commands (macOS, feature/icon-system-v4)

```bash
cd /Users/morphey/PycharmProjects/PYNIX_GUI
git pull --ff-only
./.venv/bin/python -m pytest \
  tests/test_ide_native_menu.py \
  tests/test_ide_native_v4.py \
  tests/test_advanced_commands.py \
  tests/test_macos_menu_key_equivalents.py -q
git diff --check
git status --short --branch
```

## Evidence limitations

GitHub branch names are not proof that changes were merged. The actual local
working tree and native macOS behavior cannot be inferred solely from GitHub.
Windows interactive parity remains an independent release gate.

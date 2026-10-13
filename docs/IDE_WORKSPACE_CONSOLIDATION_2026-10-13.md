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

## Sampled branch comparison against GUI main (2026-10-13)

The GitHub compare API returned:

| Branch | Relationship to main | Unique commits ahead | Behind |
| --- | --- | ---: | ---: |
| feature/ide-native-visual-shell-v3 | ahead | 43 | 0 |
| feature/ide-design-system-v2 | ahead | 18 | 0 |
| feature/ide-visual-foundation-v1 | ahead | 14 | 0 |
| fix/macos-menu-keyboard-shortcuts | diverged | 2 | 56 |

These counts show that **blind deletion would risk losing unique work**.
They do not establish whether the latest active branch already contains the
changes; compare against the integration branch, not just main, before any
archive/deletion. No remote branches have been deleted.

## Complete GUI branch ancestry audit against feature/icon-system-v4

GitHub compare results for **26 other branches** (27 branches including the
active V4). Ahead means commits in the compared branch absent from V4 by
ancestry, not necessarily unique functional behavior; cherry-picked changes
may already be equivalent.

| Branch | Ahead of V4 | Behind V4 | Classification |
| --- | ---: | ---: | --- |
| `feature/ide-native-visual-shell-v3` | 0 | 178 | Contained in V4 |
| `feature/ide-design-system-v2` | 0 | 203 | Contained in V4 |
| `feature/ide-visual-foundation-v1` | 0 | 207 | Contained in V4 |
| `feature/real-project-explorer-v1` | 0 | 246 | Contained in V4 |
| `feature/project-explorer-lazy-tree-v2` | 0 | 233 | Contained in V4 |
| `feature/commercial-gui-quality-pass` | 0 | 222 | Contained in V4 |
| `main` | 0 | 221 | Contained in V4 |
| `fix/macos-menu-keyboard-shortcuts` | 2 | 277 | Diverged; inspect |
| `feature/commercial-gallery-discovery-pass` | 5 | 279 | Diverged; inspect |
| `feature/workspace-responsive-visual-accessibility` | 7 | 278 | Diverged; inspect |
| `feature/advanced-components-quality-v1` | 3 | 274 | Diverged; inspect |
| `feature/ecosystem-integration-foundation` | 1 | 270 | Diverged; inspect |
| `feature/file-manager-interaction-v2` | 15 | 271 | Diverged; inspect |
| `feature/responsive-content-v1` | 11 | 275 | Diverged; inspect |
| `feature/responsive-workspace-v2-auto-resize` | 11 | 276 | Diverged; inspect |
| `feature/stability-release-readiness` | 6 | 273 | Diverged; inspect |
| `feature/text-layout-v2-native-pass` | 6 | 282 | Diverged; inspect |
| `feature/text-layout-v3-overflow` | 7 | 281 | Diverged; inspect |
| `feature/text-layout-v4-height-for-width` | 30 | 280 | Diverged; inspect |
| `feature/text-metrics-snapshot-v1` | 7 | 283 | Diverged; inspect |
| `feature/tree-explorer-visual-quality-v1` | 53 | 272 | Diverged; inspect |
| `fix/canvas-text-alignment` | 6 | 288 | Diverged; inspect |
| `fix/macos-label-glyph-overhang` | 3 | 284 | Diverged; inspect |
| `fix/macos-property-text-native-width` | 1 | 285 | Diverged; inspect |
| `fix/property-row-label-clipping` | 3 | 286 | Diverged; inspect |
| `fix/text-intrinsic-width` | 4 | 287 | Diverged; inspect |

**Seven historical refs have zero ahead commits** (including main). They can
be candidates for archiving once branch ownership, open PRs and default branch
safety are checked. The other nineteen are not verified duplicates. Do not
force-merge them or delete them based only on these numbers.

### Safe eventual cleanup

- Preserve the active V4 branch and the default `main` branch.
- Prefer preserving historical tags before pruning remote feature refs.
- Compare diverged branches by patch equivalence, tests and dependency impact.
- Keep standalone acceptance examples when they are needed by documented
  regression or platform gates, even if the UI is visually superseded.
- Only delete branches after a second read confirms the exact target ref and
  the repository owner approves the final classification.

## Diverged branch file-level triage (2026-10-13)

Compared representative high-impact diverged branches to V4, not just their
branch ancestry. The following files reported by older branches **already
exist** on V4: `pynix_gui/tree_visuals.py`,
`pynix_gui/wrap_engine.py`, `pynix_gui/height_for_width.py`,
`tests/test_open_event.py`, and
`tests/test_macos_menu_key_equivalents.py`.

This proves those capabilities have current *files*, **not** that their
implementations are byte-identical or satisfy the same behavioral contract.
Never copy over current V4 files from old branches.

| Historical branch | Changed-file areas | Decision |
| --- | --- | --- |
| `fix/macos-menu-keyboard-shortcuts` | macOS host + menu accelerator test | Compare key equivalent semantics and run native shortcut regression |
| `feature/file-manager-interaction-v2` | core, macOS/Windows backends, OPEN event test | Preserve current event contract, compare edge cases |
| `feature/tree-explorer-visual-quality-v1` | tree visuals, assets, backends, gallery tests | Keep current file/icon quality and run visual acceptance |
| `feature/text-layout-v4-height-for-width` | layout engine, wrap engine, backends, tests | Keep current layout, compare edge-case tests |
| `feature/commercial-gallery-discovery-pass` | showcase and gallery documentation/tests | Historical gallery track; check current showcase functionality |
| `feature/workspace-responsive-visual-accessibility` | style, backends, showcase and tests | Re-test responsiveness/contrast on V4 |

The safest next step is focused testing and reviewing actual diffs for these
areas before archiving diverged references. No branch deletion, file deletion,
or re-merge has been performed during triage.

## Source cleanup decision: retain regression fixtures (2026-10-13)

Inspected `examples/ide_shell_showcase.py` and
`tests/test_ide_shell_showcase.py`: the example is deliberately visual-only,
but its tests exercise the GUI toolkit's controlled panel state, tabs,
tree, layout sizing and menu model. It is **not** a redundant launch target.

Inspected `examples/ide_native_visual_shell.py` and
`tests/test_ide_native_visual_shell.py`: they preserve native AppKit icon,
palette, static Git panel and window lifecycle acceptance expectations.
Keep them as named regression fixtures, not as the current IDE.

`examples/adv_01_commands_smoke.py` is a general PYNIX_GUI menu smoke,
not an obsolete IDE executable; retain it.

**Concrete cleanup:** `scripts/run_ide_workspace.sh` is now the single
documented V4 preview launcher, with a project argument and explicit optional
compiler interpreter. Tests in `tests/test_ide_launch_contract.py`
guard this entry point and the historically required examples.

No source files were deleted: existing tests establish that these older
examples retain useful acceptance roles. The next retirement gate is to
replace their assertions with tests of the official application *before*
removing any fixture, not after.

## Official IDE migration decision (2026-10-13)

The cross-repository Design Gate is now in
`PYNIX_IDE/docs/WORKSPACE_V4_INTEGRATION_DESIGN_GATE.md`.
It confirms that `ide_workspace_session.py` and
`PYNIX_IDE/src/ide_session.pnx` are separate document owners. Migration must
establish the official IDE Core as the single owner before enabling writes
through a new frontend adapter. In particular, preserve V4's atomic save and
external-change protection while replacing its prototype session.

This is a migration decision, **not** a claim that V4 has been merged into
PYNIX_IDE. Keep the existing GUI regression examples and V4 launcher working
throughout the transition.

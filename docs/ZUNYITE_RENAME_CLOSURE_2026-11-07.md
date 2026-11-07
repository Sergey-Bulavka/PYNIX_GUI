# Zunyite rename closure audit — 2026-11-07

## Canonical public names

| Surface | Canonical | Legacy compatibility |
|---|---|---|
| Language | Zunyite | PYNIX historical name |
| Source files | `.uny` | `.pnx` |
| Project manifest | `zunyite.toml` | `pynix.toml` |
| Project lock | `zunyite.lock` | `pynix.lock` |
| CLI | `zuny` (`zu` alias) | `pynix` alias |
| Python GUI distribution | `zunyite-gui` | Prior distribution name |
| Python GUI import | `zunyite_gui` | `pynix_gui` |
| Compiler / debugger wire protocol | Existing versioned `pynix-*` IDs | Keep stable until a jointly versioned replacement |

## Completed in repository

- Maintained tutorial sources and project manifests use `.uny` / `zunyite.toml`.
- The GUI's interactive editor Block 2/3 and Core recovery acceptance
  scripts now generate canonical projects and discover sibling repositories
  without hard-coded developer usernames or old checkout paths.
- The live Debug bridge verifies both `.uny` and `.pnx` using the actual
  compiler worker.
- The GitHub Action for cross-repository debugger integration is named
  `zunyite-debugger-external.yml`, and its checkout is `zunyite-compiler`.
- Public GUI namespace `zunyite_gui` is available and used by the native
  first-party smoke/gallery examples.
- `zunyite_gui.wrap_engine` and `zunyite_gui.text_metrics` now own their
  implementations; `pynix_gui` exports the same classes and functions through
  legacy shims, preventing duplicate runtime types.
- Canonical `zunyite_gui.ide_*` imports now expose Workspace Session,
  Core Reader, Run, Debug and tooling as compatibility-preserving adapters.
  These IDE service implementations are **still housed in** `pynix_gui`;
  exposing canonical imports is not the same as completing their relocation.

## Explicitly preserved compatibility / history

- `pynix_gui` internal Python package and its WebView script handlers
  (`window.pynix*`): changing names without a simultaneous host/client and
  test migration would break the editor. This remains technical debt and
  **must not** be presented as a completed internal namespace migration.
- Versioned protocol identifiers `pynix-debug` and `pynix-tooling` remain
  unchanged so compiler, IDE Core, and GUI agree. A new wire name requires
  version/capability negotiation and integration tests first.
- Historical design notes and explicit compatibility regression cases may
  retain PYNIX terminology. Compiler `main` now contains **270 tracked `.uny`**
  files and only **5 tracked `.pnx`** files alongside **4 `pynix.toml`**
  manifests, all confined to `tests/conformance/projects/manifest_missing*`.
  The ordinary conformance corpus was migrated in merged PR #45 (173 programs),
  PR #46 (49 project sources, 20 manifests), and PR #47 (temporary source
  generation). All three PRs passed the full compiler GitHub Actions gate.
- GUI native widgets, Hero, file-tree icons, project explorer, current smoke
  examples and Product Gallery now display Zunyite and handle `.uny`; `.pnx`
  remains a supported legacy input. The canonical source-read API is
  `ProjectExplorer.read_source`, with `read_pnx` retained as an alias.
- `Zunyite_GUI` Workspace V4 is still developed on
  `feature/icon-system-v4` rather than released on `main`: as of this audit,
  that branch is **1532 commits ahead and 35 behind** `main`. Its integration
  and consolidation must be reviewed separately; do not claim the branch has
  already been merged or that the native IDE is shipped.
- Existing GitHub Actions secret `PYNIX_CI_READ_TOKEN` is preserved.
  Changing it requires creating/migrating the secret in the repository
  settings first, then updating the workflow in a separate coordinated change.

## Verification and limitations

Compiler PRs #45–#47 passed GitHub Actions including full pytest and CLI smoke.
The GUI's CI passed on Windows, Linux and macOS through commit `392089f3`.
For acceptance on the local macOS installation, rerun:

```bash
cd ~/PycharmProjects/Zunyite_GUI
git pull --ff-only
.venv/bin/python -m pytest -q tests/test_zunyite_naming_scripts.py
bash scripts/verify_full_stack.sh quick
```

Completion should be measured by public user-visible names, working
compatibility, and tests, not by blind elimination of the substring `pynix`.
**Status: compiler source/test-corpus naming is canonical with deliberate
legacy fixtures. Canonical GUI API imports work and two pure support modules
have been relocated; IDE service internals, wire identifiers, CI secret and
Workspace V4 release consolidation remain open.**
Native GUI visual acceptance and the transfer of internal implementation
ownership into the canonical namespace remain separate release gates.

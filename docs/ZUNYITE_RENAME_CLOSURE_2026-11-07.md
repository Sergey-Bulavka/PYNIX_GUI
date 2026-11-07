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
- The public GUI import `zunyite_gui` is available; the internal implementation
  still imports `pynix_gui` by design.

## Explicitly preserved compatibility / history

- `pynix_gui` internal Python package and its WebView script handlers
  (`window.pynix*`): changing names without a simultaneous host/client and
  test migration would break the editor. This remains technical debt and
  **must not** be presented as a completed internal namespace migration.
- Versioned protocol identifiers `pynix-debug` and `pynix-tooling` remain
  unchanged so compiler, IDE Core, and GUI agree. A new wire name requires
  version/capability negotiation and integration tests first.
- Historical design notes and explicit compatibility regression cases may
  retain PYNIX terminology. The compiler still has **227 tracked `.pnx` test
  fixtures**; not all have been classified as compatibility-only. Migrating
  ordinary conformance fixtures to `.uny` remains an open, separate test-corpus
  task and must not be called complete. A candidate migration of 173 standalone
  `tests/conformance/programs` fixtures is under draft PR #45 in Zunyite;
  it is not part of `main` until the compiler regression gate passes.
- Existing GitHub Actions secret `PYNIX_CI_READ_TOKEN` is preserved.
  Changing it requires creating/migrating the secret in the repository
  settings first, then updating the workflow in a separate coordinated change.

## Verification and limitations

Automated macOS compiler, IDE Core, GUI and real cross-repository bridge
checks passed before the current active-script naming cleanup. The new
changes require a fresh run:

```bash
cd ~/PycharmProjects/Zunyite_GUI
git pull --ff-only
.venv/bin/python -m pytest -q tests/test_zunyite_naming_scripts.py
bash scripts/verify_full_stack.sh quick
```

Completion should be measured by public user-visible names, working
compatibility, and tests, not by blind elimination of the substring `pynix`.
**Status: public naming substantially migrated; internal namespace and test
corpus migration not 100% complete.**
Native GUI visual acceptance and the transfer of internal implementation
ownership into the canonical namespace remain separate release gates.

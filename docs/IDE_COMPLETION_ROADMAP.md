# PYNIX IDE — full product completion program

## Working agreement

Complete implementation in large, coherent integration batches. Do not request
Mac user acceptance after each change. Engineer-owned focused tests and
regression tests accompany each subsystem. Run integration checks whenever
possible; never claim unrun macOS GUI tests succeeded. Request ONE consolidated
macOS manual acceptance only after all release-gate components are ready.

## Definition of 'complete IDE'

PYNIX_IDE is a practical native macOS development environment backed by the
PYNIX compiler, PYNIX IDE Core and PYNIX_GUI. 'Complete' is a concrete release
gate, not feature parity with every capability of PyCharm or Qt Creator.

### Existing blocks to harden in the integrated release

1. Editor/Core M4: authoritative buffers, atomic saves, dirty/close guards,
   recovery, multi-tab state, external-change conflicts.
2. Professional editor: inline predictive completion, Undo/Redo, multi-caret,
   bracket/indent behaviors, inline folding (Preview-only folding is not enough).
3. Smart coding: symbols, diagnostics, hover/type, definitions/references,
   semantic rename with correct cross-file positions and rollback, conflict
   handling; no stale results from disk-based compiler queries.

### Remaining product blocks

4. Workspace/projects: open/recent/new project, project tree and file operations,
   rename/move/delete with unsaved buffer protections, search/navigation,
   project-specific settings.
5. Run/debug: select target, executable/compiler integration, Run/Stop, console
   and error links; debugger only when runtime exposes a real stepping API.
   Never present a fake debugger as completed.
6. GUI development: GUI component preview and inspector, supported properties,
   examples and connection to PYNIX_GUI runtime. A drag/drop designer is an
   explicit separate acceptance gate.
7. Version control: Git changes, diff, stage/unstage, commit and conflicts,
   with safe subprocess boundaries; no hidden destructive commands.
8. Professional interface: consistent icons, accessibility, split panes,
   keyboard commands, responsive layout, theme and polish.
9. Distribution: macOS packaging/signing strategy, installation, default
   project template, dependency diagnostics, documentation and upgrade path.
10. QA and release: unit tests across all three repos, integration flows,
    macOS smoke suite, recoverability, performance, regression and security;
    record known limitations.

## Engineering cadence

- Requirements/contract for a subsystem; implement with focused tests.
- Run focused test suite as code changes (not as user acceptance).
- Periodically run combined regression once the environment is available.
- Preserve project safety and migrations/compatibility.
- Review Git diff, secrets, generated outputs and clean commit boundaries.
- At the end: one consolidated user-run macOS acceptance and fix pass.

## Outstanding known issues before declaring completion

- Mac Ctrl+Space belongs to keyboard input switching; no dependence on it.
- Inline gray completion must accept Tab without interfering with indentation.
- Editor selection/caret flash when focus moves from toolbar to source.
- References/Type and F2 Rename Symbol must be validated on multi-file project.
- Rename Local keyboard behavior needs macOS verification.
- True editable folding, IDE project workflows, Run/Debug, GUI tooling and
  packaging need completion or documented explicit release-scope decisions.

This plan does not assert that any unverified feature is finished.

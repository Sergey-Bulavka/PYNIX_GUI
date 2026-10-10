# PYNIX Ecosystem Integration — Architecture Gate and Execution Contract

Status: **PROPOSED / DO NOT MERGE before cross-repository review**.
Baseline (2026-10-10): PYNIX GUI main `8a30f5d`; PYNIX Language
`5a683eb`; PYNIX IDE `473dbfe` (as captured in the external review).
These are audit inputs, not a claim that any cross-repo migration is complete.

## Verified source boundaries

- Language: `compiler/desktop.py` implements `DesktopView` and
  `DesktopEvent`; `compiler/desktop_macos.py` hosts native Desktop.
- IDE: `src/gui.pnx` constructs its editor, controls and source list with
  `Desktop.*`, including `Desktop.textArea` and `Desktop.button`.
- PYNIX GUI: `pynix_gui/core.py` owns a distinct `GUIView` / `GUIEvent`
  contract. AppKit and Qt implementations live within GUI.
- PYNIX GUI is 0.1.6-dev, pre-alpha, release HOLD. Windows interactive
  acceptance is *not* demonstrated by green CI.

## Decision candidate — avoid two competing public UI libraries

1. Application authors should ultimately use the expressive `GUI.*` API.
2. `Desktop.*` remains a compatibility/platform boundary during migration,
   not a second expanding commercial component catalog.
3. Compiler owns language syntax, type checking, and the import/dispatch
   bridge. GUI owns immutable visual models, layout, event contracts, styling,
   resources and host implementations.
4. IDE owns project/source-buffer lifecycle, filesystem access, tooling,
   task execution, and file-opening policy. Do **not** move these services
   into the GUI framework.
5. Preserve existing `Desktop.*` consumers without source changes until
   parity is proven. Avoid a big-bang IDE rewrite.
6. No OS handles through public PYNIX-facing interfaces; platform-specific
   exceptions translate to stable PYNIX diagnostics.
7. Separate `SELECTION` and `OPEN`; changing a selection must not
   silently mutate the open directory.

## Integration seam (requires design and actual implementation)

```text
PYNIX application source (GUI.*)
    -> PYNIX Standard Platform import/type/dispatch boundary
    -> versioned PYNIX_GUI public adapter
    -> retained GUI view tree + semantic event queue
    -> AppKit / Qt hosts

PYNIX IDE source + IdeSession
    -> IDE-specific adapter -> GUI.* (incrementally)
    -> public compiler tooling protocol (not compiler internals)
```

Do not couple PYNIX IDE to `pynix_gui.backends.*` or internal Python
compiler objects. Define explicit compatibility rules for identity,
focus, text selection, UTF-16/codepoint conversion, dirty buffers and
layout before migrating the editor.

## Ten-stage program: implementation and acceptance gates

| Gate | Deliverable | Exit evidence |
| --- | --- | --- |
| 01 Ownership | This reviewed boundary + compatibility matrix | Owner sign-off across all 3 repos |
| 02 Real Project Explorer | Project-provided real directory snapshots and errors; no hard-coded demo paths | Temporary-tree traversal, symlink/permission/race/error coverage |
| 03 IDE/GUI integration | One real IDE component on GUI without Desktop regression | IDE CLI & desktop tests + live macOS acceptance |
| 04 Editor V2 | Source-buffer semantics, tabs, highlight, focus, selection | Dirty/undo/saving/Unicode/repaint tests + native visual acceptance |
| 05 Tooling V2 | Compiler public DTO adapter, diagnostics/completion/definitions | Cross-file tooling contracts + unsaved buffer regressions |
| 06 Windows parity | Real Qt mouse, key, IME, menu, DPI and resource acceptance | Interactive Windows hardware/VM checklist completed |
| 07 Product gate | Versioning, API audit, accessibility, distribution | Published verification report, no blockers remaining |
| 08 Contracts gate | Evidence-driven interface/DTO design only if needed | Real-world failure reproducer + semantics tests |
| 09 Native compiler proof | First native-code prototype isolated from default backend | Differential compiler/runtime parity and packaging evidence |
| 10 Release preparation | Reproducible artifacts, user docs, examples, upgrade guide | Install/uninstall and smoke run on target OS |

**Stage order is dependency-aware, not permission to bypass tests.**
Each stage must use RED/GREEN/regression + diff review before handoff.
Native Windows parity cannot be claimed without a Windows execution
environment. Native compiler work needs a separate language-design
review and must not be silently shipped in a GUI branch.

## Immediate integration acceptance fixture

Initial fixture: IDE opens an actual on-disk PYNIX project; explorer
lists only direct children of the open directory and uses stable
canonical project-relative IDs. A single click selects, double click
opens a directory or requests a document open. Reading a source file
remains in IDE session and never inside the GUI model. Reject
path-escape/symlink traversal outside the configured project root.
Preserve working behavior for callers of the legacy Desktop view.

## Remaining explicit blockers

- Real project traversal and IDE bridge not yet implemented.
- Interactive Windows machine/VM not provided.
- Production-grade rich source editor and native compiler backend are
  separate projects with no validated parity result.
- No release decision can be changed from HOLD by documentation alone.

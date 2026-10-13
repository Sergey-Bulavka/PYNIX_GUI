# PYNIX IDE — Block 3: Smart Coding acceptance

## Implemented

1. **Completion**: Complete toolbar button or Ctrl+Space in native editor. Suggestions
   merge language keywords, identifiers in the current buffer, and project-level
   declarations from the public `pynix-tooling symbols` protocol. Entries indicate
   compiler symbol kind / keyword / local identifier. Up/Down navigates; Tab/Enter
   accepts, Escape closes. Insertion uses the editor Undo/Core-sync path.
2. **Compiler Problems**: Problems button explicitly runs `pynix-tooling diagnostics`
   for the SAVED project and displays navigable compiler messages. No fabricated
   diagnostics or background recompilation of unsaved buffers.
3. **Definition, References, Type**: native compiler tooling through the existing
   validated, project-pinned bridge. Queries use current textarea caret, and dirty
   active buffers are rejected until saved. Reference entries navigate to files.
4. **Rename Symbol**: F2 or toolbar. Compiler references determine EXACT declaration
   and usage spans. A bounded read-only plan validates source positions and project
   paths before any changes. Native host opens each affected file in Core and verifies
   it is clean and matches disk. GUI checks the snapshots of ALL affected files and
   confirms the number of occurrences. It then changes unsaved GUI/Core buffers,
   opens affected tabs for review, and advances revisions. User manually reviews
   and saves each file using the established M4 Save workflow.
5. **Rename Local**: Shift+F2 or toolbar; narrow current-file operation ignoring
   strings/comments, with explicit shadowing warning. This is not semantic rename.

## Limits and cautions

- Completion is lexical/project-symbol based, not a full typed overload-ranked
  suggestion engine; candidate signatures, docstrings and scope-aware ranking
  remain future quality work.
- Compiler queries operate on disk. Dirty source must be saved to avoid stale data.
- Semantic rename does not atomically write multiple files: the edit plan updates
  unsaved buffers, and the user saves each document individually. Never claim
  the entire refactor was committed until those Save operations succeed.
- Semantic rename may reject complex declaration forms, unloaded sources,
  large projects or mismatched offsets rather than guessing or rewriting unsafe
  text. Unsupported symbol kinds remain unsupported.
- Unsaved data and Core disagreement abort the rename before changing buffers.
  Once applied, review every affected tab, then Save or Undo per file.
- MacOS WKWebView keyboard/menu/caret coordinates require real-device acceptance.

## Single batch verification

Run the full GUI pytest suite and `git diff --check`. Then launch the isolated
`bash scripts/test_editor_block3.sh` project. Validate native compiler completion,
saved-project diagnostics, Definition/References/Type, two-file semantic rename,
Undo and Save, and the dirty-buffer failure modes. Do not use a real project
for destructive rename testing. Document and fix any failures before accepting
Block 3.

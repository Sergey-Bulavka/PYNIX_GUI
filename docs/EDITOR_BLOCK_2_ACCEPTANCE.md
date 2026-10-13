# PYNIX IDE — Editor Block 2, implementation and acceptance

## Native V4 editing features

- Source text editing with line numbers and syntax coloring, preserving strings and comments.
- Per-tab caret, selection, scroll and undo/redo history.
- Tab and Shift+Tab indentation; Enter maintains indentation and expands empty brace blocks.
- Pair insertion for parentheses, square/curly braces, and quotes; wrap selected text; skip duplicate closers.
- Live matching-bracket highlight with strings/comments excluded.
- Cmd+/ toggles line comments; Cmd+Shift+D duplicates line; Option+Up/Down moves line.
- Cmd+D adds the next occurrence; Cmd+Option+Up/Down creates vertical cursors; Option+Click places additional cursors. Typing, backspace and paired punctuation apply to all active cursors. Esc clears extras; a normal mouse selection resets them.
- Find, replace, replace-all, go-to-line, toolbar navigation (existing features).
- Fold / Unfold toolbar commands, and line-gutter triangles in Preview, collapse indentation blocks without changing the saved document.
- Native Save remains guarded by the M4 Core revision protocol.

## Limitations to resolve before calling Block 2 commercially complete

- Folding currently switches to Preview; the textarea cannot physically elide editable source lines without breaking caret and selection offsets. True inline folding will need a virtualized editable document surface.
- Multi-caret supports Cmd+D, vertical keyboard carets, Option+Click, typing/backspace and paired punctuation; rectangular selection, multiline paste/IME and overlapping selections still require a richer editing engine and macOS acceptance.
- Native keyboard shortcuts may conflict with platform menu actions; test on macOS WKWebView.

## After the full code package: regression and manual acceptance

Run GUI pytest in one batch, then launch Workspace V4 on an isolated project. Exercise each feature across multiple tabs, undo/redo, Save, and Core recovery. Never run destructive operations on real source projects. Review stack traces and fix failures before marking Block 2 done.

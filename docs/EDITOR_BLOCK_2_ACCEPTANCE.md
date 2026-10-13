# PYNIX IDE — Editor Block 2, implementation and acceptance

## Native V4 editing features

- Source text editing with line numbers and syntax coloring, preserving strings and comments.
- Per-tab caret, selection, scroll and undo/redo history.
- Tab and Shift+Tab indentation; Enter maintains indentation and expands empty brace blocks.
- Pair insertion for parentheses, square/curly braces, and quotes; wrap selected text; skip duplicate closers.
- Live matching-bracket highlight with strings/comments excluded.
- Cmd+/ toggles line comments; Cmd+Shift+D duplicates line; Option+Up/Down moves line.
- Cmd+D adds the next occurrence as a secondary selection; typed characters/backspace apply to all selections, and Esc clears extras. Mouse selection clears extras.
- Find, replace, replace-all, go-to-line, toolbar navigation (existing features).
- Collapse/expand indentation blocks using line-gutter triangles in the Preview view. The source document is not modified by folding.
- Native Save remains guarded by the M4 Core revision protocol.

## Limitations to resolve before calling Block 2 commercially complete

- Folding is only in Preview; the textarea editor cannot physically elide source lines while preserving native selection offsets. A virtualized text editing surface is needed for inline folding.
- Multi-caret support currently covers Cmd+D same-text occurrences and text insertion/backspace; arbitrary mouse-placed carets, rectangular selection, multiline paste, IME, and overlapping selections require further design and macOS validation.
- Native keyboard shortcuts may conflict with platform menu actions; test on macOS WKWebView.

## After the full code package: regression and manual acceptance

Run GUI pytest in one batch, then launch Workspace V4 on an isolated project. Exercise each feature across multiple tabs, undo/redo, Save, and Core recovery. Never run destructive operations on real source projects. Review stack traces and fix failures before marking Block 2 done.

# Design Gate: subdued PyCharm-style text and syntax in actual V4

## Task

The user's side-by-side screenshot compares an active PYNIX V4 workspace
(on the left) with PyCharm (on the right). The PYNIX editor/tree text is
too bright. Python code also uses the PYNIX keyword palette and fails to
distinguish declarations, decorators, builtins and Python constants.

Only the **active** `examples.ide_native_v4` editor and Project tree are in
scope. This is not a new visual-shell mock.

## Reference ideas

- PyCharm New UI / Darcula: neutral gray editor body text, dim comments,
  warm keywords, green strings, blue declared function names, yellow-green
  decorators. Text weight/brightness should reflect language roles.
- VS Code TextMate/semantic highlighting: language-specific token scopes.
  It is a mistake to treat every language with one keyword set.
- Compiler-backed semantic tokens: more precise than a lexical pass, but
  introducing a compiler request on every keystroke is unnecessary and
  harmful for responsive editing.

## Native V4 design

1. Keep the textarea the **sole authoritative editor buffer**.
2. A pure, bounded JavaScript presentation lexer outputs source ranges for
   Python `.py/.pyi` and PYNIX `.pnx` without editing text or discarding
   whitespace. It supports ordinary/triple strings, common string prefixes,
   comments, numeric constants, function/class definitions and Python decorators.
3. Use the same display token stream when showing read-only Python source.
4. Add a scoped Darcula-inspired CSS layer *after* older V4 color rules.
   Do not modify font metrics, gutter sizing, caret, scroll synchronization,
   selection, IME, keyboard bindings or other toolbar/perimeter styling.
5. Keep Python and PYNIX syntax distinct. Unsupported file formats retain
   neutral text rather than incorrectly receiving PYNIX keywords.
6. Preserve the previously accepted Explorer icons and subdued selected-row
   text.

## Limitations

- This is **lexical** highlighting, not a complete Python parser or
  PYNIX semantic resolver; deeply nested f-string expressions, custom
  imported identifiers and contextual symbol resolution need language-service
  integration in a separate Design Gate.
- Screenshot palette matching is approximate until verified visually on Mac.
  The CSS uses the reference Darcula tone family rather than claiming to
  extract an authoritative scheme export from PyCharm.

## Acceptance

- `tests/conftest.py`: `from/import/def/for/return` warm orange,
  `@pytest.fixture` yellow-green, declaration `pynix_project` blue,
  `True` warm, strings green, comments muted gray.
- Plain identifiers and tree labels have reduced brightness.
- PYNIX `function` and Python `def` are correctly classified separately.
- Tripled/doc strings and comments do not accidentally color inner words.
- Typing, selection/caret, navigation, scrollbar and resize remain intact.
- Python read-only preview and edit mode have matching syntax categories.
- Focused test on Python/JS lexer plus full CI; manual macOS screenshot
  comparison once integration is ready.

## Tests

```bash
python -m pytest tests/test_ide_editor_darcula.py tests/test_ide_syntax_highlight.py tests/test_ide_workspace_preview.py -q
python -m pytest -q
git diff --check
```

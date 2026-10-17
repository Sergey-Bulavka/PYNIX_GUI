# Design Gate — File icons in the active IDE V4 Explorer

## Real user need

In the **active** `examples.ide_native_v4` window, show a meaningful,
PyCharm-style icon for each file and folder based on its actual extension or
special filename. The current ordinary launch hides the project tree glyphs.

## Reference comparison

- JetBrains New UI: stable SVG vocabulary for folders, file types and project
  files. Distinguish JavaScript, TypeScript, JSON, Markdown, YAML, TOML, SQL,
  images, archives, text and configuration files.
- Operating-system file associations: helpful for Finder, but platform-wide
  associations vary across machines and are often not the semantic code-file
  icons developers expect. We prioritize the consistent PyCharm-style
  extension icon when PYNIX runs on different computers.
- VS Code: a type-specific icon extension per file and a general fallback.

**Avoid:** drawing all files with one document icon; depending on the host
machine's personal default-app associations; replacing tree events when adding
icons; loading binary files as UTF-8; copying source SVG bytes into new,
unlicensed derivative assets.

## Native PYNIX decision

- Reuse the already bundled and license-verified JetBrains SVG catalog and
  the existing `ide_icon_parity` MutationObserver. SVGs remain source assets.
- The default V4 launch enables a **tree-only** SVG bridge. The rest of the
  compact iconless UI and the user's existing perimeter/top-bar controls are
  preserved. `--with-icons` continues to use the full icon bridge.
- Use extension data for common language/resource types and exact filenames
  for Dockerfile, Makefile, Git and editor config files.
- Preserve the distinct built-in PYNIX `.pnx` and Python `.py/.pyi`
  identities. Unknown extensions fall back to a neutral document icon.
- Keep file tree icons at 16 px, chevrons at 13 px; preserve tree row geometry,
  highlighting, focus, expansion, single-click selection and double-click open.
- Generic icon binding is a fallback; once a specific file-type icon has been
  installed, later MutationObserver passes must not replace it with generic.
- Include recognized images, archives and fonts in the Explorer tree, marked
  as nontext resources. Opening them must never forward a UTF-8 read/edit
  request. PYNIX source remains the preferred initial document.
- Safely show selected editor metadata dotfiles (`.gitignore`,
  `.gitattributes`, `.editorconfig`) without exposing secrets like `.env`.

## Boundaries

This is a display/type-mapping change, not a new program loader, language
feature, operating-system file association service, or general file manager.
No GUI public primitive or compiler API is added.

## Acceptance

- Verify PYNIX, Python, JSON, Markdown, YAML, TOML, HTML, JS/TS, CSS,
  image/archive and unknown readable file labels.
- Confirm collapsed/expanded folder icons survive many tree rerenders.
- Confirm no generic/specific icon replacement loop, no clipping/misalignment.
- Confirm default mode and `--with-icons` both show type-specific tree icons.
- Confirm selecting an image does not call the native file-open bridge.
- Regression: topbar, editor tabs, debugger, pane resizing and all interactions.

## Test commands

```bash
python -m pytest tests/test_ide_file_icons.py tests/test_ide_icon_parity.py tests/test_ide_iconless_mode.py tests/test_ide_workspace_preview.py tests/test_ide_workspace_session.py -q
python -m pytest -q
git diff --check
```

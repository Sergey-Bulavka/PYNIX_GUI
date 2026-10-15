# PYNIX IDE — full New UI icon catalog

**Scope:** every licensed icon relevant to PyCharm/IntelliJ UI, not only the
left/top/right/bottom bars. This includes Project and other tool windows,
actions, main menu, editor gutter, code navigation, inspections, refactoring,
debugger, VCS, testing, terminals, databases, notifications, status states,
files, folders, and settings.

The collection must remain an **indexed library**: an icon does not need a
visible toolbar button or implemented PYNIX command to be imported.

## Reference and copyright

- Official icon browser: https://intellij-icons.jetbrains.design/
- Official New UI guidelines: https://plugins.jetbrains.com/docs/intellij/icons.html
- Source: https://github.com/JetBrains/intellij-community
- Apache 2.0 license: https://www.apache.org/licenses/LICENSE-2.0

Most published JetBrains New UI SVGs are licensed Apache 2.0, but **not all**.
Import only assets with a copyright header explicitly granting Apache 2.0.
Keep the source SVG header intact. Avoid PyCharm/JetBrains product logos,
trademarks, splash/about images and icons without an explicit compatible
license. PYNIX retains its own app logo and visual identity.

## Import the entire eligible source tree (not a hardcoded icon subset)

The importer is offline and operates on a local clone. It walks all folders
and creates dark/light/resolution variants indexed by category:

```bash
cd /Users/morphey/PycharmProjects/PYNIX_GUI

# Obtain a JetBrains source checkout separately, then point at its expui tree.
# The source location changes with upstream releases.
./.venv/bin/python -m pynix_gui.ide_jetbrains_icons \
  /path/to/intellij-community/platform/icons/src/expui \
  ./pynix_gui/assets/jetbrains_new_ui \
  --dry-run

# After reviewing the license/skip report, remove --dry-run to copy all
# eligible SVGs and write the manifest.
```

The command does not download files or bundle them by itself. It does not
claim to include icons from proprietary PyCharm modules. Do not blindly import
the entire product asset directory: files are screened individually.

Generate a **searchable visual index of every imported icon** and review
light/dark variants directly in a local browser:

```bash
./.venv/bin/python -m examples.icon_catalog_gallery \
  ./pynix_gui/assets/jetbrains_new_ui
open ./pynix_gui/assets/jetbrains_new_ui/gallery.html
```

For an imported collection use:

```python
from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog

catalog = JetBrainsIconCatalog("pynix_gui/assets/jetbrains_new_ui")
print(len(catalog), list(catalog.names("actions/"))[:10])
svg = catalog.svg("actions/add", dark=True)
```

**Catalog guarantees**

- Preserves category-qualified names instead of flattening duplicate filenames.
- Keeps original SVG source and in-file copyright/license notice.
- Stores SHA-256 integrity for each asset in manifest.json.
- Supports `_dark`, `@2x`, `@20x20`, and `@16x16` variants.
- Uses larger glyphs for New UI tool windows, normal 16px for actions/file
  nodes, and compact variants as appropriate.
- Rejects icons without an explicit Apache 2.0 header, potentially executable
  SVG, remote resources, and product logos/trademarks.
- Provides a single runtime lookup API for eventual UI-wide rendering.

## Geometry parity

JetBrains documents New UI tool-window icons as **20×20 px** (16×16 compact),
file/action icons as **16×16 px**, gutter icons as **14×14 px**.
Layout parity for the four window edges is separate from having the complete
icon catalog. Install icons only on controls that have an actual user action.

## Acceptance checklist

1. Full category inventory from official sources, with total and skipped counts.
2. Complete license audit (every imported SVG contains its own Apache header).
3. Dark/light/compact variant review with visual icon gallery.
4. Map existing PYNIX controls across the left, top, right, bottom rails.
5. Expand mapping to menus, Project tree, editor, debugger and all secondary
   tool windows; no inert controls just because icons exist.
6. HiDPI inspection, focus/hover/active/disabled states and runtime tests.

**Status (first production slice):** importer, manifest-backed lookup,
offline gallery, and the first **16 original JetBrains New UI SVGs** are now in
the PYNIX repository under `pynix_gui/assets/jetbrains_new_ui/svg/`.
These cover Project, Find, VCS, Run, Debug, Settings, Search, Refresh in
light and dark variants. The native V4 preview activates eligible icons on
its existing left rail and toolbar and falls back to existing artwork if
a named icon is missing.

Full PyCharm icon parity has **not** yet been achieved. The user-visible
status bar, full right rail, file type families and all secondary controls
still need to be mapped as appropriate. Do not invent working controls.
The full upstream `expui` directory has not yet been imported.

Validate this slice with:

```bash
python -m pytest tests/test_ide_jetbrains_icons.py tests/test_ide_icon_parity.py \
  tests/test_ide_native_v4.py tests/test_ide_workspace_preview.py -q
```

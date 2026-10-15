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

For a reproducible, minimal sparse Git checkout, use the included importer
script. It prints the upstream commit and counts every eligible/skipped SVG:

```bash
cd /Users/morphey/PycharmProjects/PYNIX_GUI
bash scripts/import_full_new_ui_icons.sh --dry-run
bash scripts/import_full_new_ui_icons.sh --apply
```

`--apply` saves the original licensed files, their manifest, an upstream commit
record and a searchable gallery. Inspect the license counts and `git diff`
before committing the full collection. The source checkout is deleted after
import; it does not become part of PYNIX.

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

**Status (licensed full catalog):** the complete audited upstream
`platform/icons/src/expui` directory is imported from JetBrains commit
`9c8a280703b02322663b2f476ff7dbac8922889b`:

- **787 icon names, 1,642 licensed light/dark and sized SVG variants**
- 100 files excluded for lack of an explicit compatible license declaration
- Original SVG license headers and SHA-256 manifest kept
- Repeatable import job: `.github/workflows/vendor-jetbrains-icons.yml`
- Searchable gallery generated from the complete manifest

The running native V4 preview now applies licensed icons to its existing
left/top/right tool controls, Project folders, specific file extensions,
editor tabs, and the left project indicator of the bottom status strip.
When no licensed matching SVG exists, the previous PYNIX icon is retained.
The native PYNIX identity and Python logo remain distinct.

**Remaining work:** full PyCharm **visual layout and usage** parity, including
all menu/action command glyphs, debugger subpanels, contextual indicators,
hover/active/focus states, secondary tool windows and pixel-level inspection on
macOS. Import completeness alone does not mean all 787 icon names are used.
Do not add inactive tool buttons merely to display the available glyphs.

Validate this slice with:

```bash
python -m pytest tests/test_ide_jetbrains_icons.py tests/test_ide_icon_parity.py \
  tests/test_ide_native_v4.py tests/test_ide_workspace_preview.py -q
```

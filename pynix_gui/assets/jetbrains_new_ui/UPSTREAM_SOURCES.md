# Original JetBrains icon sources

PYNIX IDE accepts **original, unmodified SVGs from JetBrains repositories only**
for new iconography. Do not synthesize lookalikes, redraw missing icons, or
substitute unrelated icons. If the appropriate official asset cannot be
identified and its reuse rights verified, leave the action text-only or
disabled until the original is available.

The existing New UI pack comes from
[JetBrains/intellij-community](https://github.com/JetBrains/intellij-community),
`community/platform/icons/src/expui`. Each imported SVG retains the original
Apache 2.0 notice and its `manifest.json` SHA-256 checksum.

## GitHub Pull Requests

Source repository: `JetBrains/intellij-community`.

Pinned source revision: `c6f4ce4c9fea9993e8d2e11b808e1f6fe2896681`.

Official upstream files, both imported **without changes**:

- [Light pullRequests.svg](https://github.com/JetBrains/intellij-community/blob/c6f4ce4c9fea9993e8d2e11b808e1f6fe2896681/plugins/github/github-core/resources/org/jetbrains/plugins/github/expui/pullRequests.svg)
- [Dark pullRequests_dark.svg](https://github.com/JetBrains/intellij-community/blob/c6f4ce4c9fea9993e8d2e11b808e1f6fe2896681/plugins/github/github-core/resources/org/jetbrains/plugins/github/expui/pullRequests_dark.svg)

Bundled as `svg/github/pullRequests.svg` and
`svg/github/pullRequests_dark.svg` under the New UI asset directory.
The `github/pullRequests` catalog key is indexed with SHA-256 hashes.

## Tool-window More

The original `general/moreHorizontal` asset is already present in the
JetBrains New UI catalog in 16px and 20px, dark and light forms. The left
top tool-window group displays its **20px dark SVG**, not a text symbol.

## Design invariant

Any future icon used by `ide_edge_profile.py`, `ide_icon_parity.py`
or `ide_pycharm_chrome.py` must resolve through `JetBrainsIconCatalog`.
A missing original is not a reason to draw a new icon. The file provenance,
explicit license notice and checksum are checked in automated tests.

## More Tool Windows menu

The `More Tool Windows` menu uses imported, checksum-verified JetBrains icons:
`toolwindows/bookmarks`, `toolwindows/find`, `toolwindows/debug`,
`toolwindows/coverage`, `toolwindows/hierarchy`, `toolwindows/learn`,
`toolwindows/todo` and `pythonProcessOutput/process`.

The Python Process Output vector is copied unchanged from the official
[JetBrains process output module](https://github.com/JetBrains/intellij-community/tree/master/python/python-process-output/frontend/resources/icons):
`process.svg` and `process_dark.svg`. Unlike the expui icon set, those two
files contain no individual Apache notice; their upstream repository is
covered by the [JetBrains repository's Apache-2.0 license](https://github.com/JetBrains/intellij-community/blob/master/LICENSE.txt).
Both original files retain their exact bytes and SHA-256 checksums in
`manifest.json`.

**Endpoints:** This is a JetBrains IDE product-specific asset, but a
redistributable upstream SVG is not present in the public Apache icon pack.
PYNIX therefore **does not bundle or imitate** it. The `Endpoints` item
loads the unmodified original SVG directly from a locally installed PyCharm
or IntelliJ IDEA `.app` Java archive when that official resource is found.
This is implemented in `pynix_gui/ide_local_jetbrains_icons.py`.
The bundle is searched only on the user's computer; nothing is downloaded
or committed. The `localJetBrains/endpoints` key explicitly marks this
local-only origin.

Supported install paths include `/Applications/PyCharm.app`, user
`~/Applications` and JetBrains Toolbox apps. For other locations, point
`PYNIX_JETBRAINS_APP_PATH` at a local `PyCharm.app` bundle or the
specific official JetBrains `.jar` containing
`icons/expui/toolwindows/endpoints_dark.svg`.

**If the official Endpoints resource is absent** from the user's installed
IDE, the row will remain without artwork. Never use another SVG as a
lookalike. The original vector's availability and final visual appearance
must be checked in the user's macOS PyCharm installation.

The Bookmarks, Find and Debug macOS shortcut **labels** match the screenshot
(`⌘2`, `⌘3`, `⌘5`); a displayed shortcut does not by itself register
a new native keyboard accelerator.


## Lower-left PYNIX tool-window stripe

The seven tools are ordered to match the user's PyCharm screenshot:

`Run`, `PYNIX Terminal`, `PYNIX Packages`, `Services`,
`Terminal`, `Problems`, `Git`.

Five ordinary tools use unchanged, checksum-pinned JetBrains icons
`toolwindows/run`, `toolwindows/services`, `terminal/terminal`,
`toolwindows/problems`, and `toolwindows/vcs`.

The original JetBrains **Terminal** SVGs in the `terminal/terminal` key
were imported without changes from
[JetBrains/intellij-community/plugins/terminal/resources/icons/expui/toolwindow](https://github.com/JetBrains/intellij-community/tree/master/plugins/terminal/resources/icons/expui/toolwindow)
(16 and 20px, normal and dark).

The original JetBrains **Python Packages** SVGs in
`python/pythonPackages` were likewise imported without changes from
[JetBrains/intellij-community/python/pluginResources/icons/com/jetbrains/pythonCore/python/expui](https://github.com/JetBrains/intellij-community/tree/master/python/pluginResources/icons/com/jetbrains/pythonCore/python/expui).

**PYNIX brand artwork is an explicit exception** to the rule that
non-PYNIX UI controls use original JetBrains SVGs. Unlike licensed JetBrains
icons, our own PYNIX pictograms may be adapted for compact tool-window use.

The two PYNIX-only SVGs are redrawn to retain the native identity of our
already-bundled `pynix_gui/assets/icons/pnx-file.png` **without embedding,
tracing or rendering that raster**:

- `pynix_gui/assets/icons/pynix-terminal.svg` uses a single 14×16px
  six-sided enclosure and an open internal P-shaped mark, with precise
  1.45/1.3px strokes. It has no white document/page, fill, or tiny overlay.
- `pynix_gui/assets/icons/pynix-packages.svg` uses a complete, coherent
  isometric parcel with 1.5/1.45px edges; the **same PYNIX mark** is engraved
  in the right face at effective 1.1px stroke. This is not a tiny copy
  of an icon layered over an existing Python logo: all Python shapes are
  absent, as are opaque background stickers.

Both are intentionally redrawn **PYNIX-owned** vectors, rather than falsely
labeled copies of JetBrains artwork. The licensed original JetBrains package
icons stay **untouched** and available in the catalog. The PYNIX copies use
`currentColor`, are distributed as editable SVG assets, and are verified
by geometry and no-bitmap regression tests.

Inactive-window opacity, hover and active selection all use the existing
New UI rail styles. No embedded PNGs, hardcoded dark/light palette in the
PYNIX icons or extra overlay badges are used.

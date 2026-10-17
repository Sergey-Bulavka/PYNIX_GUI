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

The two PYNIX-only SVGs are redrawn using the high-resolution PYNIX
reference artwork supplied for the IDE. Neither icon embeds a PNG, traces
the old low-resolution file-glyph sprite, or alters the original JetBrains
catalog:

- `pynix_gui/assets/icons/pynix-terminal.svg` is a **solid, three-part
  geometric PYNIX monogram**, matching the filled brand silhouette and its
  negative spaces. The old approximated outline hexagon with nested, jagged
  strokes has been removed. Three full-size SVG fills preserve readability
  at 20×20, instead of stacked scale transforms.
- `pynix_gui/assets/icons/pynix-packages.svg` preserves the
  **exact 20×20 JetBrains Python Packages box silhouette** from the licensed
  `pythonPackages@20x20_dark.svg` (its final path is reproduced unchanged).
  The four Python snake/eye paths are removed; the three exact existing
  PYNIX Terminal logo paths replace them in the same lower-right region,
  using a single uniform scale. Thus the proportions, bevels and outline
  weight match the original PyCharm package icon rather than an invented
  PYNIX cuboid. No bitmap, extra logo badge or edited upstream catalog file
  is used.

Vector quality is also managed consistently across the native IDE by the
`geometricPrecision` SVG style and `image-rendering:auto`. The browser
retains the original 20 CSS-pixel artwork dimensions, allowing its native
WKWebView antialiasing instead of creating and rescaling bitmaps. **At very
high screenshot magnification, discrete display pixels remain visible**;
this does not by itself indicate a raster-source icon.

The terminal SVG is a PYNIX-owned vector; the adapted Packages SVG
combines an unmodified Apache-2.0-licensed JetBrains package silhouette
with our own PYNIX brand mark. The licensed JetBrains originals remain
untouched in the catalog. Both use `currentColor`, are distributed as
editable SVG assets, and are covered by geometry/no-bitmap tests.

Inactive-window opacity, hover and active selection all use the existing
New UI rail styles. No embedded PNGs, hardcoded dark/light palette in the
PYNIX icons or extra overlay badges are used.

## Right-side PyCharm Notifications and AI Chat

The screenshot-matched **Notifications** tool uses the untouched
`toolwindows/notifications@20x20_dark.svg` icon from the imported
JetBrains New UI collection. Its blue notification dot is a separate
presentation-layer CSS decoration and **does not indicate actual unread
notifications** until the PYNIX notification subsystem is implemented.

The screenshot-matched **AI Chat** icon uses the unmodified official
[JetBrains/Kotlin documentation icon](https://github.com/JetBrains/kotlin-web-site/blob/master/docs/images/ide-icons/toolWindowChat@20x20.svg)
(`JetBrains/kotlin-web-site` is published under Apache-2.0). Its SVG is
distributed as `svg/chat/toolWindowChat@20x20.svg`, SHA-256
`6ab00849a4aaa1cf682411b80b1e45be9624b1198b842addfa9adc1d2477d5dd`.
The official file has no per-file copyright header, so the importer
validates its exact path and SHA-256 in `OFFICIAL_UNHEADERED_ICONS`.
There is only one official file: both light and dark catalog variants
reference the **same unchanged original SVG**; the displayed grey color
is adjusted through PYNIX CSS rather than editing the source asset.

Both tool buttons stay clearly marked as unimplemented in accessibility
labels and tooltips, and no extra right-side More menu is introduced.

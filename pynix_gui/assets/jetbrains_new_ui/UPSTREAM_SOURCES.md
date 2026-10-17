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

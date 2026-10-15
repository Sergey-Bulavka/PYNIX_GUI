# Workspace V4 — PyCharm New UI visual acceptance gate

Reference: user-provided PyCharm macOS screenshot (2026-10-15, 1644 × 896) and official JetBrains New UI documentation.
Goal: visual parity at the same window size, macOS scaling, editor font, open files, panel layout, and theme. This is NOT proof of pixel-perfect parity yet.

Official references:
- https://www.jetbrains.com/help/pycharm/guided-tour-around-the-user-interface.html
- https://www.jetbrains.com/help/pycharm/new-ui.html
- https://www.jetbrains.com/help/pycharm/tool-windows.html
- https://www.jetbrains.com/help/pycharm/editor-gutter.html

## Design Gate
Problem: repeated small CSS patches have produced conflicting selectors. A matching structure is not the same as matching visual metrics. PyCharm's New UI separates title bar, project window, editor tabs, gutters, tool windows and status bar. Build one scoped presentation contract; preserve commands and the neutral PYNIX_GUI toolkit API.
Reference screenshot is copyrighted UI reference only: recreate layout and behavior without redistributing JetBrains artwork, trademark assets, or fonts.

## Visual acceptance checklist

| Priority | Zone | Target / measurable checkpoint | V4 gap and action | Status |
| --- | --- | --- | --- | --- |
| P0 | Whole window | Match 1644×896 reference at 100% screenshot scale; compare images with overlay/diff | Confirm macOS titlebar vs in-WebView header origin; do not stack two toolbars | pending visual |
| P0 | Header | One toolbar, consistent optical alignment, separate project/branch/run/action groups | Align title and icons to screenshot, avoid hidden controls affecting flex widths | pending visual |
| P0 | Editor tabs | Compact rounded active pill, 30px tab chip within ~39px row; title 24px, close slot 18px | Generic `.editor-tabs button` overwrites both title and close; override with specific descendant selectors | implemented; native verification pending |
| P0 | Editor tab states | Inactive neutral, active brighter; close visible for active/hover/focus, fixed widths (no reflow) | Verify CSS specificity of close button and disabled pointer state | implemented; native verification pending |
| P0 | Project pane | ~200px visible column at reference screenshot, header compact, tree rows ~24px, clipped long filenames | Measure left rail and explorer independently; project pane width is user-resizable | pending visual |
| P0 | Terminal | Bottom dock separated by narrow gap, dedicated header and session row; terminal is not editor overlay | Measure terminal dock height and top gap, keep resize affordance | pending visual |
| P1 | Left tool rail | ~32–40px, controls optically centered, no oversized selection backgrounds | Compare icon viewport and hit targets at actual Retina scaling | pending visual |
| P1 | Right tool rail | Symmetric tool icon spacing, correct active/hover states | Compare against reference edge strip | pending visual |
| P1 | Status bar | Slim bottom row, breadcrumb left, encoding/indent/environment right | Ensure right items don't collide or truncate | pending visual |
| P1 | Editor gutter | 1–3 digit line numbers align right, breakpoint in gutter, active line clear but subtle | Compare line-height, baseline, breakpoint center and highlight across split panes | pending visual |
| P1 | Editor type | Separate code monospace metrics from UI typography; don't alter line height to match UI font | JetBrains uses Inter for UI; use licensed/local font fallback, never distribute proprietary fonts | pending visual |
| P2 | Hover and focus | Active/hover/keyboard focus distinct, no layout shift | Evaluate tabs, tree rows, tool headers and rails | pending visual |
| P2 | Compact/resized states | Restore usable navigation at minimum window size | Native resize test at 760×520 and reference resolution | pending visual |
| P2 | Gallery isolation | Only .workspace-mode changes; icon gallery unaffected | Check both modes | pending tests |

## Test protocol
1. Same file and tree selection, 1644×896 screenshot both apps, same appearance and display scale.
2. Capture PyCharm and PYNIX V4; compare panel boundary pixel coordinates, text baselines, icon centers, hover/selection and scrollbars.
3. Exercise active and inactive tabs, hovered close, keyboard focus, tree selection, terminal resize and minimum window size.
4. Run `tests/test_ide_native_v4.py`, `tests/test_ide_workspace_preview.py`, and native smoke.
5. Do not claim visual parity until two screenshots pass an image-overlay review.

## Constraints
- Preserve PYNIX Core editor buffers/save semantics. No backend work in this pass.
- No placeholder commands and no direct copying of JetBrains branded graphic assets.
- Every CSS addition must be scoped to `.workspace-mode` and must not globally modify gallery components.
- Consolidate legacy conflicting tab rules in a subsequent cleanup after visual acceptance, not blind deletion.

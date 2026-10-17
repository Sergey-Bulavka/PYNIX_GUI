# Design Gate — collision-free native V4 toolbar during live resize

## Task

When the macOS IDE window is resized horizontally, the controls at the top
sometimes visibly overlap, then appear to recover seconds later. The
requested behavior is continuous, immediate and deterministic at every window
width, **without** layout jumps or occluding hit targets.

## Reference and limitations of alternatives

- JetBrains PyCharm uses a width-aware compact top bar; group boundaries stay
  independent while some labels become shorter on narrower windows.
- Qt Layout and CSS Flexbox both solve resizing through one layout owner,
  reflowing children on every size change. The key advantage is avoiding
  manual guesses about coordinates.
- Absolute coordinates followed by JS measuring, debouncing, timers or
  repeated animation frames create states where painting and hit-testing do
  not agree. They mask the symptom rather than enforcing a constraint.

## Root cause in native V4

`pynix-pycharm-center` was `position:absolute;left:70%;transform:translateX(-50%)`.
This made Current File/Run/Debug/More Actions independent of the project/Git
identity and the Search/Settings/Beta group. Under `max-width:1160px`
it switched to `position:static` and `margin-left:auto` while the
right-hand controls retained their own sizing. Nothing prevented two groups
from occupying the same area at intermediate widths.

## Native PYNIX correction

- Use one flex row with `identity`, the existing empty drag-safe
  `toolbar-spacer`, `center`, a second equally flexible empty region, and
  `right`. The equal spacers keep Run/Debug centered within the free space
  without absolute positioning, and both shrink to zero under pressure.
- A single final CSS layer resets absolute positioning, left/top and transforms
  and makes the identity/right groups shrink with `min-width:0`.
- The spacer takes only remaining free width and still supplies safe native
  window-drag geometry; the original Run/Debug listeners are never cloned.
- Keep Run/Debug/Search/Settings SVG button hit areas at 29/31px in both
  standard V4 and `--with-icons`, preventing the old text-fallback
  min-widths from silently inflating buttons.
- When narrower, shorten project/Git/config names and change the green badge
  to `β · [same actual version]`, retaining its full accessible version.
  Breakpoints modify label lengths/gaps **only**, never the positioning model.
- Avoid new event loops, repeated DOM reparenting, sleeps, timers or
  delayed measurement. Chromium/WebKit flex layout owns intermediate sizes.
- Existing `ResizeObserver` remains only for the native window drag-region
  geometry; it does not determine toolbar button placement.

## Acceptance

1. Drag continuously from wide (~1400px) to the native minimum (~760px),
   across 1160, 1060 and 930px, then reverse, at different drag speeds.
2. Project/Git, Current File, Run, Debug, More Actions, Search, Settings
   never overlap or jump, and remain clickable during resize.
3. The green Beta badge can shorten, but Search/Settings must not disappear.
4. Hover/focus/tooltip state remains bound to the correct icon hit box.
5. Dragging the empty toolbar and native window resizing still work.
6. Project tree resize, Run/Debug, selection and menu click behavior unchanged.
7. Test in both default iconless-with-restored-buttons and `--with-icons`.

## Verification

```bash
python -m pytest tests/test_ide_toolbar_resize_layout.py tests/test_ide_pycharm_chrome.py -q
python -m pytest -q
git diff --check
```

Automated CSS/DOM contracts and platform CI prevent known regressions, but
do **not** replace interactive macOS rapid-resize screenshot acceptance.

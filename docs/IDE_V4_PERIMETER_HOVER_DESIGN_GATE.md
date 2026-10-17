# Design Gate — uniform V4 left/right tool button hover

## Real task

In the currently accepted **native V4** layout, all sidebar icons should look
like a button when the pointer moves over them, including icons that point to
not-yet-implemented features. Topbar, editor, tree, commands and geometry
must remain unchanged.

## Reference and pitfalls

PyCharm New UI uses a consistent rounded rectangular hit area for its tool
windows. An icon's unavailable state is separate from its visual hit target.
The existing PYNIX theme diverged in two ways:

- Its common :hover rule excluded `aria-disabled="true"` tools, even though
  these remain focusable for explaining their current status.
- The right-top icon rule declared `background:transparent!important`, which
  overrode the common hover rule. Inactive-window CSS also cleared hover.
- The existing "More Tool Windows" button followed another rule.

Giving unavailable buttons real click listeners just to create hover feedback
would be incorrect and misleading.

## Native PYNIX solution

1. Keep the existing single DOM icon renderer (`ide_edge_profile`), verified
   JetBrains SVG assets, 36 x 36 px icon hit boxes and menu positioning.
2. Apply one **late, sufficiently specific** hover/focus style to all
   `.pynix-extra-tools[data-edge]` item buttons on left and right.
   This includes disabled but focusable controls. Use `#3a3d45`.
3. Preserve actual `aria-pressed="true"` tools in blue (`#3574d6`).
4. Apply the same hover/focus/expanded background to the More button.
5. Keep click handlers *only* for implemented commands. Tooltips for
   unfinished tools explicitly say "not available yet", without fake actions.
6. Preserve keyboard focus outline, inactive icon dimming, reduced-motion
   preference and original SVG color/geometry.

## Acceptance checklist

- All left-top and left-bottom icons show rounded background on hover.
- Notifications and AI Chat on right-top show the same background.
- More Tool Windows has the same hover/focus/expanded feedback.
- Unavailable icons highlight but do not open an unimplemented tool.
- Active Project retains its blue selected state when hovered.
- Native tooltips appear on both edges and keyboard focus remains visible.
- Check both default V4 mode and `--with-icons` after launch.
- Verify visually on macOS after automatic tests, including window inactive
  and reactivated states.

## Testing

```bash
python -m pytest tests/test_ide_edge_hover_unification.py tests/test_ide_edge_profile.py tests/test_ide_tooltips.py -q
python -m pytest -q
git diff --check
```

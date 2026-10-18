# Design Gate — PYNIX IDE V4 Terminal as a PyCharm tool window

## Actual user task
The native IDE V4 lower dock currently has a VS Code-like four-tab header.
The user wants the compact PyCharm Terminal header shown in the reference
image, a **single Terminal side button** that opens *and* hides the dock, and
the full reclaimed height assigned to the file tree and editor.

## Existing strong solutions
- JetBrains PyCharm tool windows provide a single left sidebar tool-window
  button and a header containing its name, session tab ("Local"), contextual
  tool menu and Hide button. Hiding fully removes the dock from the editor
  vertical space; opening Problems/Debug selects their own tool window.
- VS Code's bottom panel defaults to a series of Terminal/Problems/Output/
  Debug Console tabs. This is functional but visually mismatched here.
- Native Qt/NSStackView and CSS Flexbox both support removing a dock entirely
  while sibling editor surfaces grow, *provided no fixed 100% height remains*.

## Identified PYNIX weaknesses
- A pre-existing `setToolWindowVisible` and collapsed CSS already exist.
- The legacy fifth rail button has **no Terminal-specific click listener**;
  the new JetBrains SVG icon is only a proxy for `rail:4`.
- The bottom contains both a VS Code four-tab strip and a redundant separate
  Local-session row. Adding another independent visible controller would
  create UI/keyboard and content consistency bugs.
- Old `.ide{height:100%!important}` can compete with the parent's flex height.

## Native design (Complex inside. Simple outside.)
1. Keep the existing `toolTabs` elements, output buffer snapshots,
   `selectedTool`, debugger/diagnostics/run callbacks and
   `setToolWindowVisible` as the **only** source of terminal state.
2. Insert one compact PyCharm-like dock toolbar with Terminal title, "Local"
   session pill, contextual tool-window selector, Terminal Options menu, and
   Hide button; no second terminal emulator is invented.
3. Existing legacy `toolTabs` remain *DOM command targets* for debug/run/
   problems/output and are visually hidden; the redundant old Local row is
   visually hidden too.
4. Left-side **Terminal / PYNIX Terminal** icon proxies retain the original
   `rail:4` command, which toggles dock visibility when Terminal is already
   selected and selects/opens Terminal otherwise. `aria-pressed` tracks
   actual visibility. The same button always reopens the dock.
5. Debug, diagnostics and Run continue selecting the relevant original tab
   and opening the dock automatically, without clearing output on hide.
6. On initial load, terminal is hidden (user explicitly opens it); hiding
   removes both the resizer and dock from CSS flex layout. The editor/tree
   live in a `flex:1 1 0%; min-height:0` parent and fill all released space.
   Existing remembered `--terminal-height` remains unchanged.
7. "New Terminal" and "AI Agents" are visibly disabled, because the current
   bottom window is a run-output and diagnostics host, not a real interactive
   shell or multi-session terminal service. Do not pretend to create one.
8. The existing dock keyboard shortcut and Escape-to-hide remain functional.
   Menu options switch to the real Problems / Output / Debug Console views.

## Acceptance
- Launch V4: Terminal is hidden and both editor and Project tree fill the
  entire available height above the status bar.
- Click either left PYNIX Terminal or Terminal icon: opens Terminal; click the
  same icon: hides it. Reopen preserves buffer and last dock height.
- Run and Diagnostics automatically show respective output with no stale
  content; Debug Console selection still works.
- Other tool views remain accessible through the contextual menus.
- Hover/focus and keyboard work, no clickable fake "New Terminal" or Agents.
- Resize macOS window and Project pane with the dock hidden and shown;
  no dead blank area; no change to editor tabs, root tree, status bar.

## Verification
```bash
python -m pytest tests/test_ide_v4_terminal_dock.py \
 tests/test_ide_workspace_preview.py tests/test_ide_native_v4.py -q
python -m pytest -q
git diff --check
```

Static and JavaScript syntax tests cannot prove pixel-perfect WKWebView
rendering or actual pointer interaction; native Mac acceptance remains needed.

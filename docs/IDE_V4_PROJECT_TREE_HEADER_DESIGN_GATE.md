# Design Gate — active V4 Project Explorer header

## User task

Match the supplied PyCharm screenshot in the **actual**
`examples.ide_native_v4` workspace, not an old visual mock:

- Root row: clear **project name** plus muted actual project path, e.g.
  `PYNIX ~/PycharmProjects/PYNIX`, with ellipsis.
- Header: **Project** drop-down at left and (on Explorer hover/focus)
  **New File or Directory**, separator, **Select Opened File**,
  **Expand Selected**, **Collapse All**, **Options**, **Hide** at right.
- Each icon uses the existing original JetBrains SVG catalog, round hover hit
  area, and delegated native macOS tooltip.
- Commands must operate on the real source tree.

## Reference comparison

PyCharm provides a contextual Project tool-window header and local
selection/expansion actions; VS Code Explorer provides similar creation,
collapse and reveal operations. The best common design keeps toolbar logic
attached to the existing tree model instead of duplicating a filesystem tree.
Avoid global context menus, decorative dead buttons and unsafe file creation.

## PYNIX design

1. Keep the original Project tree, single/double-click file behavior, folder
   disclosure, editor state and existing native file-operation handlers.
2. Pass real project root path as **JSON data**, never HTML. Show home-relative
   `~/...` path when possible, otherwise the resolved absolute path. Styling
   clips the muted path and keeps project name readable.
3. Rebuild the header as a **single** action group on each existing
   `renderTree()`; the MutationObserver already reconnects controls.
4. Use official, already bundled `general/add`, `locate`, `expandAll`,
   `collapseAll`, `moreVertical`, `hide`, `chevronDown` SVGs **in both**
   V4 display modes. Do not change the rest of the perimeter.
5. Reveal on `tree:hover` or keyboard focus, not only header hover.
   Use the same rounded hover and accessible focus style for every action.
6. All actions call current tree/editor APIs:
   - New → File or Directory, real native creation with exclusive
     `WorkspaceSession.create_file/create_directory`, no overwrites.
     Only known text extensions can be created from this menu; binary and
     hidden paths are rejected. Newly created items rebuild the tree.
   - Locate → select the current open tab and expand ancestor folders.
   - Expand Selected → reveal the selected folder and its ancestors;
     Shift+Command+Plus expands all nodes.
   - Collapse All → close all nested folders, retaining the project root.
   - Options → working Select Opened File, Expand All and Collapse All.
   - Hide → same existing native Project tool window toggle.
7. A narrow tree keeps **New**, **Options** and **Hide**; additional commands
   remain available in Options until the user widens the Project pane. A
   wider tree displays the full horizontal header, as in PyCharm.

## Boundaries

The code is part of the V4 IDE adapter, not the generic PYNIX_GUI public
toolkit. Real semantic tree indexing, project views other than Project,
file templates, and context-specific IDE Core actions require separate
Design Gates. No filesystem writes happen without clicking an action and
confirming a native prompt.

## Acceptance

- Accurate root name and path; ellipsis works under resize.
- Project dropdown, action icons, hover and keyboard focus work.
- Tooltips: New File or Directory, Select Opened File, Expand Selected,
  Collapse All, Options, Hide.
- Create both .pnx/.py files and a nested directory; reject invalid paths,
  symlinks and binary creations; no existing file overwritten.
- Selected file is brought into view without opening extra tabs.
- Expand/Collapse and Options operate without losing selection.
- Sidebar Project Hide/restore and all prior editor shortcuts still work.
- Native macOS screenshot comparison remains necessary after full CI.

## Automated checks

```bash
python -m pytest tests/test_ide_project_header_v4.py \
    tests/test_ide_pycharm_chrome.py tests/test_ide_workspace_preview.py \
    tests/test_ide_workspace_session.py -q
python -m pytest -q
git diff --check
```

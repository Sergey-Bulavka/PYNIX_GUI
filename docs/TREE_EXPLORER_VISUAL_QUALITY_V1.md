# Tree Explorer Visual Quality V1

## Goal
Make the semantic Tree control look like a recognizable file explorer, rather
than a collection of full-width push buttons. Visual reference: PyCharm's
Project pane (compact hierarchy, chevrons, folder/document icon distinction).

## Changes
- macOS: folder/document NSImage copied and resized from row height and native font point size (around 15–18 pt in a 30 pt row). The shared NSImage is never modified. Compact AppKit label button bounds based on measured approximation
  (not stretched to the entire panel width); native NSImage icons for folders
  and documents, preserving selection IDs and disclosure event mapping.
- Windows/Qt: use platform standard folder/document icons in QTreeWidget.
- Shared pure presentation helpers with focused tests.

## Current known boundary
Expandable nodes are inferred to be folders. An empty directory represented
as a leaf cannot be distinguished from an ordinary file by the current
GUITreeNode API; an explicit semantic node kind is a separate future change.

## Native QA
On macOS open Product Gallery -> Data Views, IDE App, File Manager.
Verify short filenames occupy compact visual widths, icons differ, nested
indentation is aligned, selected item can be opened, chevrons expand/collapse,
and keyboard navigation survives. Check system Light and Dark appearance.

Windows screenshots and physical interaction remain pending; CI checks
contracts only. No changes to GUI version in this pass.

# Project Explorer V2 — Lazy Folder Tree Design Gate

## User task

Explore real projects with deeply nested directories without freezing on startup
or arbitrarily hiding directories beyond a fixed depth.

## Alternatives and tradeoffs

VS Code and native file browsers reveal children as folders are expanded.
A bounded recursive scan is simple but violates discoverability and causes
needless disk I/O. A fully asynchronous provider is appropriate for remote
filesystems but not required for the current local read-only demonstration.

## V2 design

- The table continues to display the selected directory's direct entries.
- The tree traverses descendants only for explicitly expanded directories.
- Collapsed directories perform a one-level subdirectory check to determine
  whether to display the disclosure arrow (synthetic invisible label child).
- Opening a deep folder expands its ancestors so tree selection stays visible.
- IDs are project-relative and stable. Hidden directories remain opt-in.
- No AppKit/Qt APIs enter project model or app event handlers.

## Acceptance

- Reach nine nested directories without the former four-level cutoff.
- An unexpanded subtree is not recursively traversed.
- Expand/collapse does not navigate the table.
- Opening a directory by table selection keeps ancestor folders expanded.
- Full suite and cross-platform CI must pass.
- Native Mac tree disclosure and hidden-label rendering require interactive
  visual validation. Synthetic nodes are a temporary adapter until toolkit
  tree providers support explicit hasChildren without fake rows.

## Deferred

Large sibling sets still use synchronous one-level lookahead. For thousands
of immediate subdirectories, a provider API that caches hasChildren and
supports asynchronous expansion may be needed.

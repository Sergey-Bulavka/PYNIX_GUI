# PYNIX IDE V4 — Git tool window

Reference: [PyCharm — Investigate changes in Git repository](https://www.jetbrains.com/help/pycharm/investigate-changes.html), [Manage Git branches](https://www.jetbrains.com/help/pycharm/manage-branches.html), [Use Git worktrees](https://www.jetbrains.com/help/idea/use-git-worktrees.html).

## What is actually connected

The **Git** button on the bottom-left rail toggles its own Git tool view; it no longer redirects into the old Source Control project-tree mock. The Git content is isolated from Run, Problems, Debug and Terminal, and uses the existing resizable bottom dock.

**Log** contains:

- Left: a searchable branch/tree listing with HEAD (current branch), Local, Remote and Tags, including collapsible slash-separated namespaces such as feature/ and fix/. Clicking a ref filters Git history to that ref; it does not check it out.
- Center: bounded real Git log with parent-based commit-graph connectors, branch decorations, commit subjects, authors and date/time.
- Search and filter toolbar: text/hash search, exact branch, author, inclusive date range, project-relative path. All searches are performed through native Git CLI reading the chosen project root. New Log tabs preserve their own filter states.
- Right: changed files of the selected commit and actual commit metadata, plus a read-only textual unified diff when selecting a file.
- Refresh: reloads Git data. Separate asynchronous responses for Log, Commit and Diff avoid freezing the macOS UI and stale responses.

**Worktrees** lists actual git worktree paths, attached branches, hashes, locked and prunable states. Creating/deleting worktrees and checkout/cherry-pick/rebase/merge are **not enabled** yet: they require confirmation, dirty-buffer and multi-worktree guards. The UI does not invent Git operations or claim they succeeded.

## Safety / limitations

The native backend uses a narrow, read-only list of Git subprocess commands: rev-parse, branch --show-current, for-each-ref, worktree list --porcelain, log, show and diff-tree. It does not run a shell, mutate the repository, trigger checkout/merge/rebase, fetch from network or invoke external diff tools. Commit IDs must be complete hexadecimal hashes, and diff paths must be project-relative and present in the selected commit. Git output is bounded and text-rendered, never interpolated into HTML. Projects inside a parent repo do not leak the parent's history.

The default log returns the first **250** commits for the selected filters. Use branch/author/date/path filters to query further back in history, or search by a full SHA. Visual Git graph is derived from actual parent SHAs; it is not a fake static decoration. Local Git must be installed and the selected project must itself be a Git repository.

## macOS acceptance

1. Pull the latest feature/icon-system-v4 branch. Start the native IDE with a Git-backed PYNIX project.
2. Press the bottom-left **Git** icon: the Git tool window opens with Log, Worktrees, branch tree and commit list. Press the same icon again: the dock closes; press again: state returns. Other tools remain independent.
3. Check HEAD and Local > feature/fix against real output of git branch --all. Expand/collapse groups and choose a branch. Confirm only the history is filtered (no checkout).
4. Search text, hash, user, date and file path. Confirm real commit rows, correct authors, dates and graph connector positions.
5. Select a commit, inspect changed files and commit details, then select a file to show a real unified diff. Changes must render as plain text safely.
6. Create a second Log tab, filter it, switch between the tabs and confirm each retains its filters.
7. Open Worktrees and compare against git worktree list --porcelain; close/reopen the tab through the Git tabs menu.
8. Switch to Problems/Run/Terminal and back. Each window must retain its own content. Resize the dock and pane split.
9. Check original JetBrains toolbar vector sizing and dark backgrounds against the supplied PyCharm screenshot.

## Tests

    python -m pytest -q tests/test_ide_git_window.py tests/test_ide_git_snapshot.py tests/test_ide_edge_profile.py tests/test_ide_v4_separate_terminals.py

The automated tests cover API correctness, parser safety, source path boundaries, JavaScript syntax and native bridge registration. Real macOS visual acceptance still needs a WKWebView session.

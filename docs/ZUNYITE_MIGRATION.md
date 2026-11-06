# Zunyite GUI migration status

The toolkit public brand is **Zunyite GUI**. Zunyite source uses `.uny` and the `zuny` / `zu` commands.

The `main` branch now distributes `zunyite-gui`, exposing `zunyite_gui` with `pynix_gui` compatibility (merged PR #43). The Workspace V4 migration was separately integrated into `feature/icon-system-v4` (merged PR #44). Embedded JetBrains assets and stable internal namespaces are preserved, and IDE development is still ongoing.

Acceptance: all macOS/Windows backend tests, GUI sample smoke tests, resource discovery and file icons support `.uny`, with an intentional compatibility path for `.pnx`.

**Status: package migration and Workspace V4 branch integration merged and checked in CI.** GitHub repository rename, local remotes, and full interactive IDE functionality are separate outstanding tasks.

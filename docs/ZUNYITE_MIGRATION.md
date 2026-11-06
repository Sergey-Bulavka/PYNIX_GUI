# Zunyite GUI migration status

The toolkit public brand is **Zunyite GUI**. Zunyite source uses `.uny` and the `zuny` / `zu` commands.

The migration branch changes the Python distribution name to `zunyite-gui`. The import namespace `pynix_gui` and embedded file icon assets remain transitional implementation details. They must not be blindly renamed before auditing dependencies in the compiler, IDE Core, and Workspace V4; the active Workspace V4 feature branch must be reconciled before merging this migration.

Acceptance: all macOS/Windows backend tests, GUI sample smoke tests, resource discovery and file icons support `.uny`, with an intentional compatibility path for `.pnx`.

**Status: branding and package metadata staged; Python import/API and active Workspace V4 migration pending; no verification run.**

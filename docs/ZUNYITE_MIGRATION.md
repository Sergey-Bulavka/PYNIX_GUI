# Zunyite GUI migration status

The toolkit public brand is **Zunyite GUI**. Zunyite source uses `.uny` and the `zuny` / `zu` commands.

The current Python distribution `pynix-gui`, import namespace `pynix_gui`, and embedded file icon assets are implementation details. They must not be blindly renamed before auditing dependencies in the compiler, IDE Core, and Workspace V4; the active Workspace V4 feature branch must be reconciled before merging this migration.

Acceptance: all macOS/Windows backend tests, GUI sample smoke tests, resource discovery and file icons support `.uny`, with an intentional compatibility path for `.pnx`.

**Status: branding in progress, runtime/API migration pending; no verification run.**

# PYNIX GUI Repository Extraction Plan

## Decision

Extract the accepted GUI implementation into a dedicated `PYNIX_GUI` repository while
preserving the public PYNIX `GUI.*` language surface.

The extraction is performed as a controlled migration, not a rewrite.

## Constraints

- no accepted GUI behavior may regress;
- the current 177-test GUI/Desktop regression remains the baseline;
- Git history for GUI implementation and docs should be preserved where practical;
- component version remains `0.1.0-dev`;
- PYNIX source syntax does not change merely because repository ownership changes;
- PYNIX compiler must not import platform backend implementation directly after extraction.

## Target ownership

### PYNIX_GUI

Move/own:

- `compiler/gui.py` platform-independent GUI model/runtime portions;
- `compiler/gui_layout.py`;
- `compiler/gui_design.py`;
- `compiler/gui_macos.py`;
- future backend modules;
- GUI-specific docs;
- GUI-specific tests;
- GUI examples/showcase.

During extraction these modules should be reorganized into a GUI-owned package rather than
retaining the misleading `compiler/` path.

Suggested package layout:

```text
pynix_gui/
    core.py
    layout.py
    design.py
    events.py
    resources.py
    controls/
    advanced/
    backends/
        macos.py
        windows.py
```

### PYNIX

Retain:

- GUI type declarations used by the compiler;
- protected namespace/static member knowledge;
- stdlib call signatures;
- adapter boundary that invokes the installed/linked PYNIX_GUI runtime;
- language-level integration tests.

## Extraction stages

### Stage 1 — Repository/bootstrap

Create empty `Sergey-Bulavka/PYNIX_GUI`.
Add licensing, README, version metadata, contribution/agent rules and initial architecture
documents.

### Stage 2 — Pure modules first

Move/copy with history where practical:

- layout;
- design tokens;
- GUI value/event model portions that do not depend on compiler diagnostics/runtime.

Keep compatibility imports in PYNIX temporarily.

### Stage 3 — Backend extraction

Move macOS realization behind a GUI backend interface.

PYNIX runtime receives/constructs the GUI backend through the adapter rather than importing
AppKit implementation from the compiler package.

### Stage 4 — Runtime boundary

Replace direct PYNIX compiler-package ownership of GUI runtime calls with a narrow adapter
API.

No public PYNIX source change.

### Stage 5 — Test split

PYNIX_GUI owns toolkit tests.
PYNIX owns integration/typing/binding tests.

Both repositories retain a small contract suite to detect version skew.

### Stage 6 — Advanced development

All new advanced GUI work happens in PYNIX_GUI.
PYNIX changes only when a new public language binding is required.

## Version compatibility

PYNIX should declare the compatible GUI component range explicitly once packaging begins.

Development checkout may use an editable/local dependency until the first package release.

## Acceptance of extraction

Extraction is complete when:

- current GUI behavior is reproducible from PYNIX_GUI;
- PYNIX integration suite remains green;
- GUI runtime can be developed/tested independently;
- no AppKit/Windows backend code remains owned by the PYNIX compiler package;
- advanced GUI milestones can proceed without unrelated compiler commits.

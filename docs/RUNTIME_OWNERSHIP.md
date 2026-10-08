# Runtime Ownership

PYNIX_GUI is the canonical owner of the GUI runtime implementation.

## Canonical modules

- `pynix_gui.core` — immutable GUI values, logical events, constructors, validation;
- `pynix_gui.layout` — deterministic geometry and layout;
- `pynix_gui.design` — PYNIX Standard tokens and semantic visual mappings;
- `pynix_gui.runtime` — backend-neutral standalone lifecycle;
- `pynix_gui.backends.macos` — macOS realization;
- `pynix_gui.backends._macos_host` — Cocoa host boundary.

## PYNIX language repository boundary

The PYNIX compiler repository may retain narrow compatibility modules for:

- conversion from PYNIX runtime collections into toolkit-native tuples;
- conversion of GUI toolkit diagnostics into PYNIX runtime diagnostics;
- public PYNIX method naming such as `GUIWindow.nextEvent()`;
- compiler/static semantic registration of the `GUI.*` language API.

It must not keep a second authoritative implementation of layout, design tokens, event
validation, or platform backend realization.

## Dependency rule

The dependency direction is:

```text
PYNIX language/runtime
        ↓
    PYNIX_GUI
        ↓
platform backend
```

PYNIX_GUI must never import the PYNIX compiler/runtime merely to implement GUI behavior.

## Version transition

Until the first independently packaged GUI release, the PYNIX repository pins an exact
PYNIX_GUI Git commit for reproducible bootstrap installs.

Once a stable package distribution exists, the Git commit dependency should be replaced by
an explicit compatible package version range.

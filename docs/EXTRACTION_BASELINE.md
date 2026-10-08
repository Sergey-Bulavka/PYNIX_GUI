# Extraction Baseline

## Source

Initial standalone extraction source:

- repository: `Sergey-Bulavka/PYNIX`
- branch: `feature/gui-architecture-v1`
- accepted GUI component version: `0.1.0-dev`

The five foundational layers were accepted before extraction:

- GUI-01 Window/Core
- GUI-02 Layout
- GUI-03 Surfaces
- GUI-04 Controls
- GUI-05 Visual System

## Verification baseline

Immediately before repository extraction, the affected PYNIX GUI/Desktop subsystem
regression was:

```text
177 passed
```

Native macOS acceptance had passed for:

- window/core lifecycle;
- layout and split resizing;
- surfaces and scrolling;
- controls and logical events;
- controlled rerender;
- PYNIX Standard System/Light/Dark visual themes.

## Migration rule

This repository is a controlled extraction, not a rewrite.

During migration:

1. PYNIX remains the compatibility source until the standalone package reproduces accepted
   behavior.
2. Standalone modules are verified independently before PYNIX switches to them.
3. No public PYNIX `GUI.*` syntax changes merely because implementation ownership moves.
4. The 177-test baseline remains the cross-repository compatibility gate until replaced by a
   stronger contract suite.

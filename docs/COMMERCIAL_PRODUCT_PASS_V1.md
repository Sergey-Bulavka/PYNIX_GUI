# Commercial Product Pass v1 — Design Gate

## Status

**ACTIVE — implementation milestone after 0.1.6-dev**

PYNIX GUI has proven architecture, deterministic layout, native backends, advanced controls,
resources and real PYNIX-language integration. The remaining weakness is product expression:
the current engineering Showcase demonstrates capability but does not communicate a
commercially competitive toolkit.

This milestone deliberately improves the product before Windows native acceptance and before
returning to PYNIX_IDE.

## Product goal

A developer opening the PYNIX GUI Gallery must immediately understand both:

1. what the toolkit can build;
2. why the PYNIX surface is simpler than lower-level desktop frameworks.

The target is not to clone Qt. The target is commercial-quality defaults with substantially
less ceremony.

## Principles

- Complex inside. Simple outside.
- Rich result from small declarative composition.
- Semantic design roles instead of arbitrary application paint.
- Consistent hierarchy, spacing, surfaces, states and density.
- Capability discoverability is part of product quality.
- Gallery examples must look like real software, not unit-test fixtures.
- Native handles remain private implementation details.
- Existing accepted behavior must remain regression protected.

## Scope

### Design System 2

Expand the PYNIX Standard system with:

- display/heading/subheading/overline typography;
- richer semantic surfaces;
- muted semantic status colors;
- card/hero/navigation surfaces;
- focus/hover/pressed/disabled treatment;
- consistent radius, spacing and elevation metadata.

### Commercial composition layer

Add high-level components implemented from the stable core:

- card;
- metric card;
- badge;
- alert;
- search field;
- navigation item/sidebar;
- section header;
- form section/row;
- property row;
- empty state;
- button group.

These components must remain backend-neutral and compose ordinary GUIView values.

### Product Gallery

Replace the engineering-only Showcase with a navigable product Gallery containing:

- Overview;
- Controls;
- Data;
- Editor;
- Canvas;
- Forms;
- commercial application-style examples.

The Gallery must make existing capabilities visible rather than merely mention them.

### Backend polish

Both AppKit and Qt backends must consume the semantic roles without exposing native styling
APIs. The reference macOS Gallery receives visual acceptance first. Windows native visual
acceptance remains pending until real Windows hardware/environment is available.

## Non-goals

This pass does not add:

- arbitrary CSS;
- arbitrary native handles;
- GPU Canvas;
- animation system;
- 3D;
- WebView.

Those require separate Design Gates.

## Acceptance

Commercial Product Pass v1 is accepted only when:

1. full standalone regression is green;
2. component tests are green;
3. three-OS CI remains green;
4. the new Gallery runs natively on macOS;
5. visual review shows clear hierarchy, coherent cards/surfaces and discoverable capability;
6. continuous Rich Editor editing remains intact;
7. documentation matches the actual API.

Windows native parity remains a separate final product gate.

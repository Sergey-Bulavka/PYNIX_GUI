# PYNIX GUI Architecture V1

## Status

Approved design direction. GUI-00 architecture phase.

Implementation must not begin beyond the currently accepted Desktop foundation until this
document and the GUI roadmap are internally consistent.

## Product goal

PYNIX GUI must let application authors describe what an interface should be, while the
runtime owns platform-specific layout, drawing, input, DPI, focus, and native integration.

Project principles:

- Complex ideas. Simple solutions.
- Complex inside. Simple outside.
- User intent over toolkit mechanics.
- Predictable geometry before decorative styling.
- Semantic styling before arbitrary per-widget paint.
- Beautiful applications must not require knowledge of AppKit, WinUI, GTK, CSS, or Qt internals.

The first major consumer will eventually be PYNIX_IDE, but the GUI is designed as a general
Standard Platform capability rather than an IDE-specific framework.

## Reference systems and extracted ideas

### Qt Quick / QML

Useful ideas:

- declarative tree composition;
- layouts separate from controls;
- minimum, preferred, and maximum sizes;
- explicit fill behavior;
- styling as a separate concern from control semantics;
- platform and cross-platform style families;
- complete application/window abstraction.

Do not copy:

- attached-property ceremony;
- broad CSS-like property surface;
- large historical API surface;
- toolkit-specific visual assumptions;
- multiple overlapping ways to express the same layout intent.

### Slint

Useful ideas:

- declarative component tree;
- compact layout model;
- minimum, preferred, maximum geometry;
- stretch behavior;
- compile-time style families;
- strong separation between widget meaning and visual style.

Do not copy:

- syntax or component model mechanically;
- style names as PYNIX public semantics;
- implementation-driven restrictions that are not necessary for PYNIX.

### PYNIX decision

PYNIX uses a small declarative retained view tree with a deterministic layout engine and a
semantic design system.

The public model should require fewer decisions than Qt/QML while preserving the layout
information needed for professional desktop applications.

## Public namespace direction

The long-term public namespace is:

```pynix
GUI...
```

The existing `Desktop` namespace remains the accepted experimental/compatibility surface
until GUI V1 proves replacement parity.

Do not mass-rename Desktop during GUI-00. Migration requires a separate compatibility plan.

## Core model

Application code creates immutable GUI view values. A window renders a complete desired
view tree. Runtime reconciliation maps that logical tree to native or portable host
implementation.

GUI application state remains ordinary PYNIX state.

The GUI runtime owns:

- native handles;
- layout calculation;
- DPI scaling;
- text measurement;
- painting;
- hit testing;
- focus;
- pointer and keyboard normalization;
- control state presentation;
- accessibility plumbing;
- resource realization;
- host event-loop integration.

Application code must not own or manipulate native widget objects.

## Five implementation layers

### Layer 1 — Window / Core

Purpose: establish the application and view lifecycle before layout or decoration.

Scope:

- GUI capability probe;
- application/window lifecycle;
- immutable GUIView;
- render/reconcile boundary;
- normalized GUIEvent;
- stable target identity;
- focus identity;
- logical enabled/disabled state foundation;
- resource identity foundation;
- host error normalization;
- deterministic close semantics.

Not included:

- sophisticated layout;
- colors;
- borders;
- icons;
- general controls.

Acceptance: lifecycle and reconciliation contracts are deterministic across repeated renders.

### Layer 2 — Layout

Purpose: define geometry independently of widget styling.

Minimum scope:

- Row;
- Column;
- Grid;
- Stack/overlay;
- Spacer;
- Fill;
- alignment;
- spacing;
- padding;
- minimum size;
- preferred size;
- maximum size;
- split panes;
- scroll geometry;
- empty-container semantics;
- resize propagation;
- intrinsic control sizing contract.

Sizing model:

Every view has logical constraints:

```text
minimum <= preferred <= maximum
```

Unspecified values are derived from intrinsic content and container rules.

Fill means: consume available space while respecting constraints.

Preferred size means: desired size, not a fixed size.

An empty Row/Column is geometrically empty unless explicit padding, minimum size, or fill
semantics make it non-empty.

No public AppKit hugging/compression priorities exist.

No percentages or CSS flexbox model are required in GUI V1.

### Layer 3 — Containers / Surfaces

Purpose: create visual and structural regions without mixing them with business controls.

Minimum scope:

- Panel;
- Group;
- Scroll;
- Tabs;
- separator;
- toolbar surface;
- status surface;
- optional collapsible region only after real pressure.

A Panel is a semantic visual surface. It may receive standardized background, border,
radius, and padding from the active design system.

Layout and visual surface remain separate concepts.

### Layer 4 — Controls

Initial control family:

- Text;
- Button;
- TextField;
- TextArea;
- CheckBox;
- RadioButton;
- ComboBox;
- Slider;
- ProgressBar;
- List;
- Image;
- Icon.

Later, after real pressure:

- Tree;
- Table;
- Menu;
- ContextMenu;
- Dialog;
- Tooltip;
- richer editor controls.

Controls expose meaning and state, not platform-native handles.

### Layer 5 — Visual / Design System

Purpose: make applications coherent and beautiful without per-widget improvisation.

The design system defines semantic tokens for:

- colors;
- text roles;
- surface roles;
- borders;
- separators;
- focus rings;
- spacing;
- padding;
- radii;
- typography;
- control heights;
- icon sizes;
- shadows/elevation where supported;
- hover;
- pressed;
- focused;
- disabled;
- selected;
- error/warning/success/information states;
- light/dark themes.

Application code should prefer semantic roles over raw values.

Example direction:

```pynix
GUI.panel(
    content,
    role = "sidebar"
)
```

rather than repeated arbitrary color/border declarations.

Raw styling escape hatches, if later required, must be narrow and explicit.

## Event model

GUI V1 continues the successful logical-event boundary:

- ACTIVATE
- CHANGE
- SELECTION
- CLOSE

New event kinds are added only for general UI semantics demonstrated by real applications.

Do not expose raw Cocoa/Win32/GTK events as public PYNIX semantics.

## Resources

GUI must eventually support:

- packaged images;
- SVG icons;
- raster images;
- logical icon identifiers;
- scale-aware assets.

Resource lookup must be deterministic and build-compatible.

Icons are content, not text glyph hacks.

## Themes and style strategy

PYNIX GUI ships with one canonical cross-platform design language: **PYNIX Standard**.

Goals:

- consistent visual rhythm;
- deterministic geometry;
- good light and dark variants;
- professional desktop appearance;
- the same semantic hierarchy across platforms.

A future `native` style may map semantic controls to host conventions, but native styling
must not redefine layout semantics.

The canonical style is the acceptance reference for screenshots and visual tests.

## Portability contract

Public GUI semantics are platform-independent.

Backends may use AppKit, WinUI, Qt, GTK, Skia, or another implementation technique, but
backend-specific behavior is not public API.

Initial verified platform remains macOS. Cross-platform claims require separate host
acceptance.

## Non-goals for GUI V1

- CSS compatibility;
- HTML DOM semantics;
- arbitrary constraint solver exposed to user code;
- arbitrary native handles;
- raw drawing as the primary application model;
- animation framework before static layout is stable;
- IDE-specific widgets before generic controls prove insufficient;
- pixel-perfect replication of Qt, macOS, Windows, or Material.

## Architecture acceptance gate

GUI-00 is complete only when:

1. all five layers have explicit scope;
2. sizing rules do not contradict existing Desktop lessons;
3. design tokens are specified;
4. default control metrics are specified;
5. event/resource/theme ownership is explicit;
6. migration from Desktop is planned, not improvised;
7. test cadence is documented;
8. GUI Showcase acceptance strategy is documented;
9. unresolved public semantics are explicitly listed.

## Open decisions

These remain design questions, not permission to improvise during implementation:

- final syntax for semantic roles versus typed enums;
- whether GUI V1 exposes preferredSize as one modifier or width/height helpers;
- whether Grid enters Layer 2 initial implementation or second batch;
- exact Desktop compatibility/deprecation schedule;
- accessibility public API beyond runtime defaults.

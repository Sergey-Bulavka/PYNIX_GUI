# Commercial Composition Layer

PYNIX GUI exposes a high-level product layer built entirely from the stable semantic core.
These components do not introduce native handles or backend-specific paint APIs.

## Components

- `card(title, content, subtitle=None, footer=None, role="card")`
- `hero(title, subtitle, actions=[])`
- `metric_card(label, value, detail="", badge_view=None)`
- `badge(label, tone="neutral")`
- `alert(title, message, tone="info")`
- `search_field(target, value="", placeholder="Search")`
- `navigation_item(target, label, selected=False)`
- `navigation_sidebar(title, items, footer=None)`
- `section_header(title, subtitle=None, action=None)`
- `form_row(label, control, helper=None)`
- `form_section(title, rows, description=None)`
- `property_row(label, value, detail=None)`
- `empty_state(title, message, action=None)`
- `button_group(buttons)`

## Why composition instead of another widget backend

The product layer deliberately composes existing `GUIView` values. A card or settings
section remains deterministic layout + semantic surfaces + ordinary controls. AppKit and Qt
therefore do not need a new native implementation for every product component.

This preserves the PYNIX product rule:

```text
Complex inside. Simple outside.
```

A developer should be able to assemble a finished application surface with small,
recognizable calls while the toolkit retains control of spacing, typography, colors,
states and platform realization.

## Semantic status tones

Badges and alerts use:

- neutral
- accent
- success
- warning
- danger
- info

Applications do not provide raw colors. PYNIX Standard resolves each tone for Light and
Dark appearance.

## Product Gallery

`examples/showcase.py` is now the Product Gallery. It contains:

- Overview
- Controls
- Data
- Rich Editor
- Canvas 2D
- Forms
- Dashboard application
- IDE application
- Settings application
- File Manager application

The Gallery is both a capability browser and the visual acceptance surface for the
Commercial Product Pass v1.

## Language surface

The composition layer is currently implemented in standalone PYNIX_GUI first. The PYNIX
language facade should expose the accepted components only after the Product Gallery passes
visual/product acceptance, preserving the existing staged architecture process.

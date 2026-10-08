# PYNIX GUI Design System V1

## Status

GUI-00 design specification.

This document standardizes the visual language before GUI controls are implemented.

## Goal

PYNIX GUI must not accumulate arbitrary colors, line widths, radii, paddings, and control
sizes independently in each application.

The default visual language is **PYNIX Standard**.

Applications may later choose another supported style, but every style must implement the
same semantic roles and geometry contract.

## Principles

- semantic tokens before raw values;
- small token set before unrestricted styling;
- visual consistency across controls;
- light and dark variants are first-class;
- accessibility contrast is a design requirement;
- geometry must remain stable when switching light/dark variants;
- platform rendering differences must not change semantic hierarchy;
- icons are vector-first where practical;
- decorative choices never redefine layout semantics.

## Token families

### 1. Color roles

Public design semantics use roles, not application-specific color names.

Required roles:

```text
background
surface
surfaceRaised
surfaceSunken
surfaceSelected
surfaceHover
surfacePressed

textPrimary
textSecondary
textMuted
textDisabled
textOnAccent

accent
accentHover
accentPressed
accentMuted

border
borderStrong
separator
focus

success
warning
error
info
```

Each role has a light and dark value.

Controls consume roles. They do not embed their own unrelated palette.

### 2. Line roles

Standard logical widths:

```text
hairline    host/DPI-aware one-pixel-equivalent
thin        1 logical unit
strong      2 logical units
focus       2 logical units minimum
```

Use:

- `separator` for structural division;
- `border` for normal container/control outlines;
- `borderStrong` for emphasized boundaries;
- `focus` only for keyboard/focus indication.

Do not simulate layout spacing with thick borders.

### 3. Spacing scale

Canonical spacing scale:

```text
space0 = 0
space1 = 4
space2 = 8
space3 = 12
space4 = 16
space5 = 24
space6 = 32
space7 = 48
```

These are logical units, resolved through host scale/DPI.

Default rules:

- inline icon/text gap: `space1` or `space2`;
- related controls: `space2`;
- control groups: `space3` or `space4`;
- panel padding: `space3`;
- major section separation: `space5`+.

Arbitrary values are not part of the normal application path.

### 4. Radius scale

```text
radius0 = 0
radius1 = 4
radius2 = 8
radius3 = 12
radiusRound = fully rounded where applicable
```

Default:

- compact controls: `radius1`;
- standard controls/panels: `radius2`;
- prominent cards/dialog surfaces: `radius3`.

### 5. Typography roles

Required roles:

```text
caption
body
bodyStrong
label
titleSmall
title
titleLarge
code
```

The active backend/style resolves font family and exact host metrics.

Application code chooses semantic role, not a raw font file.

Typography contract includes:

- size;
- weight;
- line height;
- letter spacing only when required;
- monospace preference for `code`.

### 6. Control metrics

Initial standard logical heights:

```text
compactControl = 28
standardControl = 32
comfortableControl = 40
toolbar = 40
statusBar = 28
```

These are design targets, not fixed pixel frames. A style/backend may adjust them where text
metrics or accessibility settings require more space.

Minimum clickable/tappable area must remain usable.

### 7. Icon metrics

Canonical icon boxes:

```text
iconSmall = 14
iconStandard = 16
iconMedium = 20
iconLarge = 24
iconHero = 32
```

SVG is the preferred authored format.

Icons must preserve aspect ratio and render scale-aware.

### 8. Surface roles

Initial semantic surface roles:

```text
app
toolbar
sidebar
workspace
panel
toolPanel
status
dialog
menu
selected
```

A surface role determines default background/border/separator behavior without changing
the child layout contract.

### 9. Interaction states

Controls and interactive surfaces support a common state vocabulary:

```text
normal
hover
pressed
focused
disabled
selected
error
warning
success
```

State visual priority:

1. disabled semantics;
2. error/warning when semantically required;
3. focus visibility;
4. selected/pressed;
5. hover;
6. normal.

Focus must remain visible in both light and dark themes.

## Standard component appearance

### Button

Default:

- standard control height;
- horizontal padding from spacing tokens;
- radius2;
- semantic label typography;
- hover/pressed/focus states;
- disabled state;
- optional leading/trailing icon.

Button variants are semantic, not arbitrary paint:

```text
primary
secondary
quiet
danger
```

### TextField / TextArea

Default:

- surfaceSunken/background role;
- border;
- stronger focus indication;
- error role when invalid;
- placeholder uses textMuted;
- selection follows accent/selected roles.

### Panel

Default:

- semantic surface role;
- optional border/separator according to role;
- radius only where the role requires it;
- standard panel padding.

A split pane is geometry. A Panel is visual structure. They are independent.

### Toolbar

Default:

- toolbar surface;
- compact or standard controls;
- consistent spacing;
- bottom separator where appropriate.

### Status bar

Default:

- status surface;
- compact typography/control height;
- top separator.

## Theme model

Initial required themes:

```text
PYNIX Standard Light
PYNIX Standard Dark
PYNIX Standard System
```

`System` selects light/dark according to host preference but keeps PYNIX Standard geometry.

Future styles may include:

- Native;
- High Contrast;
- application-supplied style packs.

A style pack must map the complete semantic token contract. Missing required tokens are a
controlled configuration error.

## Raw customization policy

GUI V1 does not start with arbitrary per-control CSS-like styling.

If real applications later prove a need for local overrides, add the narrowest semantic
override that solves the general problem.

Examples of acceptable future direction:

```pynix
GUI.panel(content, role = PanelRole.sidebar)
GUI.text("Warning", role = TextRole.bodyStrong)
GUI.button("save", "Save", role = ButtonRole.primary)
```

Avoid:

```text
border-left-width
margin-right
box-shadow string
CSS selector
host-native color object
```

unless future evidence demonstrates that semantic roles cannot solve the task.

## Visual acceptance

Every completed GUI layer must be represented in the GUI Showcase.

Visual acceptance includes:

- light theme;
- dark theme;
- normal/hover/pressed/focused/disabled where applicable;
- common window sizes;
- high-DPI rendering on a verified host;
- no clipped text at standard accessibility text settings;
- consistent spacing and alignment.

Screenshots supplement tests; they do not replace semantic tests.

## Versioning

Design-token meaning is public behavior once GUI V1 is accepted.

Exact palette values may evolve within a style version, but role meaning and geometry
contracts must remain compatible unless a documented GUI design version changes.

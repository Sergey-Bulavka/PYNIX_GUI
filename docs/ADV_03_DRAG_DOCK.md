# GUI-ADV-03 — Drag & Drop and Docking

## Status

**ACCEPTED — PYNIX GUI 0.1.3-dev**

Acceptance evidence:

```text
Standalone regression before final wiring fix: 66 passed
Native macOS Drag/Dock smoke: PASS
Real panel movement between dock regions: PASS
Controlled GUIDockState rerender: PASS
```

A final regression test was added for the dockTarget layout path after native smoke exposed
a missing geometry-neutral wrapper. The complete post-fix regression is intentionally
scheduled in the consolidated verification pass.

## Goal

Provide application-level drag/drop and dockable workspace semantics without exposing
platform drag objects, pasteboards, window handles, or pointer-coordinate protocols.

## Drag payload

Immutable value:

```text
GUIDragPayload
- kind: String
- value: String
- operations: ("copy" | "move")[]
```

The payload is deliberately logical and serializable.

Public wrappers:

```text
draggable(view, sourceId, payload)
drop_target(view, targetId, acceptedKinds, acceptedOperations=("copy", "move"))
```

A successful drop emits:

```text
GUIEvent(
    kind="DROP",
    target=<drop target id>,
    source_id=<drag source id>,
    payload_kind=<payload kind>,
    payload_value=<payload value>,
    operation=<copy|move>
)
```

The application owns the resulting data mutation and rerenders.

## Docking model

Immutable values:

```text
GUIDockPanel
- panel_id
- title
- content
- closable

GUIDockPlacement
- panel_id
- region
- order

GUIDockState
- placements
- active_left
- active_right
- active_bottom
- active_center
- left_width
- right_width
- bottom_height
```

Supported regions:

```text
left
right
bottom
center
```

The state is application-owned and deterministic. It can be persisted as ordinary logical
data and restored later.

Public constructor:

```text
dock_workspace(target, panels, state)
```

Docking interactions emit controlled state-change requests rather than mutating hidden
backend state.

```text
GUIEvent(
    kind="DOCK",
    target=<workspace target>,
    item_id=<panel id>,
    region=<new region>
)
```

## Layout rules

The workspace reserves left/right/bottom regions from the available rectangle and assigns
the remaining rectangle to center.

- left and right widths are state-controlled;
- bottom height is state-controlled;
- sizes are clamped to leave a viable center region;
- only the active panel in each region is visible;
- multiple panel identities may belong to one region and preserve order for future tab UI;
- inactive panel content does not participate in layout.

This is a deterministic retained layout contract.

## Relationship to Tree/Table

ADV-02 stable identities are the basis for structured drag payloads.

Tree/Table do not automatically become draggable merely by existing. The application wraps
the intended subtree or future structured-control source with explicit drag semantics.

## Diagnostics

Malformed drag/drop/docking contracts use:

```text
PYNIX-GUI-010
```

## Native acceptance

ADV-03 is accepted only when macOS proves:

- logical drag source;
- logical drop target;
- normalized DROP event;
- dock workspace region layout;
- panel move request normalized as DOCK;
- controlled rerender from updated state;
- persistence round-trip of docking state;
- no native object escapes the API.

Windows later implements the same semantics without changing application code.

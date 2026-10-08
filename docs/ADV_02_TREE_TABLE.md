# GUI-ADV-02 — Tree and Table

## Status

**ACCEPTED — PYNIX GUI 0.1.2-dev**

Acceptance evidence:

```text
Standalone regression: 54 passed
Native macOS Tree/Table smoke: PASS
Keyboard navigation: PASS
Controlled focus persistence across rerender: PASS
```

Verified stable identity selection, controlled tree expansion, table selection, scrolling,
semantic column sizing/alignment, keyboard navigation and focus restoration after rerender.

## Goal

Provide stable hierarchical and tabular controls for professional desktop applications
without exposing platform-native view objects.

## Identity model

Tree nodes and table rows use application-owned non-empty String identities.

Identity, not visual index, is authoritative across rerenders.

Selection events:

```text
GUIEvent(
    kind="SELECTION",
    target=<control target>,
    item_id=<stable node/row id>
)
```

Existing index-based SELECTION events remain valid for List, ComboBox, Tabs and other
index-oriented controls.

Tree expansion events:

```text
GUIEvent(
    kind="EXPANSION",
    target=<tree target>,
    item_id=<stable node id>,
    checked=<new expanded state>
)
```

## Tree

Immutable value:

```text
GUITreeNode
- node_id
- label
- children
```

Constructor:

```text
tree(target, nodes, expanded_ids=(), selected_id=None)
```

Contract:

- node ids are globally unique inside one tree;
- expanded ids must refer to nodes that exist;
- selected id is null or refers to an existing node;
- expansion is controlled by the application;
- selection is controlled by the application;
- hierarchy order is deterministic;
- collapsed descendants do not participate in visible row geometry.

## Table

Immutable values:

```text
GUITableColumn
- column_id
- title
- width
- alignment

GUITableRow
- row_id
- cells
```

Constructors:

```text
table_column(id, title, width=None, alignment="start")
table_row(id, cells)
table(target, columns, rows, selected_id=None)
```

Contract:

- column ids are unique;
- row ids are unique;
- every row has exactly one cell per column;
- cells are textual presentation values in ADV-02;
- selected id is null or refers to an existing row;
- headers are always explicit;
- optional column width is a semantic preferred width, not a native pixel handle.

## Geometry

Tree and Table are scrollable structured controls.

Default geometry is defined by PYNIX Standard metrics and does not depend on AppKit.

Tree:

- minimum 180×120;
- preferred 280×260.

Table:

- minimum 260×140;
- preferred 520×280.

## Native realization

The first macOS realization may internally use native scroll/container controls as long as:

- stable logical identity is preserved;
- selection/expansion events are normalized;
- headers/rows are visually coherent;
- scrolling works;
- rerender is deterministic;
- no AppKit objects escape the backend.

Keyboard navigation is part of the ADV-02 acceptance gate. If the first realization cannot
yet satisfy it, ADV-02 remains implementation-complete but not ACCEPTED until that gap is
closed.

## Diagnostics

Malformed structured data uses:

```text
PYNIX-GUI-009
```

## Acceptance

ADV-02 requires:

- platform-independent model tests;
- identity/validation tests;
- geometry tests;
- backend event normalization tests;
- standalone regression;
- native macOS visual/interaction smoke;
- keyboard selection/navigation confirmation;
- deterministic rerender with controlled selection and expansion.

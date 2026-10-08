# PYNIX GUI Public API V1

## Status

Implementation reference for the standalone package. The accepted component version remains
**0.1.3-dev** until the consolidated verification gate accepts the pending Canvas, Editor,
resource and Windows layers.

PYNIX GUI follows one rule throughout this API:

> application code owns logical state; the backend owns native objects.

No AppKit, Qt, Win32, Cocoa graphics context, pasteboard or native window handle is a public
application value.

## Runtime

```python
GUIRuntime(backend)
GUIRuntime.default()
GUIRuntime.is_available()
GUIRuntime.open(title, width, height) -> GUIWindow

GUIWindow.render(view)
GUIWindow.next_event() -> GUIEvent
GUIWindow.set_menu_bar(menu_bar)
GUIWindow.clear_menu_bar()
GUIWindow.present_dialog(dialog)
GUIWindow.dismiss_dialog(dialog_id)
GUIWindow.set_resources(catalog)
GUIWindow.close()
```

One live window is currently supported per GUIRuntime.

## Core composition

```python
empty()
row(children, spacing=8)
column(children, spacing=8)
fill(view)
spacer()
padding(view, ...)
min_size(view, width, height)
preferred_size(view, width, height)
max_size(view, width, height)
align(view, horizontal, vertical)
stack(children)
grid(columns, children, ...)
horizontal_split(...)
vertical_split(...)
scroll(view)
```

## Surfaces

```python
panel(view, role="panel")
group(view, role="group")
separator(...)
toolbar(view)
status_bar(view)
tabs(target, labels, selected, children)
```

## Controls

```python
text(...)
button(...)
text_field(...)
text_area(...)
check_box(...)
radio_button(...)
combo_box(...)
slider(...)
progress_bar(...)
list_view(...)
icon(...)
image(...)
vector_icon(...)
enabled(view, state)
focused(view, state)
theme(view, "system" | "light" | "dark")
```

## Commands and transient UI

Values:

```text
GUIShortcut
GUIMenuItem
GUIMenu
GUIMenuBar
GUIDialogAction
GUIDialog
```

Constructors:

```python
shortcut(...)
menu_item(...)
menu_separator()
submenu(...)
menu(...)
menu_bar(...)
context_menu(view, menu)
tooltip(view, text)
collapsible(...)
dialog_action(...)
dialog(...)
```

Command activation uses `GUIEvent(kind="ACTIVATE", target=...)`.

## Structured data

Values:

```text
GUITreeNode
GUITableColumn
GUITableRow
```

Constructors:

```python
tree_node(...)
tree(...)
table_column(...)
table_row(...)
table(...)
```

Tree/Table use stable application-owned string identities rather than visual row indexes.

## Drag/drop and docking

Values:

```text
GUIDragPayload
GUIDockPanel
GUIDockPlacement
GUIDockState
```

Constructors:

```python
drag_payload(...)
draggable(...)
drop_target(...)
dock_panel(...)
dock_placement(...)
dock_state(...)
dock_workspace(...)
dock_target(...)
```

Generic drops emit `DROP`; docking drops emit `DOCK`. The application updates data/state
and rerenders.

## Canvas 2D

Values:

```text
GUICanvasCommand
GUICanvasScene
```

Constructors:

```python
canvas_scene(...)
canvas(...)
canvas_line(...)
canvas_rect(...)
canvas_ellipse(...)
canvas_path(...)
canvas_text(...)
canvas_image(...)
canvas_clip(...)
canvas_transform(...)
```

Canvas is retained and immutable. Semantic hit targets emit ACTIVATE. GPU/3D is intentionally
outside this contract.

## Rich Editor

```python
text_span(start, end, role) -> GUITextSpan
rich_editor(
    target,
    text,
    selection_start,
    selection_end,
    spans=(),
    read_only=False,
) -> GUIView
```

The application owns text and selection. The backend supplies native editing, caret,
selection, scrolling and keyboard behavior.

## Resources

```python
image_resource(name, path)
vector_resource(name, scene)
svg_resource(name, path)
resource_catalog(resources)
GUIWindow.set_resources(catalog)
```

Application views then refer to logical names through `image(name)` or
`vector_icon(name)`.

## Logical events

Current event kinds:

```text
CLOSE
ACTIVATE
CHANGE
SELECTION
EXPANSION
DROP
DOCK
EDITOR_SELECTION
```

Payload members are optional by event family:

```text
target
text
index
number
checked
item_id
source_id
payload_kind
payload_value
operation
region
selection_start
selection_end
```

Each event family validates that only its legal payload combination is present.

## Diagnostics

```text
PYNIX-GUI-001  capability unavailable
PYNIX-GUI-002  window/lifecycle contract
PYNIX-GUI-003  render/host operation
PYNIX-GUI-004  event processing
PYNIX-GUI-005  layout/view structure
PYNIX-GUI-006  control/event contract
PYNIX-GUI-007  theme contract
PYNIX-GUI-008  commands/transient UI
PYNIX-GUI-009  Tree/Table
PYNIX-GUI-010  Drag/Drop/Docking
PYNIX-GUI-011  Canvas 2D
PYNIX-GUI-012  Rich Editor
PYNIX-GUI-013  resources
```

## Platform boundary

Reference backend:

```text
macOS -> AppKit/PyObjC
```

Parity backend under verification:

```text
Windows -> Qt/PySide6
```

Linux currently participates in backend-neutral regression only. Native Linux support is a
separate future product gate.

## Completion rule

A capability is not accepted because its code exists. It becomes accepted only after its
focused regression, full regression where required, native smoke, visual/interaction gate,
documentation sync and version bump are complete.

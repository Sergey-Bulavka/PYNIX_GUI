# GUI-ADV-01 — Commands and Transient UI

## Status

Implementation contract.

This milestone extends the accepted five-layer GUI foundation without creating a parallel
event, styling, layout, or native-handle model.

## Goals

Applications must be able to expose ordinary commercial desktop commands and transient
interaction without backend-specific code:

- application menu bar;
- nested menus;
- menu items and separators;
- semantic keyboard shortcuts;
- context menus;
- tooltips;
- collapsible disclosure regions;
- modal dialogs with application-owned GUI content;
- command-oriented use of the existing Toolbar surface;
- structured composition inside the existing StatusBar surface.

## Command model

Commands are not ordinary layout children.

Immutable command values:

```text
GUIShortcut
GUIMenuItem
GUIMenu
GUIMenuBar
GUIDialogAction
GUIDialog
```

Menu activation and dialog actions reuse:

```text
GUIEvent("ACTIVATE", target=...)
```

No raw key events, NSEvent, NSMenuItem, Win32 command IDs, or native handles enter the
public model.

## Semantic shortcuts

A shortcut has:

- a logical key;
- zero or more semantic modifiers.

Supported modifier vocabulary:

```text
primary
shift
alt
control
```

`primary` maps to the host's normal command modifier: Command on macOS and Control on
Windows.

This is deliberately not a raw modifier-bit API.

## Menu model

`menu_item(target, label, shortcut=None, enabled=True, checked=False)`

`menu_separator()`

`menu(title, items)`

`menu_bar(menus)`

Nested menus use a menu as an item through `submenu(menu)`.

Targets must remain non-empty and unique within one installed menu bar or context menu.

## Window command surface

Standalone runtime:

```text
GUIWindow.set_menu_bar(menuBar)
GUIWindow.clear_menu_bar()
GUIWindow.present_dialog(dialog)
GUIWindow.dismiss_dialog(dialogId)
```

The backend may realize the menu bar through the native application menu system and a dialog
through a native sheet/window. Those host objects never become application values.

## Context menus and tooltips

These remain declarative GUIView wrappers because they belong to a content subtree:

```text
context_menu(view, menu)
tooltip(view, text)
```

They are geometry-neutral.

The context menu is host-owned while open. Selecting an item emits ACTIVATE.

The tooltip is host-managed; the application does not implement hover timing.

## Collapsible

```text
collapsible(target, label, expanded, content)
```

The app owns `expanded`.

A disclosure interaction emits:

```text
GUIEvent("CHANGE", target=target, checked=<new expanded state>)
```

The application rerenders with the updated controlled state.

Collapsed content contributes no content height; expanded content participates in normal
layout.

## Dialog model

`GUIDialog` contains:

- stable dialog id;
- title;
- arbitrary GUIView content;
- one or more actions.

`GUIDialogAction` contains:

- logical target;
- label;
- semantic button role;
- enabled state;
- default-action flag.

Dialog buttons emit ACTIVATE and dismiss the dialog. Programmatic dismissal is supported.

Only one dialog with the same id may be active for a window.

## Toolbar and StatusBar

No duplicate Toolbar or StatusBar widgets are introduced.

The already accepted GUI-03 surfaces remain canonical. ADV-01 completes their desktop role
through composition with ordinary buttons, menus, text, separators, enabled state, and
future overflow policy.

A second parallel toolbar/status API is explicitly rejected.

## Diagnostics

Malformed command/transient values use:

```text
PYNIX-GUI-008
```

Backend failure while installing menus or presenting/dismissing dialogs uses the existing
host/runtime error family and is normalized by GUIRuntime.

## Native acceptance

On macOS, acceptance requires:

- real menu bar with nested menus;
- semantic shortcuts;
- enabled and checked menu states;
- context menu activation;
- native tooltip;
- controlled collapsible;
- native modal sheet/dialog;
- logical ACTIVATE/CHANGE events;
- rerender after command handling;
- Light/Dark/System compatibility.

Windows must later realize the same public semantics without changing application code.

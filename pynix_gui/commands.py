# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Platform-independent command and transient UI values."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from .core import GUIError, GUIView


_MODIFIERS = {"primary", "shift", "alt", "control"}
_BUTTON_ROLES = {"primary", "secondary", "quiet", "danger"}


def _non_empty(value, label: str) -> str:
    if type(value) is not str or value == "":
        raise GUIError("PYNIX-GUI-008", f"{label} must be a non-empty String.")
    return value


@dataclass(frozen=True, slots=True)
class GUIShortcut:
    key: str
    modifiers: tuple[str, ...] = ()

    def __post_init__(self):
        key = _non_empty(self.key, "GUI shortcut key")
        if len(key) > 32:
            raise GUIError("PYNIX-GUI-008", "GUI shortcut key is too long.")
        if type(self.modifiers) is not tuple:
            raise GUIError("PYNIX-GUI-008", "GUI shortcut modifiers must be a tuple.")
        if len(set(self.modifiers)) != len(self.modifiers):
            raise GUIError("PYNIX-GUI-008", "GUI shortcut modifiers must be unique.")
        if any(item not in _MODIFIERS for item in self.modifiers):
            raise GUIError("PYNIX-GUI-008", "GUI shortcut modifier is invalid.")


@dataclass(frozen=True, slots=True)
class GUIMenuItem:
    kind: str
    label: str | None = None
    target: str | None = None
    shortcut: GUIShortcut | None = None
    enabled: bool = True
    checked: bool = False
    submenu: "GUIMenu | None" = None

    def __post_init__(self):
        if self.kind == "separator":
            if any(
                value is not None
                for value in (self.label, self.target, self.shortcut, self.submenu)
            ) or self.checked or self.enabled is not True:
                raise GUIError("PYNIX-GUI-008", "GUI menu separator is malformed.")
            return

        if self.kind == "submenu":
            _non_empty(self.label, "GUI submenu label")
            if self.submenu is None or self.target is not None or self.shortcut is not None:
                raise GUIError("PYNIX-GUI-008", "GUI submenu is malformed.")
            if type(self.enabled) is not bool or self.checked:
                raise GUIError("PYNIX-GUI-008", "GUI submenu state is malformed.")
            return

        if self.kind != "item":
            raise GUIError("PYNIX-GUI-008", "GUI menu item kind is invalid.")

        _non_empty(self.label, "GUI menu item label")
        _non_empty(self.target, "GUI menu item target")
        if self.shortcut is not None and not isinstance(self.shortcut, GUIShortcut):
            raise GUIError("PYNIX-GUI-008", "GUI menu item shortcut is invalid.")
        if type(self.enabled) is not bool or type(self.checked) is not bool:
            raise GUIError("PYNIX-GUI-008", "GUI menu item state must be Bool.")
        if self.submenu is not None:
            raise GUIError("PYNIX-GUI-008", "GUI command item cannot also be a submenu.")


@dataclass(frozen=True, slots=True)
class GUIMenu:
    title: str
    items: tuple[GUIMenuItem, ...]

    def __post_init__(self):
        _non_empty(self.title, "GUI menu title")
        if type(self.items) is not tuple or any(
            not isinstance(item, GUIMenuItem) for item in self.items
        ):
            raise GUIError("PYNIX-GUI-008", "GUI menu items are invalid.")


@dataclass(frozen=True, slots=True)
class GUIMenuBar:
    menus: tuple[GUIMenu, ...]

    def __post_init__(self):
        if type(self.menus) is not tuple or any(
            not isinstance(menu, GUIMenu) for menu in self.menus
        ):
            raise GUIError("PYNIX-GUI-008", "GUI menu bar menus are invalid.")
        validate_menu_targets(self)


@dataclass(frozen=True, slots=True)
class GUIDialogAction:
    target: str
    label: str
    role: str = "secondary"
    enabled: bool = True
    default: bool = False

    def __post_init__(self):
        _non_empty(self.target, "GUI dialog action target")
        _non_empty(self.label, "GUI dialog action label")
        if self.role not in _BUTTON_ROLES:
            raise GUIError("PYNIX-GUI-008", "GUI dialog action role is invalid.")
        if type(self.enabled) is not bool or type(self.default) is not bool:
            raise GUIError("PYNIX-GUI-008", "GUI dialog action state must be Bool.")


@dataclass(frozen=True, slots=True)
class GUIDialog:
    dialog_id: str
    title: str
    content: GUIView
    actions: tuple[GUIDialogAction, ...]

    def __post_init__(self):
        _non_empty(self.dialog_id, "GUI dialog id")
        _non_empty(self.title, "GUI dialog title")
        if not isinstance(self.content, GUIView):
            raise GUIError("PYNIX-GUI-008", "GUI dialog content must be GUIView.")
        if type(self.actions) is not tuple or not self.actions:
            raise GUIError("PYNIX-GUI-008", "GUI dialog requires at least one action.")
        if any(not isinstance(action, GUIDialogAction) for action in self.actions):
            raise GUIError("PYNIX-GUI-008", "GUI dialog actions are invalid.")
        targets = [action.target for action in self.actions]
        if len(set(targets)) != len(targets):
            raise GUIError("PYNIX-GUI-008", "GUI dialog action targets must be unique.")
        if sum(1 for action in self.actions if action.default) > 1:
            raise GUIError("PYNIX-GUI-008", "GUI dialog may have only one default action.")


def shortcut(key: str, modifiers=()) -> GUIShortcut:
    if isinstance(modifiers, (str, bytes)) or not isinstance(modifiers, Sequence):
        raise GUIError("PYNIX-GUI-008", "GUI shortcut modifiers must be a sequence.")
    return GUIShortcut(key, tuple(modifiers))


def menu_item(
    target: str,
    label: str,
    shortcut_value: GUIShortcut | None = None,
    *,
    enabled: bool = True,
    checked: bool = False,
) -> GUIMenuItem:
    return GUIMenuItem(
        "item",
        label=label,
        target=target,
        shortcut=shortcut_value,
        enabled=enabled,
        checked=checked,
    )


def menu_separator() -> GUIMenuItem:
    return GUIMenuItem("separator")


def submenu(menu_value: GUIMenu, *, enabled: bool = True) -> GUIMenuItem:
    if not isinstance(menu_value, GUIMenu):
        raise GUIError("PYNIX-GUI-008", "GUI submenu requires a GUIMenu.")
    return GUIMenuItem(
        "submenu",
        label=menu_value.title,
        submenu=menu_value,
        enabled=enabled,
    )


def menu(title: str, items) -> GUIMenu:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise GUIError("PYNIX-GUI-008", "GUI menu items must be a sequence.")
    result = GUIMenu(title, tuple(items))
    validate_menu_targets(result)
    return result


def menu_bar(menus) -> GUIMenuBar:
    if isinstance(menus, (str, bytes)) or not isinstance(menus, Sequence):
        raise GUIError("PYNIX-GUI-008", "GUI menu bar menus must be a sequence.")
    return GUIMenuBar(tuple(menus))


def dialog_action(
    target: str,
    label: str,
    role="secondary",
    *,
    enabled=True,
    default=False,
) -> GUIDialogAction:
    return GUIDialogAction(target, label, role, enabled, default)


def dialog(dialog_id: str, title: str, content: GUIView, actions) -> GUIDialog:
    if isinstance(actions, (str, bytes)) or not isinstance(actions, Sequence):
        raise GUIError("PYNIX-GUI-008", "GUI dialog actions must be a sequence.")
    return GUIDialog(dialog_id, title, content, tuple(actions))


def _walk_menu_items(menu_value: GUIMenu):
    for item in menu_value.items:
        yield item
        if item.kind == "submenu":
            yield from _walk_menu_items(item.submenu)


def validate_menu_targets(value) -> None:
    if isinstance(value, GUIMenuBar):
        menus = value.menus
    elif isinstance(value, GUIMenu):
        menus = (value,)
    else:
        raise GUIError("PYNIX-GUI-008", "GUI menu target validation requires a menu value.")

    targets = []
    for menu_value in menus:
        for item in _walk_menu_items(menu_value):
            if item.kind == "item":
                targets.append(item.target)

    if len(set(targets)) != len(targets):
        raise GUIError("PYNIX-GUI-008", "GUI menu command targets must be unique.")

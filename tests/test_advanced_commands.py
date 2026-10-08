# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import (
    GUIError,
    GUIRuntime,
    collapsible,
    context_menu,
    dialog,
    dialog_action,
    empty,
    menu,
    menu_bar,
    menu_item,
    menu_separator,
    shortcut,
    submenu,
    text,
    tooltip,
    validate_view,
)
from pynix_gui.layout import measure


class FakeAdvancedBackend:
    def __init__(self):
        self.calls = []

    def is_available(self):
        return True

    def open(self, title, width, height):
        return object()

    def render(self, handle, view):
        self.calls.append(("render", handle, view))

    def next_event(self, handle):
        raise RuntimeError("not used")

    def close(self, handle):
        self.calls.append(("close", handle))

    def set_menu_bar(self, handle, value):
        self.calls.append(("set_menu_bar", handle, value))

    def clear_menu_bar(self, handle):
        self.calls.append(("clear_menu_bar", handle))

    def present_dialog(self, handle, value):
        self.calls.append(("present_dialog", handle, value))

    def dismiss_dialog(self, handle, dialog_id):
        self.calls.append(("dismiss_dialog", handle, dialog_id))


def test_adv01_shortcut_uses_semantic_modifier_vocabulary():
    value = shortcut("s", ["primary", "shift"])
    assert value.key == "s"
    assert value.modifiers == ("primary", "shift")

    with pytest.raises(GUIError) as failure:
        shortcut("s", ["command"])
    assert failure.value.code == "PYNIX-GUI-008"


def test_adv01_menu_supports_items_separators_and_nested_submenus():
    recent = menu("Recent", [
        menu_item("recent-one", "One"),
    ])
    file_menu = menu("File", [
        menu_item("new", "New", shortcut("n", ["primary"])),
        menu_separator(),
        submenu(recent),
    ])

    assert file_menu.items[0].target == "new"
    assert file_menu.items[1].kind == "separator"
    assert file_menu.items[2].submenu is recent


def test_adv01_menu_rejects_duplicate_targets_across_nested_tree():
    recent = menu("Recent", [
        menu_item("open", "Recent One"),
    ])

    with pytest.raises(GUIError) as failure:
        menu("File", [
            menu_item("open", "Open"),
            submenu(recent),
        ])

    assert failure.value.code == "PYNIX-GUI-008"


def test_adv01_menu_bar_rejects_duplicate_targets_across_top_level_menus():
    first = menu("File", [menu_item("shared", "Open")])
    second = menu("Edit", [menu_item("shared", "Repeat")])

    with pytest.raises(GUIError) as failure:
        menu_bar([first, second])

    assert failure.value.code == "PYNIX-GUI-008"


def test_adv01_dialog_requires_unique_actions_and_single_default():
    valid = dialog(
        "confirm",
        "Confirm",
        text("Continue?", "body"),
        [
            dialog_action("cancel", "Cancel"),
            dialog_action("ok", "Continue", "primary", default=True),
        ],
    )
    assert valid.dialog_id == "confirm"
    assert valid.actions[1].default is True

    with pytest.raises(GUIError):
        dialog(
            "bad",
            "Bad",
            empty(),
            [
                dialog_action("a", "A", default=True),
                dialog_action("b", "B", default=True),
            ],
        )


def test_adv01_context_menu_is_geometry_neutral():
    content = text("Context", "body")
    wrapped = context_menu(
        content,
        menu("Context", [menu_item("inspect", "Inspect")]),
    )

    assert measure(wrapped) == measure(content)
    validate_view(wrapped)


def test_adv01_tooltip_is_geometry_neutral():
    content = text("Hover", "body")
    wrapped = tooltip(content, "Helpful information")

    assert measure(wrapped) == measure(content)
    validate_view(wrapped)


def test_adv01_collapsible_has_controlled_expanded_geometry():
    content = text("Details", "body")
    closed = collapsible("details", "Details", False, content)
    opened = collapsible("details", "Details", True, content)

    closed_size = measure(closed)
    opened_size = measure(opened)

    assert closed_size.preferred.height == 32
    assert opened_size.preferred.height > closed_size.preferred.height
    validate_view(closed)
    validate_view(opened)


def test_adv01_runtime_delegates_menu_bar_install_and_clear():
    backend = FakeAdvancedBackend()
    runtime = GUIRuntime(backend)
    window = runtime.open("Commands", 640, 480)
    value = menu_bar([
        menu("File", [menu_item("open", "Open")]),
    ])

    window.set_menu_bar(value)
    window.clear_menu_bar()

    assert backend.calls[0][0] == "set_menu_bar"
    assert backend.calls[1][0] == "clear_menu_bar"


def test_adv01_runtime_delegates_dialog_present_and_dismiss():
    backend = FakeAdvancedBackend()
    runtime = GUIRuntime(backend)
    window = runtime.open("Dialog", 640, 480)
    value = dialog(
        "sample",
        "Sample",
        text("Body", "body"),
        [dialog_action("ok", "OK", "primary", default=True)],
    )

    window.present_dialog(value)
    window.dismiss_dialog("sample")

    assert backend.calls[0][0] == "present_dialog"
    assert backend.calls[1] == ("dismiss_dialog", window._handle, "sample")



def test_adv01_dialog_event_maps_survive_main_render_replacement():
    from pynix_gui.backends import MacOSGUIBackend

    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    window = object()
    dialog_control = object()
    dialog_tab = object()

    backend._gui_control_meta_by_window[window] = {}
    backend._gui_tab_buttons_by_window[window] = {}
    backend._gui_dialog_controls_by_window[window] = {
        "settings": {
            dialog_control: ("textField", "dialog-name"),
        }
    }
    backend._gui_dialog_tab_buttons_by_window[window] = {
        "settings": {
            dialog_tab: ("dialog-tabs", 1),
        }
    }

    backend._merge_dialog_event_maps(window)

    assert backend._gui_control_meta_by_window[window][dialog_control] == (
        "textField",
        "dialog-name",
    )
    assert backend._gui_tab_buttons_by_window[window][dialog_tab] == (
        "dialog-tabs",
        1,
    )

# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Native menu adapter for the V4 WKWebView acceptance workspace.

The public PYNIX_GUI MenuBar belongs to GUIRuntime windows. V4 currently uses
a raw WKWebView, so this narrow adapter forwards native selections to existing
browser actions instead of introducing a second IDE command implementation.
"""
from __future__ import annotations

import json

MENU_GROUPS = (
    ("File", (("file.save", "Save", "s", False),)),
    ("Edit", (
        ("edit.find", "Find in File", "f", False),
        ("edit.replace", "Replace in File", "f", False),
        ("edit.findProject", "Find in Project", "f", True),
        ("edit.goToLine", "Go to Line", "l", False),
    )),
    ("Navigate", (
        ("navigate.definition", "Go to Definition", "", False),
        ("navigate.references", "Find References", "", False),
        ("navigate.type", "Type at Cursor", "", False),
    )),
)

def command_ids() -> tuple[str, ...]:
    return tuple(item[0] for _, group in MENU_GROUPS for item in group)


def install_native_workspace_menu(app, webview, appkit):
    """Install system-menu entries that reuse the workspace command dispatcher.

    Called only by the macOS launcher; no AppKit dependency at import time.
    """
    from Foundation import NSObject

    class MenuDispatcher(NSObject):
        def activate_(self, sender):
            command = str(sender.representedObject())
            if command not in command_ids():
                return
            script = "window.pynixMenuCommand && window.pynixMenuCommand(" + json.dumps(command) + ");"
            webview.evaluateJavaScript_completionHandler_(script, None)

    dispatcher = MenuDispatcher.alloc().init()
    main_menu = appkit.NSMenu.alloc().initWithTitle_("PYNIX IDE")
    app_menu = appkit.NSMenu.alloc().initWithTitle_("PYNIX IDE")
    quit_item = appkit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Quit PYNIX IDE", "terminate:", "q")
    app_menu.addItem_(quit_item)
    app_item = appkit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("", None, "")
    app_item.setSubmenu_(app_menu)
    main_menu.addItem_(app_item)

    for title, entries in MENU_GROUPS:
        submenu = appkit.NSMenu.alloc().initWithTitle_(title)
        submenu.setAutoenablesItems_(False)
        for command, label, key, shift in entries:
            item = appkit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                label, "activate:", key)
            item.setRepresentedObject_(command)
            item.setTarget_(dispatcher)
            if key:
                mask = appkit.NSEventModifierFlagCommand
                if shift:
                    mask |= appkit.NSEventModifierFlagShift
                if command == "edit.replace":
                    mask |= appkit.NSEventModifierFlagOption
                item.setKeyEquivalentModifierMask_(mask)
            submenu.addItem_(item)
        parent = appkit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, "")
        parent.setSubmenu_(submenu)
        main_menu.addItem_(parent)

    app.setMainMenu_(main_menu)
    return dispatcher  # Strong reference retained by caller.

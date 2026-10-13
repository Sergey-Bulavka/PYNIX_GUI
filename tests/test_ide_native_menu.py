"""Regression checks for the native V4 menu adapter (portable, no AppKit import)."""
from pathlib import Path

from pynix_gui.ide_native_menu import MENU_GROUPS, command_ids
from examples import ide_native_v4
from pynix_gui import ide_workspace_preview


def test_native_menu_commands_are_unique():
    ids = command_ids()
    assert len(ids) == len(set(ids))
    assert "file.save" in ids
    assert "navigate.definition" in ids


def test_v4_installs_native_menu_on_actual_workspace():
    source = Path(ide_native_v4.__file__).read_text(encoding="utf-8")
    assert "install_native_workspace_menu(app, view, AppKit)" in source
    assert "window.setContentView_(view)" in source


def test_every_native_command_is_wired_to_existing_web_actions():
    source = Path(ide_workspace_preview.__file__).read_text(encoding="utf-8")
    assert "window.pynixMenuCommand=command=>" in source
    for command in command_ids():
        assert "case '" + command + "':" in source
    assert "case 'file.save': saveSource();" in source
    assert "case 'navigate.definition': nav('Definition');" in source
    assert "case 'navigate.references': nav('References');" in source


def test_native_menu_has_no_duplicate_keyboard_chords():
    chords = [
        (key, shift, command == "edit.replace")
        for _, items in MENU_GROUPS
        for command, _, key, shift in items if key
    ]
    assert len(chords) == len(set(chords))


def test_replace_uses_native_command_option_f():
    menu = {command: (key, shift) for _, items in MENU_GROUPS
            for command, _, key, shift in items}
    assert menu["edit.replace"] == ("f", False)
    source = Path(__import__("pynix_gui.ide_native_menu", fromlist=["__file__"]).__file__).read_text(encoding="utf-8")
    assert 'if command == "edit.replace":' in source
    assert "mask |= appkit.NSEventModifierFlagOption" in source

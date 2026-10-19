"""Native PyCharm-style Settings V1: typed data and real window wiring."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pynix_gui.ide_settings_window import (
    CATEGORIES, DEFAULTS, SettingsStore, editor_font_script,
    settings_html, validate_editor_settings,
)


def test_settings_defaults_and_versioned_persistence_are_user_scoped(tmp_path):
    file = tmp_path / "Library" / "Application Support" / "PYNIX" / "ide-settings-v1.json"
    store = SettingsStore(file)
    assert store.read() == DEFAULTS
    assert not file.exists()
    desired = {"editor.font_size": 14.5, "editor.line_height": 1.3}
    assert store.write(desired) == desired
    assert store.read() == desired
    assert json.loads(file.read_text(encoding="utf-8")) == desired
    assert file.stat().st_mode & 0o077 == 0


@pytest.mark.parametrize("bad", [
    None, [], {}, {"editor.font_size": 13},
    {"editor.font_size": True, "editor.line_height": 1.2},
    {"editor.font_size": 13, "editor.line_height": "1.2"},
    {"editor.font_size": float("nan"), "editor.line_height": 1.2},
    {"editor.font_size": 36.1, "editor.line_height": 1.2},
    {"editor.font_size": 7.9, "editor.line_height": 1.2},
    {"editor.font_size": 13, "editor.line_height": 2.6},
    {"editor.font_size": 13, "editor.line_height": .9},
    {"editor.font_size": 13, "editor.line_height": 1.2, "token": "bad"},
])
def test_settings_reject_invalid_data(bad):
    with pytest.raises(ValueError):
        validate_editor_settings(bad)


def test_corrupt_settings_fall_back_safely_without_overwrite(tmp_path):
    file = tmp_path / "settings.json"
    file.write_text("{invalid JSON", encoding="utf-8")
    before = file.read_bytes()
    assert SettingsStore(file).read() == DEFAULTS
    assert file.read_bytes() == before


def test_settings_page_navigation_reuses_real_sections_without_fake_switches():
    html = settings_html(DEFAULTS)
    assert "<title>Settings — PYNIX</title>" in html
    assert 'class="shell"' in html
    assert 'id="filter"' in html
    assert 'id="content"' in html
    assert 'id="cancel"' in html
    assert 'id="apply" disabled' in html
    assert 'id="ok"' in html
    assert "showPage(\"Editor\");" in html
    assert "const groups=new Map(categories)" in html
    assert "window.pynixSettingsSaved=result=>" in html
    assert "postMessage(data)" in html
    assert "No editable controls are shown" in html
    assert "File Encodings" in html
    assert "Code Editing" in html
    assert "Reader Mode" in html
    assert "Intentions" in html
    assert "Minimap" in html
    assert "TODO" in html
    assert "Settings — PYNIX" in html
    assert any(group == "Editor" for group, _ in CATEGORIES)


def test_settings_page_route_whitelist():
    html = settings_html(DEFAULTS, "Appearance")
    assert 'showPage("Appearance");' in html
    bad = settings_html(DEFAULTS, '</script><script>alert("oops")</script>')
    assert 'showPage("Editor");' in bad
    assert 'alert("oops")' not in bad


def test_settings_font_script_is_editor_scoped_without_changing_menu_font():
    js = editor_font_script(DEFAULTS)
    assert "pynix-user-editor-font" in js
    assert ".workspace-mode .pynix-source-input" in js
    assert ".workspace-mode .pynix-edit-highlight" in js
    assert ".workspace-mode .pynix-edit-gutter" in js
    assert ".pynix-ide-gear-menu" not in js
    assert ".pynix-services-options-menu" not in js
    assert "s['editor.font_size']" in js
    assert "s['editor.line_height']" in js


def test_native_settings_window_and_topbar_menu_are_connected():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    assert "class SettingsWindowHandler(NSObject):" in native
    assert 'settings_handler, "pynixIDEWindow"' in native
    assert 'self, "pynixSettings"' in native
    assert 'settings_window.setTitle_("Settings — PYNIX")' in native
    assert "settings_html(settings_store.read(), page)" in native
    assert "settings_store.write(dict(request.get(" in native
    assert "editor_font_script(settings_store.read())" in native
    assert "editor_font_script(values)" in native
    assert "setReleasedWhenClosed_(False)" in native

    assert "const gearMenu=document.createElement('div');" in chrome
    assert 'gearMenu.setAttribute(\'role\',\'menu\')' in chrome
    assert "gearItem('Settings…',()=>openSettings('Editor')" in chrome
    assert "gearItem('Theme…',()=>openSettings('Appearance'))" in chrome
    assert "gearItem('Keymap…',()=>openSettings('Keymap'))" in chrome
    assert "bridge.postMessage({action:'open-settings',page});" in chrome
    assert "event.metaKey" in chrome
    assert "settings.setAttribute('aria-expanded'" in chrome
    assert "document.querySelectorAll('.workspace-mode .rail>.rail-item')[5]?.click();" not in chrome


def test_settings_store_atomic_write_keeps_valid_config_on_failed_input(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    previous = {"editor.font_size": 18.0, "editor.line_height": 1.5}
    store.write(previous)
    with pytest.raises(ValueError):
        store.write({"editor.font_size": -10, "editor.line_height": 1.2})
    assert store.read() == previous

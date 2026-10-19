"""New UI edge roster and native host integration contracts."""
from pathlib import Path

from pynix_gui.ide_edge_profile import (
    TOOL_WINDOW_PROFILE, apply_edge_profile, EDGE_PROFILE_SCRIPT,
    EDGE_PROFILE_STYLE,
)
from pynix_gui.ide_icon_parity import BUNDLED_ICONS
from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog


def test_profile_has_four_edges_unique_labels_and_real_licensed_assets():
    edges = {"left-top", "left-bottom", "right-top", "right-bottom"}
    labels = [label for label, *_ in TOOL_WINDOW_PROFILE]
    assert len(labels) == len(set(labels))
    assert {edge for _, _, edge, _ in TOOL_WINDOW_PROFILE} == edges
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for label, icon, edge, state in TOOL_WINDOW_PROFILE:
        assert state in {"existing", "unavailable"}
        if label not in {"PYNIX Terminal", "PYNIX Packages"}:
            assert catalog.resolve(icon, dark=True, tool_window=True) is not None, label
        else:
            assert icon.startswith("pynix/")
    assert len(TOOL_WINDOW_PROFILE) >= 15


def test_profile_is_idempotent_and_never_pretends_disabled_tools_work():
    source = "<html><body class='workspace-mode'></body></html>"
    result = apply_edge_profile(source)
    assert result != source
    assert apply_edge_profile(result) == result
    assert "button.setAttribute('aria-disabled',String(unavailable));" in EDGE_PROFILE_SCRIPT
    assert "not implemented in PYNIX IDE" in EDGE_PROFILE_SCRIPT
    assert "More tool windows" in EDGE_PROFILE_SCRIPT
    assert "place('left-top'" in EDGE_PROFILE_SCRIPT
    assert "place('right-bottom'" in EDGE_PROFILE_SCRIPT
    assert 'pynix-extra-tool[aria-disabled="true"]' in EDGE_PROFILE_STYLE
    assert "<svg" not in result


def test_native_preview_loads_roster_after_original_icon_bindings():
    source = (Path(__file__).resolve().parents[1] / "examples" /
              "ide_native_v4.py").read_text(encoding="utf-8")
    assert "from pynix_gui.ide_edge_profile import apply_edge_profile" in source
    assert "document = apply_edge_profile(document)" in source
    assert source.index("document = apply_new_ui_icons(document)") < source.index(
        "document = apply_edge_profile(document)"
    )


def test_new_ui_rail_placement_keeps_existing_buttons_and_bottom_anchors():
    style = EDGE_PROFILE_STYLE
    for expected in (
        '.workspace-mode .ide>.rail>.rail-item{display:none!important}',
        '.workspace-mode .ide>.rail>.pynix-extra-tools[data-edge="left-top"]',
        '.workspace-mode .ide>.rail>.pynix-extra-tools[data-edge="left-bottom"]',
        '.workspace-mode .right-tools>.pynix-extra-tools[data-edge="right-top"]',
        'margin-top:auto!important',
        'overflow-y:auto!important',
    ):
        assert expected in style
    assert 'pointer-events:none' not in style
    assert "if(!unavailable)button.addEventListener('click',()=>clickExisting(entry));" in EDGE_PROFILE_SCRIPT
    assert "document.querySelectorAll('.workspace-mode .rail>.rail-item')[index]?.click();" in EDGE_PROFILE_SCRIPT
    assert "button.querySelectorAll('svg').forEach(svg=>svg.remove());" in EDGE_PROFILE_SCRIPT


def test_screenshot_pins_only_reference_icons_and_keeps_extra_tools_in_menu():
    from pynix_gui.ide_edge_profile import PINNED_TOOLS, EXISTING_ACTIONS
    assert {"Project", "Commit", "Pull Requests", "Structure",
            "Run", "PYNIX Terminal", "PYNIX Packages", "Services",
            "Terminal", "Problems", "Git",
            "Notifications", "AI Chat"} <= PINNED_TOOLS
    assert "Debug" not in PINNED_TOOLS
    assert "Search" not in PINNED_TOOLS
    assert "Version Control" not in PINNED_TOOLS
    assert EXISTING_ACTIONS["Run"] == "run-window"
    assert EXISTING_ACTIONS["Terminal"] == "terminal:system"
    assert EXISTING_ACTIONS["Problems"] == "dock:PROBLEMS"
    assert "x.pinned" in EDGE_PROFILE_SCRIPT
    assert "clickExisting(entry)" in EDGE_PROFILE_SCRIPT


def test_more_tool_windows_tracks_expansion_and_closes_on_escape():
    script = EDGE_PROFILE_SCRIPT
    assert "more.setAttribute('aria-expanded','false')" in script
    assert "more.setAttribute('aria-controls','pynix-more-'+edge)" in script
    assert "popover.hidden=!open;" in script
    assert "if(event.key==='Escape'){setOpen(false);more.focus();}" in script
    assert "if(!container.contains(event.target))setOpen(false);" in script


def test_overflow_menu_escapes_scroll_clipping_and_stays_on_screen():
    assert "position:fixed;z-index:600" in EDGE_PROFILE_STYLE
    assert "const bounds=more.getBoundingClientRect();" in EDGE_PROFILE_SCRIPT
    assert "edge.startsWith('left')?" in EDGE_PROFILE_SCRIPT
    assert "Math.min(window.innerWidth-width-4,left)" in EDGE_PROFILE_SCRIPT
    assert "Math.min(window.innerHeight-height-4,bounds.top)" in EDGE_PROFILE_SCRIPT

def test_tool_window_icons_do_not_use_handmade_python_or_other_fallbacks():
    from pynix_gui.ide_edge_profile import EDGE_PROFILE_SCRIPT
    assert "window.pynixPythonFileIcon?.()" not in EDGE_PROFILE_SCRIPT
    assert "entry.label==='Python Console'" not in EDGE_PROFILE_SCRIPT
    assert "const visual=(iconless&&!pictogram)?null:entry.svg;" in EDGE_PROFILE_SCRIPT
    assert "const unavailable=entry.state==='unavailable';" in EDGE_PROFILE_SCRIPT
    assert "const moreIcon=__MORE_ICON_DATA__;" in EDGE_PROFILE_SCRIPT


def test_exact_requested_six_items_in_the_top_left():
    from pynix_gui.ide_edge_profile import TOP_LEFT_ICONS, PINNED_TOOLS
    visible = [label for label, _, edge, _ in TOOL_WINDOW_PROFILE
               if edge == "left-top" and label in PINNED_TOOLS]
    assert visible == ["Project", "Commit", "Pull Requests", "Structure"]
    assert TOP_LEFT_ICONS == frozenset(visible)
    assert "entry.label==='Pull Requests'" in EDGE_PROFILE_SCRIPT
    assert "separator.className='pynix-extra-separator';" in EDGE_PROFILE_SCRIPT
    assert "separator.setAttribute('role','separator');" in EDGE_PROFILE_SCRIPT
    assert "const moreIcon=__MORE_ICON_DATA__;" in EDGE_PROFILE_SCRIPT
    assert "more.appendChild(node);" in EDGE_PROFILE_SCRIPT
    assert "more.textContent=edge==='left-top'?'•••'" not in EDGE_PROFILE_SCRIPT
    assert '[data-edge="left-top"] .pynix-extra-tool' in EDGE_PROFILE_STYLE
    assert "width:36px!important;height:36px!important" in EDGE_PROFILE_STYLE


def test_top_left_icons_load_in_iconless_mode_without_loading_other_rails():
    from pynix_gui.ide_icon_parity import BUNDLED_ICONS
    result = apply_edge_profile(
        "<html><body class='workspace-mode'></body></html>",
        directory=BUNDLED_ICONS, iconless=True,
    )
    assert "const iconless=true;" in result
    assert '"label": "Pull Requests"' in result
    assert "toolwindows/commit" in result
    assert "toolwindows/structure" in result
    assert r'\u003csvg' in result
    assert '"svg": null' in result
    assert "const pictogram=iconless&&(edge==='left-top'||edge==='left-bottom'||edge==='right-top');" in EDGE_PROFILE_SCRIPT
    assert "general/moreHorizontal" in result
    assert '"name": "github/pullRequests"' in result


def test_window_focus_changes_brightness_not_original_svg_variants():
    from pynix_gui.ide_edge_profile import EDGE_PROFILE_STYLE, EDGE_PROFILE_SCRIPT
    assert "window.pynixSetWindowActive=setWindowActive;" in EDGE_PROFILE_SCRIPT
    assert "window.addEventListener('focus',()=>setWindowActive(true));" in EDGE_PROFILE_SCRIPT
    assert "window.addEventListener('blur',()=>setWindowActive(false));" in EDGE_PROFILE_SCRIPT
    assert "workspace.classList.toggle('pynix-window-inactive',!active);" in EDGE_PROFILE_SCRIPT
    assert "setWindowActive(document.hasFocus());" in EDGE_PROFILE_SCRIPT
    assert ".workspace-mode.pynix-window-inactive" in EDGE_PROFILE_STYLE
    assert "opacity:.48!important" in EDGE_PROFILE_STYLE
    assert "background:#3a3b41!important" in EDGE_PROFILE_STYLE
    assert "@media(prefers-reduced-motion:reduce)" in EDGE_PROFILE_STYLE
    assert "catalog.svg(key, dark=dark, tool_window=True)" in (
        Path(__file__).resolve().parents[1] / "pynix_gui" /
        "ide_edge_profile.py").read_text(encoding="utf-8")


def test_macos_native_window_key_resign_events_notify_icon_layer():
    source = (Path(__file__).resolve().parents[1] /
              "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert 'window_focus_callback = {"update": None}' in source
    assert "def windowDidBecomeKey_(self, notification):" in source
    assert "def windowDidResignKey_(self, notification):" in source
    assert "update(True)" in source
    assert "update(False)" in source
    assert 'window_focus_callback["update"] = publish_window_focus' in source
    assert 'f"window.pynixSetWindowActive?.({literal});"' in source


def test_left_top_more_popup_matches_pycharm_reference_in_exact_order():
    from pynix_gui.ide_edge_profile import MORE_TOOL_WINDOWS, EDGE_PROFILE_SCRIPT
    labels = [item[0] for item in MORE_TOOL_WINDOWS]
    assert labels == [
        "Bookmarks", "Find", "Debug", "Coverage", "Endpoints",
        "Hierarchy", "Learn", "Python Process Output", "TODO", "Services",
    ]
    assert [item[2] for item in MORE_TOOL_WINDOWS] == [
        "⌘2", "⌘3", "⌘5", "", "", "", "", "", "", "",
    ]
    assert MORE_TOOL_WINDOWS[1][3] == "rail:1"
    assert MORE_TOOL_WINDOWS[2][3] == "dock:DEBUG CONSOLE"
    assert all(not item[3] for item in MORE_TOOL_WINDOWS[3:-1])
    assert MORE_TOOL_WINDOWS[-1][3] == "services-window"
    assert "const leftTopMore=__MORE_WINDOW_DATA__;" in EDGE_PROFILE_SCRIPT
    assert "if(edge==='left-top'){" in EDGE_PROFILE_SCRIPT
    assert "row.className='pynix-more-item';" in EDGE_PROFILE_SCRIPT
    assert "shortcut.textContent=entry.shortcut;" in EDGE_PROFILE_SCRIPT
    assert "if(entry.label==='Bookmarks')row.classList.add('is-highlighted');" in EDGE_PROFILE_SCRIPT
    assert "row.disabled=!entry.action;" in EDGE_PROFILE_SCRIPT


def test_left_top_more_icons_are_verifiable_jetbrains_art_not_drawn_fallbacks():
    from pynix_gui.ide_edge_profile import MORE_TOOL_WINDOWS
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    for label, key, _, _ in MORE_TOOL_WINDOWS:
        if label == "Endpoints":
            # JetBrains' proprietary Endpoints glyph is read directly from
            # the user's installed PyCharm app, never bundled as a copy.
            assert key == "localJetBrains/endpoints"
            continue
        assert key is not None, label
        for dark in (True, False):
            resolved = catalog.resolve(key, dark=dark, tool_window=True)
            assert resolved is not None, (label, dark)
            assert catalog.svg(key, dark=dark, tool_window=True), label
    html = apply_edge_profile(
        "<html><body class='workspace-mode'></body></html>",
        iconless=True,
    )
    assert html.count('"label": "Bookmarks"') >= 1
    assert '"label": "Endpoints"' in html
    assert '"svg": null' in html
    assert '"name": "pythonProcessOutput/process"' in html
    assert "pythonProcessOutput/process_dark.svg" not in html
    assert "const leftTopMore=__MORE_WINDOW_DATA__;" not in html
    assert "<svg" not in html
    assert "localJetBrains/endpoints" in html


def test_left_top_more_popup_visual_scope_and_overflow_placement():
    from pynix_gui.ide_edge_profile import EDGE_PROFILE_STYLE, EDGE_PROFILE_SCRIPT
    assert '.pynix-tool-profile-popover[data-edge="left-top"]' in EDGE_PROFILE_STYLE
    assert "width:296px!important" in EDGE_PROFILE_STYLE
    # PyCharm's screenshot has ~24 CSS px per row, not our old 36 px.
    assert "min-height:24px!important;height:24px!important" in EDGE_PROFILE_STYLE
    assert "padding:2px 10px!important" in EDGE_PROFILE_STYLE
    assert "popover.childElementCount*(edge==='left-top'?24:30)+18" in EDGE_PROFILE_SCRIPT
    assert "font:13px/1.25 system-ui" in EDGE_PROFILE_STYLE
    assert ".pynix-more-shortcut" in EDGE_PROFILE_STYLE
    assert "const width=edge==='left-top'?296:220;" in EDGE_PROFILE_SCRIPT
    assert "popover.dataset.edge=edge;" in EDGE_PROFILE_SCRIPT
    assert "popover.hidden=!open;" in EDGE_PROFILE_SCRIPT


def test_more_menu_resolves_original_endpoints_from_local_pycharm(monkeypatch):
    from pynix_gui import ide_edge_profile
    bundled = BUNDLED_ICONS / "svg/toolwindows/find_dark.svg"
    # The production resolver only returns bytes sourced from a local IDE
    # archive. Inject known original JetBrains artwork for this bridge test.
    official_vector = bundled.read_text(encoding="utf-8")
    calls = []
    def local_vector(*, dark):
        calls.append(dark)
        return official_vector
    monkeypatch.setattr(ide_edge_profile, "original_endpoints_svg", local_vector)
    html = ide_edge_profile.apply_edge_profile(
        "<html><body class='workspace-mode'></body></html>", iconless=True,
    )
    assert calls == [True]
    assert '"name": "localJetBrains/endpoints"' in html
    assert official_vector[:10].replace("<", r"\u003c") in html


def test_bottom_left_matches_seven_pycharm_reference_tools_without_more_button():
    from pynix_gui.ide_edge_profile import (
        BOTTOM_LEFT_ICONS, PINNED_TOOLS, EXISTING_ACTIONS,
    )
    visible = tuple(label for label, _, edge, _ in TOOL_WINDOW_PROFILE
                    if edge == "left-bottom" and label in PINNED_TOOLS)
    assert visible == BOTTOM_LEFT_ICONS == (
        "Run", "PYNIX Terminal", "PYNIX Packages", "Services",
        "Terminal", "Problems", "Git",
    )
    assert EXISTING_ACTIONS["Run"] == "run-window"
    assert EXISTING_ACTIONS["PYNIX Terminal"] == "terminal:pynix"
    assert EXISTING_ACTIONS["Terminal"] == "terminal:system"
    assert EXISTING_ACTIONS["Problems"] == "dock:PROBLEMS"
    assert EXISTING_ACTIONS["Git"] == "rail:2"
    assert EXISTING_ACTIONS["Services"] == "services-window"
    assert EXISTING_ACTIONS["PYNIX Packages"] == "packages-window"
    assert "if(edge==='left-bottom'||edge==='right-top'){" in EDGE_PROFILE_SCRIPT
    assert "host.appendChild(container);" in EDGE_PROFILE_SCRIPT


def test_lower_left_icons_are_exact_upstream_jetbrains_art_and_native_pynix_brand():
    from pynix_gui.ide_edge_profile import (
        BOTTOM_LEFT_ICONS, PYNIX_BRANDED_TOOLS,
    )
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    assert PYNIX_BRANDED_TOOLS == {"PYNIX Terminal", "PYNIX Packages"}
    names = {label: icon for label, icon, edge, _ in TOOL_WINDOW_PROFILE
             if edge == "left-bottom" and label in BOTTOM_LEFT_ICONS}
    assert names == {
        "Run": "toolwindows/run",
        "PYNIX Terminal": "pynix/pynix-terminal",
        "PYNIX Packages": "pynix/pynix-packages",
        "Services": "toolwindows/services",
        "Terminal": "terminal/terminal",
        "Problems": "toolwindows/problems",
        "Git": "toolwindows/vcs",
    }
    for name, icon in names.items():
        if name in PYNIX_BRANDED_TOOLS:
            continue  # Our own PYNIX marks are not in the JetBrains catalog.
        for dark in (True, False):
            resolved = catalog.resolve(icon, dark=dark, tool_window=True)
            assert resolved is not None, (name, dark)
            assert resolved.variant == ("dark_20" if dark else "light_20")
            svg = catalog.svg(icon, dark=dark, tool_window=True)
            assert svg.startswith("<!-- Copyright")
            assert "JetBrains s.r.o." in svg

    html = apply_edge_profile("<html><body class='workspace-mode'></body></html>",
                              iconless=True)
    assert "data:image/png;base64" not in html
    assert '"label": "PYNIX Terminal"' in html
    assert '"label": "PYNIX Packages"' in html
    assert '"isPynixBrand": true' in html
    assert "entry.brand" not in EDGE_PROFILE_SCRIPT
    assert "const visual=(iconless&&!pictogram)?null:entry.svg;" in EDGE_PROFILE_SCRIPT


def test_lower_left_icons_visible_in_iconless_mode_and_dim_on_blur():
    from pynix_gui.ide_iconless_mode import ICONLESS_STYLE
    assert '.pynix-extra-tools[data-edge="left-bottom"]' in EDGE_PROFILE_STYLE
    assert "gap:7px!important;padding-bottom:7px!important" in EDGE_PROFILE_STYLE
    assert "width:36px!important;height:36px!important" in EDGE_PROFILE_STYLE
    assert ".pynix-brand-package" not in EDGE_PROFILE_STYLE
    assert ".pynix-brand-terminal" not in EDGE_PROFILE_STYLE
    assert '.pynix-extra-tools[data-edge="left-bottom"] .pynix-extra-tool svg' in ICONLESS_STYLE
    assert '.pynix-extra-tools[data-edge="left-bottom"] .pynix-extra-tool img' not in ICONLESS_STYLE
    assert ".workspace-mode.pynix-window-inactive" in EDGE_PROFILE_STYLE


def test_right_top_uses_exact_jetbrains_notifications_and_chat_icons():
    from pynix_gui.ide_edge_profile import RIGHT_TOP_ICONS, PINNED_TOOLS
    actual = tuple(label for label, _, edge, _ in TOOL_WINDOW_PROFILE
                   if edge == "right-top" and label in PINNED_TOOLS)
    assert actual == RIGHT_TOP_ICONS == ("Notifications", "AI Chat")
    icons = {label: key for label, key, edge, _ in TOOL_WINDOW_PROFILE
             if edge == "right-top" and label in RIGHT_TOP_ICONS}
    assert icons == {
        "Notifications": "toolwindows/notifications",
        "AI Chat": "chat/toolWindowChat",
    }
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    notification = catalog.resolve("toolwindows/notifications", dark=True,
                                   tool_window=True)
    chat = catalog.resolve("chat/toolWindowChat", dark=True,
                           tool_window=True)
    assert notification is not None and notification.variant == "dark_20"
    assert chat is not None and chat.variant == "dark_20"
    assert chat.svg_path.name == "toolWindowChat@20x20.svg"
    assert 'viewBox="0 0 20 20"' in catalog.svg("chat/toolWindowChat",
                                               dark=True,tool_window=True)
    assert "toolWindowChat@20x20.svg" in str(chat.svg_path)


def test_right_top_buttons_keep_source_svg_and_state_dot_separate():
    from pynix_gui.ide_edge_profile import (
        EDGE_PROFILE_SCRIPT, EDGE_PROFILE_STYLE, apply_edge_profile,
    )
    from pynix_gui.ide_iconless_mode import ICONLESS_STYLE
    html = apply_edge_profile(
        "<html><body class='workspace-mode'></body></html>",
        iconless=True,
    )
    assert '"label": "Notifications"' in html
    assert '"label": "AI Chat"' in html
    assert '"name": "chat/toolWindowChat"' in html
    assert "button.dataset.toolWindow=entry.label;" in EDGE_PROFILE_SCRIPT
    assert "button.dataset.previewBadge='true';" in EDGE_PROFILE_SCRIPT
    assert "if(edge==='left-bottom'||edge==='right-top'){" in EDGE_PROFILE_SCRIPT
    assert "right-top" in ICONLESS_STYLE
    assert "data-preview-badge" in EDGE_PROFILE_STYLE
    assert "background:#467de4" in EDGE_PROFILE_STYLE
    assert "stroke:#9498a3" in EDGE_PROFILE_STYLE
    assert "fill:#9498a3" in EDGE_PROFILE_STYLE
    assert "opacity:.48!important" in EDGE_PROFILE_STYLE
    assert 'data-edge="right-top"] .pynix-extra-tool svg' in ICONLESS_STYLE


def test_right_top_no_more_menu_and_no_fake_ready_status():
    from pynix_gui.ide_edge_profile import (
        TOOL_WINDOW_PROFILE, EXISTING_ACTIONS, EDGE_PROFILE_SCRIPT,
    )
    state = {label: status for label, _, edge, status in TOOL_WINDOW_PROFILE
             if edge == "right-top"}
    assert state["Notifications"] == "unavailable"
    assert state["AI Chat"] == "unavailable"
    assert "Notifications" not in EXISTING_ACTIONS
    assert "AI Chat" not in EXISTING_ACTIONS
    assert "entry.state==='unavailable'" in EDGE_PROFILE_SCRIPT
    assert "button.title=entry.label+(unavailable?' — not implemented in PYNIX IDE':'');" in EDGE_PROFILE_SCRIPT

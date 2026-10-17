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
        assert catalog.resolve(icon, dark=True, tool_window=True) is not None, label
    assert len(TOOL_WINDOW_PROFILE) >= 15


def test_profile_is_idempotent_and_never_pretends_disabled_tools_work():
    source = "<html><body class='workspace-mode'></body></html>"
    result = apply_edge_profile(source)
    assert result != source
    assert apply_edge_profile(result) == result
    assert "button.disabled=entry.state==='unavailable'" in EDGE_PROFILE_SCRIPT
    assert "not implemented in PYNIX IDE" in EDGE_PROFILE_SCRIPT
    assert "More tool windows" in EDGE_PROFILE_SCRIPT
    assert "place('left-top'" in EDGE_PROFILE_SCRIPT
    assert "place('right-bottom'" in EDGE_PROFILE_SCRIPT
    assert "pynix-extra-tool:disabled" in EDGE_PROFILE_STYLE
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
    assert "if(!button.disabled)button.addEventListener('click',()=>clickExisting(entry));" in EDGE_PROFILE_SCRIPT
    assert "document.querySelectorAll('.workspace-mode .rail>.rail-item')[index]?.click();" in EDGE_PROFILE_SCRIPT
    assert "button.querySelectorAll('svg').forEach(svg=>svg.remove());" in EDGE_PROFILE_SCRIPT


def test_screenshot_pins_only_reference_icons_and_keeps_extra_tools_in_menu():
    from pynix_gui.ide_edge_profile import PINNED_TOOLS, EXISTING_ACTIONS
    assert {"Project", "Commit", "Pull Requests", "Structure",
            "Run", "Debug", "Terminal", "Problems",
            "Notifications", "AI Assistant"} <= PINNED_TOOLS
    assert "Search" not in PINNED_TOOLS
    assert "Version Control" not in PINNED_TOOLS
    assert EXISTING_ACTIONS["Run"] == "rail:3"
    assert EXISTING_ACTIONS["Terminal"] == "rail:4"
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
    assert "button.disabled=entry.state==='unavailable';" in EDGE_PROFILE_SCRIPT
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
    assert "const pictogram=iconless&&edge==='left-top';" in EDGE_PROFILE_SCRIPT
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

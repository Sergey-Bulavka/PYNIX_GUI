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
    assert "button.disabled=true" in EDGE_PROFILE_SCRIPT
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
        '.workspace-mode .rail>.rail-item:nth-child(-n+4){order:0!important',
        '.workspace-mode .rail>.pynix-extra-tools[data-edge="left-top"]{order:1!important',
        '.workspace-mode .rail>.pynix-extra-tools[data-edge="left-bottom"]{order:2!important',
        '.workspace-mode .rail>.rail-item:nth-child(n+5){order:3!important',
        '.workspace-mode .right-tools>.pynix-extra-tools[data-edge="right-bottom"]{order:2!important',
        'margin-top:auto!important',
        'overflow-y:auto!important',
    ):
        assert expected in style
    assert 'pointer-events:none' not in style
    assert 'display:none!important' not in style


def test_more_tool_windows_tracks_expansion_and_closes_on_escape():
    script = EDGE_PROFILE_SCRIPT
    assert "more.setAttribute('aria-expanded','false')" in script
    assert "more.setAttribute('aria-controls','pynix-more-'+edge)" in script
    assert "popover.hidden=!open;" in script
    assert "if(event.key==='Escape'){setOpen(false);more.focus();}" in script
    assert "if(!container.contains(event.target))setOpen(false);" in script

"""Actual V4 Search Everywhere routes to existing IDE actions and project data."""
from pathlib import Path

from pynix_gui.ide_search_everywhere import SEARCH_SCRIPT, apply_search_everywhere
from pynix_gui.ide_workspace_preview import workspace_bootstrap


def test_search_palette_is_injected_once_and_preserves_document():
    source='<html><body class="workspace-mode"><div id="workspace"></div></body></html>'
    result=apply_search_everywhere(source)
    assert result != source
    assert result.count('id="pynix-search-everywhere-script"') == 1
    assert 'id="workspace"' in result
    assert apply_search_everywhere(result) == result
    assert apply_search_everywhere("not html") == "not html"


def test_search_palette_uses_authoritative_buffers_and_safe_targets():
    source=(Path(__file__).resolve().parents[1] /
            "pynix_gui/ide_workspace_preview.py").read_text("utf-8")
    for contract in (
        "window.pynixSearchEverywhereCatalog=()=>{",
        "persistBuffer();",
        "category:'Files'",
        "category:definition[1]==='class'?'Classes':'Symbols'",
        "if(file.unloaded||typeof file.text!=='string')continue;",
        "window.pynixOpenSourceFromSearch=(source,line=1)=>{",
        "if(!byName.has(source))return false;",
        "show(source);",
        "selectNavigationLocation({source,line,column:1})",
    ):
        assert contract in source, contract
    assert "window.pynixSearchEverywhereCatalog?.()" in SEARCH_SCRIPT
    assert "window.pynixOpenSourceFromSearch?.(entry.source,entry.line||1);" in SEARCH_SCRIPT


def test_search_over_available_actions_and_settings_not_an_unconnected_mock():
    for contract in (
        "['Project',0]", "['Search',1]", "['Version Control',2]",
        "['Settings',5]", "'Run Current File'", "'Debug Current File'",
        "'Save Source'", "'More Actions'",
        "document.querySelector(entry.action)?.click();",
        "document.querySelectorAll('.workspace-mode .rail>.rail-item')[entry.rail]?.click();",
        "if(document.querySelector(action))",
    ):
        assert contract in SEARCH_SCRIPT, contract
    assert "document.body.appendChild(backdrop);" in SEARCH_SCRIPT
    assert "event.key==='ArrowDown'||event.key==='ArrowUp'" in SEARCH_SCRIPT
    assert "event.key==='Enter'" in SEARCH_SCRIPT
    assert "event.key==='Escape'" in SEARCH_SCRIPT
    assert "event.key!=='Shift'" in SEARCH_SCRIPT


def test_actual_native_v4_injects_search_in_both_display_modes():
    source=(Path(__file__).resolve().parents[1] /
            "examples/ide_native_v4.py").read_text("utf-8")
    assert "from pynix_gui.ide_search_everywhere import apply_search_everywhere" in source
    assert "document = apply_search_everywhere(document)" in source
    assert source.index("document = apply_search_everywhere(document)") > source.index(
        "document = apply_native_tooltips(document)"
    )
    assert "examples.ide_native_visual_shell" not in source


def test_search_tooltip_can_show_reference_multiline_description():
    from pynix_gui.ide_tooltips import TOOLTIP_STYLE
    assert "white-space:pre-line;" in TOOLTIP_STYLE

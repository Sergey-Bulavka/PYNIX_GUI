"""Regression checks for explicit tab pagination in native IDE V4.

These static contracts complement, but do not replace, macOS WKWebView
visual checks. Tab presence is determined by the PYNIX session maps.
"""
import re

from pynix_gui.ide_pycharm_chrome import CHROME_STYLE
from pynix_gui.ide_terminal_dock import TERMINAL_DOCK_JS


def rule(selector):
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", CHROME_STYLE)
    assert match is not None, selector
    return match.group(1)


def test_tab_strip_preserves_flex_alignment_without_overlap():
    strip = rule(".workspace-mode .pynix-terminal-session-tabs")
    assert "display:flex!important" in strip
    assert "overflow:hidden!important" in strip
    assert "gap:4px!important" in strip
    assert "max-width:none!important" in strip
    item = rule(".workspace-mode .pynix-terminal-session-tab")
    assert "flex:0 0 auto!important" in item
    assert "width:0!important" not in TERMINAL_DOCK_JS


def test_right_toolbar_controls_stay_at_right():
    spacer = rule(".workspace-mode .pynix-terminal-dock-gap")
    assert "flex:1 1 auto!important" in spacer
    assert "margin-left:auto!important" in spacer
    assert "header.append(title,sessions,newSession,chevron,gap,overflow,tools,hide)" in TERMINAL_DOCK_JS


def test_both_console_scopes_keep_independent_local_tabs():
    assert "const shellTabs=new Map();" in TERMINAL_DOCK_JS
    assert "const pynixTabs=new Map();" in TERMINAL_DOCK_JS
    assert "label:pynixTabs.size===0?'Local'" in TERMINAL_DOCK_JS
    assert "label:shellTabs.size===0?'Local'" in TERMINAL_DOCK_JS
    assert "if(scope==='pynix')createPynixTab()" in TERMINAL_DOCK_JS


def test_pagination_is_data_driven_not_scroll_clipping():
    assert "items.forEach(item=>{item.hidden=false;});" in TERMINAL_DOCK_JS
    assert "const activeIndex=Math.max(0,tabs.findIndex" in TERMINAL_DOCK_JS
    assert "item.hidden=!shown.has(index)" in TERMINAL_DOCK_JS
    assert "if(item.hidden)hidden.push(index)" in TERMINAL_DOCK_JS
    assert "for(const index of hidden)" in TERMINAL_DOCK_JS
    assert "sessions.scrollLeft=0" in TERMINAL_DOCK_JS
    assert "sessions.scrollWidth>" not in TERMINAL_DOCK_JS
    assert "const offscreen=" not in TERMINAL_DOCK_JS


def test_overflow_chevron_shows_only_for_missing_tabs():
    assert "const visible=hidden.length>0;" in TERMINAL_DOCK_JS
    assert "setArrow(visible);" in TERMINAL_DOCK_JS
    assert "overflow.style.visibility=visible?'visible':'hidden'" in TERMINAL_DOCK_JS
    assert "overflow.style.pointerEvents=visible?'auto':'none'" in TERMINAL_DOCK_JS
    assert "overflowToggle.dataset.hint='More Tabs ('+hidden.length+')'" in TERMINAL_DOCK_JS
    assert "entry.setAttribute('role','menuitem')" in TERMINAL_DOCK_JS
    assert ".workspace-mode .pynix-terminal-tab-overflow{display:block!important" in TERMINAL_DOCK_JS
    assert "flex:0 0 27px!important" in TERMINAL_DOCK_JS


def test_active_tab_and_overflow_selection_work():
    assert "add(activeIndex);" in TERMINAL_DOCK_JS
    assert "if(scope==='pynix'){" in TERMINAL_DOCK_JS
    assert "pynixId=id;paintSessions();paintPynix();" in TERMINAL_DOCK_JS
    assert "activeId=id;paintSessions();paintShell();" in TERMINAL_DOCK_JS
    assert "requestAnimationFrame(updateOverflow)" in TERMINAL_DOCK_JS


def test_overflow_debug_state_reports_missing_labels():
    assert "tabLayout:()=>({...tabOverflowDebug})" in TERMINAL_DOCK_JS
    assert "hidden:hidden.map(index=>tabs[index][1].label)" in TERMINAL_DOCK_JS
    assert "header.dataset.overflowTabs=String(visible)" in TERMINAL_DOCK_JS

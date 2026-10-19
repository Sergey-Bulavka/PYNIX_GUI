"""Guard the terminal tab layout contract against CSS regressions.

The macOS WKWebView screenshot acceptance remains necessary; these assertions
catch the conflicting CSS declarations which previously hid or stacked tabs.
"""
import re

from pynix_gui.ide_pycharm_chrome import CHROME_STYLE
from pynix_gui.ide_terminal_dock import TERMINAL_DOCK_JS


def css_rule(selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", CHROME_STYLE)
    assert match is not None, selector
    return match.group(1)


def test_tab_strip_uses_all_available_space_without_stacking():
    strip = css_rule(".workspace-mode .pynix-terminal-session-tabs")
    assert "width:max-content!important" in strip
    assert "flex:0 1 auto!important" in strip
    assert "max-width:none!important" in strip
    assert "overflow:hidden!important" in strip
    assert "max-width:min(50%,560px)" not in CHROME_STYLE
    assert "width:0!important" not in TERMINAL_DOCK_JS
    assert "flex:0 0 0!important" not in TERMINAL_DOCK_JS


def test_right_side_actions_remain_pinned_to_trailing_edge():
    gap = css_rule(".workspace-mode .pynix-terminal-dock-gap")
    assert "flex:1 1 auto!important" in gap
    assert "margin-left:auto!important" in gap
    assert "header.append(title,sessions,newSession,chevron,gap,overflow,tools,hide)" in TERMINAL_DOCK_JS


def test_overflow_keeps_active_tab_visible_and_has_svg_chevron():
    assert "const activeItem=items.find(item=>item.classList.contains('active'))" in TERMINAL_DOCK_JS
    assert "entry.setAttribute('role','menuitem')" in TERMINAL_DOCK_JS
    assert 'overflowToggle.innerHTML=\'<svg viewBox="0 0 16 16"' in TERMINAL_DOCK_JS
    assert ".pynix-terminal-session-tab[hidden]{display:none!important}" in TERMINAL_DOCK_JS


def test_both_tools_have_local_tabs_and_pycharmlike_selected_highlight():
    assert "label:pynixTabs.size===0?'Local'" in TERMINAL_DOCK_JS
    assert "label:shellTabs.size===0?'Local'" in TERMINAL_DOCK_JS
    active = css_rule(".workspace-mode .pynix-terminal-session-tab.active")
    assert "border-color:#3b66b0!important" in active


def test_overflow_budget_uses_dock_width_and_reserved_controls():
    # WKWebView may clip outside the strip's reported scroll viewport;
    # explicitly reserve fixed toolbar controls before showing overflow.
    assert "const natural=widths.reduce((sum,w)=>sum+w,0)" in TERMINAL_DOCK_JS
    assert "const capacity=Math.max(0,header.clientWidth-padding-fixed-" in TERMINAL_DOCK_JS
    assert "outerGap*controls.length" in TERMINAL_DOCK_JS
    assert "node===gap?0:node.getBoundingClientRect().width" in TERMINAL_DOCK_JS
    assert "const needsOverflow=natural>capacity+0.5" in TERMINAL_DOCK_JS
    assert "sessions.style.setProperty(property,value,'important')" in TERMINAL_DOCK_JS
    assert "show(hasInvisibleTabs);" in TERMINAL_DOCK_JS


def test_hidden_tab_menu_and_active_tab_preserved():
    assert "const activeItem=items.find(item=>item.classList.contains('active'))" in TERMINAL_DOCK_JS
    assert "sessions.scrollLeft+=selected.right-viewport.right" in TERMINAL_DOCK_JS
    assert "sessions.scrollLeft+=selected.left-viewport.left" in TERMINAL_DOCK_JS
    assert "entry.setAttribute('role','menuitem')" in TERMINAL_DOCK_JS
    assert "const byWidth=position< -0.5||position+widths[index]>actualWidth+0.5" in TERMINAL_DOCK_JS
    assert "tabOverflowDebug={" in TERMINAL_DOCK_JS
    assert "tabLayout:()=>({...tabOverflowDebug})" in TERMINAL_DOCK_JS


def test_overflow_arrow_remains_next_to_options():
    assert "overflow.hidden=false;" in TERMINAL_DOCK_JS
    assert "overflow.hidden=true;" not in TERMINAL_DOCK_JS
    assert "header.append(title,sessions,newSession,chevron,gap,overflow,tools,hide)" in TERMINAL_DOCK_JS
    assert "overflowToggle.innerHTML='<svg viewBox=" in TERMINAL_DOCK_JS
    assert "requestAnimationFrame(updateOverflow)" in TERMINAL_DOCK_JS
    assert ".workspace-mode .pynix-terminal-tab-overflow{display:block!important" in TERMINAL_DOCK_JS
    assert "flex:0 0 27px!important" in TERMINAL_DOCK_JS


def test_fully_offscreen_tabs_enable_chevron_even_if_budget_fits():
    # Regression: with Local 7 selected, Local and Local 2 can be scrolled
    # wholly past the left edge while needsOverflow is false in WKWebView.
    assert "const offscreen=rect.left<viewport.left-0.5||" in TERMINAL_DOCK_JS
    assert "rect.right>viewport.right+0.5;" in TERMINAL_DOCK_JS
    assert "if(!offscreen&&!byWidth)return;" in TERMINAL_DOCK_JS
    assert "if(!needsOverflow||" not in TERMINAL_DOCK_JS
    assert "const hasInvisibleTabs=hiddenCount>0;" in TERMINAL_DOCK_JS
    assert "show(hasInvisibleTabs);" in TERMINAL_DOCK_JS
    assert "header.dataset.overflowTabs=String(hasInvisibleTabs);" in TERMINAL_DOCK_JS

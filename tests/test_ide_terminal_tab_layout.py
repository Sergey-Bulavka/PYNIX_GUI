"""Terminal tab overflow contracts for native IDE V4.

The JavaScript is embedded in the preview bootstrap. These assertions guard
WKWebView-specific visibility and tab pagination behaviour. Visual acceptance
on macOS remains a separate step.
"""
import re

from pynix_gui.ide_pycharm_chrome import CHROME_STYLE
from pynix_gui.ide_terminal_dock import TERMINAL_DOCK_JS


def css_rule(selector):
    found = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", CHROME_STYLE)
    assert found is not None, selector
    return found.group(1)


def test_tab_strips_and_actions_retain_pycharm_spacing():
    strip = css_rule(".workspace-mode .pynix-terminal-session-tabs")
    assert "display:flex!important" in strip
    assert "gap:4px!important" in strip
    assert "overflow:hidden!important" in strip
    assert "flex:0 1 auto!important" in strip
    spacer = css_rule(".workspace-mode .pynix-terminal-dock-gap")
    assert "flex:1 1 auto!important" in spacer
    assert "margin-left:auto!important" in spacer
    assert "header.append(title,sessions,newSession,chevron,gap,overflow,tools,hide)" in TERMINAL_DOCK_JS


def test_overflow_menu_uses_session_map_not_scroll_coordinates():
    for expected in (
        "for(const item of items)item.hidden=false;",
        "const tabs=[...(scope==='pynix'?pynixTabs:shellTabs).entries()]",
        "const activeIndex=Math.max(0,tabs.findIndex(",
        "item.hidden=!shown.has(i);",
        "if(item.hidden)hidden.push(i);",
        "for(const i of hidden){",
        "entry.setAttribute('role','menuitem');",
        "const hasHidden=hiddenTabs.length>0;",
        "overflow.classList.toggle('has-hidden-tabs',hasHidden);",
    ):
        assert expected in TERMINAL_DOCK_JS
    assert "sessions.scrollWidth" not in TERMINAL_DOCK_JS
    assert "const offscreen=" not in TERMINAL_DOCK_JS


def test_overflow_control_is_real_button_with_independent_menu():
    assert "const overflow=document.createElement('div');" in TERMINAL_DOCK_JS
    assert "const overflowToggle=document.createElement('button');" in TERMINAL_DOCK_JS
    assert "overflowToggle.setAttribute('aria-haspopup','menu');" in TERMINAL_DOCK_JS
    assert "overflowToggle.addEventListener('click',()=>{" in TERMINAL_DOCK_JS
    assert "overflowPopup.hidden=!nextOpen;" in TERMINAL_DOCK_JS
    assert "overflowToggle.setAttribute('aria-expanded',String(nextOpen));" in TERMINAL_DOCK_JS
    assert "const closeOverflow=()=>{" in TERMINAL_DOCK_JS
    assert "overflow.classList.toggle('has-hidden-tabs',hasHidden);" in TERMINAL_DOCK_JS
    assert "overflow.style.setProperty('visibility',hasHidden?'visible':'hidden','important');" in TERMINAL_DOCK_JS
    assert "overflow.style.setProperty('pointer-events',hasHidden?'auto':'none','important');" in TERMINAL_DOCK_JS
    assert ".pynix-tab-overflow-control.has-hidden-tabs{" in TERMINAL_DOCK_JS
    assert "visibility:visible!important" in TERMINAL_DOCK_JS
    assert "overflow.open=false" not in TERMINAL_DOCK_JS


def test_overflow_reserves_permanent_27px_slot_next_to_options():
    assert "header.append(title,sessions,newSession,chevron,gap,overflow,tools,hide)" in TERMINAL_DOCK_JS
    assert "flex:0 0 27px!important" in TERMINAL_DOCK_JS
    assert "display:flex!important;align-items:center!important;justify-content:center!important" in TERMINAL_DOCK_JS
    assert ".pynix-tab-overflow-popup[hidden]{display:none!important}" in TERMINAL_DOCK_JS
    assert ".pynix-tab-overflow-popup:not([hidden]){display:block!important}" in TERMINAL_DOCK_JS
    assert "overflowPopup.setAttribute('role','menu');" in TERMINAL_DOCK_JS


def test_active_tab_remains_visible_and_hidden_tab_is_selectable():
    assert "include(activeIndex);" in TERMINAL_DOCK_JS
    assert "pynixId=id;paintSessions();paintPynix();" in TERMINAL_DOCK_JS
    assert "activeId=id;paintSessions();paintShell();" in TERMINAL_DOCK_JS
    assert "requestAnimationFrame(updateOverflow)" in TERMINAL_DOCK_JS
    assert "tabLayout:()=>({...tabOverflowDebug})" in TERMINAL_DOCK_JS


def test_both_panels_keep_independent_local_tabs():
    assert "const shellTabs=new Map();" in TERMINAL_DOCK_JS
    assert "const pynixTabs=new Map();" in TERMINAL_DOCK_JS
    assert "label:pynixTabs.size===0?'Local'" in TERMINAL_DOCK_JS
    assert "label:shellTabs.size===0?'Local'" in TERMINAL_DOCK_JS


def _paginate(widths, available, active, gap=4):
    # Model of the same active-first budgeting rule used in the browser.
    selected = set()
    consumed = 0

    def include(i):
        nonlocal consumed
        if i < 0 or i >= len(widths) or i in selected:
            return False
        extra = widths[i] + (gap if selected else 0)
        if selected and consumed + extra > available + 0.5:
            return False
        selected.add(i)
        consumed += extra
        return True

    include(active)
    for i in range(active - 1, -1, -1):
        if not include(i):
            break
    for i in range(active + 1, len(widths)):
        if not include(i):
            break
    return sorted(selected), [i for i in range(len(widths)) if i not in selected]


def test_seven_tabs_hide_local_and_local_2_when_only_five_fit():
    visible, hidden = _paginate([148] * 7, 780, 6)
    assert visible == [2, 3, 4, 5, 6]
    assert hidden == [0, 1]


def test_no_overflow_when_every_tab_fits():
    visible, hidden = _paginate([148] * 7, 1100, 6)
    assert visible == list(range(7))
    assert hidden == []


def test_hidden_tabs_arrow_works_without_svg_or_has_selector():
    assert "overflowToggle.textContent='⌄';" in TERMINAL_DOCK_JS
    assert ".pynix-tab-overflow-control.has-hidden-tabs{" in TERMINAL_DOCK_JS
    assert ".pynix-terminal-dock-bar:has(.pynix-terminal-session-tab[hidden])" in TERMINAL_DOCK_JS
    assert "header.classList.toggle('has-overflow-tabs',hasHidden)" in TERMINAL_DOCK_JS
    assert "overflow.style.setProperty('display','flex','important')" in TERMINAL_DOCK_JS
    assert "overflow.style.setProperty('visibility',hasHidden?'visible':'hidden','important')" in TERMINAL_DOCK_JS
    assert "overflow.style.setProperty('opacity',hasHidden?'1':'0','important')" in TERMINAL_DOCK_JS


def test_options_exposes_native_layout_diagnostics():
    assert "option('Tab Layout Diagnostics',()=>{" in TERMINAL_DOCK_JS
    assert "arrowDisplay:getComputedStyle(overflow).display" in TERMINAL_DOCK_JS
    assert "arrowVisibility:getComputedStyle(overflow).visibility" in TERMINAL_DOCK_JS
    assert "[Tab layout]" in TERMINAL_DOCK_JS


def test_native_final_layout_pass_reconciles_menu_and_arrow():
    # Fully hidden tabs must remain selectable even when WebKit resolves
    # flex measurements after the initial requestAnimationFrame.
    assert "const hiddenNow=[...sessions.children].map((el,i)=>({el,i}))" in TERMINAL_DOCK_JS
    assert "return el.hidden||rect.right<box.left-0.5||rect.left>box.right+0.5" in TERMINAL_DOCK_JS
    assert "entry.dataset.sessionId=id;" in TERMINAL_DOCK_JS
    assert "overflowPopup.appendChild(entry);existing.add(id);" in TERMINAL_DOCK_JS
    assert "setOverflow([...overflowPopup.children]);" in TERMINAL_DOCK_JS
    assert "tabOverflowDebug.hidden=[...overflowPopup.children].map(el=>el.textContent);" in TERMINAL_DOCK_JS

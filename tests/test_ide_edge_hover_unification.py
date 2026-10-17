"""All real V4 perimeter icons have the same hover/focus hit feedback.

Availability controls execution only: unfinished tools still expose their
label and status on hover without impersonating working commands.
"""
from pynix_gui.ide_edge_profile import (
    EDGE_PROFILE_SCRIPT, EDGE_PROFILE_STYLE, PINNED_TOOLS,
    TOOL_WINDOW_PROFILE, apply_edge_profile,
)


def test_all_four_edge_groups_share_one_hover_rule():
    expected = [label for label, _, edge, _ in TOOL_WINDOW_PROFILE
                if label in PINNED_TOOLS and edge in {
                    "left-top", "left-bottom", "right-top", "right-bottom"
                }]
    assert {"Commit", "Pull Requests", "Structure", "PYNIX Packages",
            "Notifications", "AI Chat", "Project", "Run"} <= set(expected)
    # The dynamic DOM factory gives every pinned tool the same button class.
    assert "button.className='pynix-extra-tool';" in EDGE_PROFILE_SCRIPT
    assert "button.dataset.toolWindow=entry.label;" in EDGE_PROFILE_SCRIPT
    assert "for(const entry of entries.filter(x=>x.edge===edge&&x.pinned))" in EDGE_PROFILE_SCRIPT
    # Uniform selectors apply regardless of icon availability or edge.
    assert ('.workspace-mode .pynix-extra-tools[data-edge] '
            '.pynix-extra-tool:hover:not([aria-pressed="true"])'
            in EDGE_PROFILE_STYLE)
    assert ('.workspace-mode .pynix-extra-tools[data-edge] '
            '.pynix-extra-tool:focus-visible:not([aria-pressed="true"])'
            in EDGE_PROFILE_STYLE)
    assert "background:#3a3d45!important;" in EDGE_PROFILE_STYLE
    assert ':hover:not([aria-pressed="true"]):not([aria-disabled="true"])' not in EDGE_PROFILE_STYLE


def test_hover_override_outprioritizes_right_transparent_and_inactive_rules():
    css = EDGE_PROFILE_STYLE
    right_override = ('[data-edge="right-top"] .pynix-extra-tool{')
    inactive_override = ('.workspace-mode.pynix-window-inactive '
                         '.pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool:hover')
    unified = '.pynix-extra-tool:hover:not([aria-pressed="true"])'
    assert right_override in css
    assert "background:transparent!important" in css
    assert inactive_override in css
    # Important: late, more specific override wins in WKWebView CSS cascade.
    assert css.rindex(unified) > css.rindex(right_override)
    assert css.rindex(unified) > css.rindex(inactive_override)
    assert css.rindex('background:#3a3d45!important') > css.rindex(right_override)


def test_active_side_item_stays_selected_and_more_button_highlights():
    css = EDGE_PROFILE_STYLE
    assert '.pynix-extra-tool[aria-pressed="true"]' in css
    assert 'background:#3574d6!important;color:#fff!important;' in css
    assert '.pynix-tool-profile-more:hover' in css
    assert '.pynix-tool-profile-more:focus-visible' in css
    assert '.pynix-tool-profile-more[aria-expanded="true"]' in css
    assert "more.setAttribute('aria-expanded',String(open));" in EDGE_PROFILE_SCRIPT
    assert "outline:2px solid #80b8f4" in css


def test_unavailable_controls_are_hoverable_but_never_execute_action():
    script = EDGE_PROFILE_SCRIPT
    assert "const unavailable=entry.state==='unavailable';" in script
    assert "button.setAttribute('aria-disabled',String(unavailable));" in script
    assert "button.dataset.pynixTooltip=entry.label+" in script
    assert "(unavailable?' (not available yet)':'')" in script
    assert "if(!unavailable)button.addEventListener('click',()=>clickExisting(entry));" in script
    assert "button.disabled=unavailable" not in script
    assert 'button.title=entry.label+' in script
    html = apply_edge_profile("<html><body class='workspace-mode'></body></html>",
                              iconless=True)
    assert "const iconless=true;" in html
    assert '"label": "AI Chat"' in html
    assert '"label": "Commit"' in html
    assert ".pynix-extra-tool:hover:not([aria-pressed=" in html

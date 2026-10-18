"""Project selector typography matches the IDE editor and file tree."""

import re

from pynix_gui.ide_pycharm_chrome import CHROME_STYLE, CHROME_SCRIPT, apply_pycharm_chrome


def test_project_view_label_uses_13_px_without_resizing_icons_or_hitbox():
    selector = ".workspace-mode .tree .pynix-project-view-switcher>summary"
    assert selector in CHROME_STYLE
    matches = re.findall(
        re.escape(selector) + r"\s*\{([^}]*)\}",
        CHROME_STYLE,
    )
    assert len(matches) == 1
    declarations = matches[0]
    assert "font-size:13px!important" in declarations
    assert "font-size:12px!important" not in declarations
    assert "font-weight:600!important" in declarations
    assert "gap:6px!important" in declarations
    assert "min-width:68px!important" in declarations
    assert "width:14px!important;height:14px!important" in CHROME_STYLE


def test_only_project_title_is_affected_not_buttons_or_explorer_rows():
    assert "viewLabel.className='pynix-project-view-label'" in CHROME_SCRIPT
    assert "viewLabel.textContent='Project'" in CHROME_SCRIPT
    assert ".workspace-mode .tree .project-entry .project-label," in CHROME_STYLE
    assert ".workspace-mode .tree .project-entry .pynix-project-root-path{" in CHROME_STYLE
    page = apply_pycharm_chrome(
        '<html><head></head><body class="workspace-mode"></body></html>',
        iconless=True,
    )
    assert "font-size:13px!important;font-weight:600!important" in page
    assert ".workspace-mode .tree .pynix-project-view-switcher>summary{" in page

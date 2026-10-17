"""Regression: a more-specific legacy !important rule pinned Project to 31px.

Old selector:
.workspace-mode .tree .tree-title.pynix-project-header (4 classes)
Newer (ineffective) selector:
.workspace-mode .tree .pynix-project-header (3 classes)
CSS cascade compares specificity BEFORE source order, even for !important.
"""

import re

from pynix_gui.ide_pycharm_chrome import CHROME_STYLE, apply_pycharm_chrome
from pynix_gui.ide_project_header_sync import (
    PROJECT_HEADER_SYNC_STYLE, apply_project_header_alignment,
)


def _declarations(css, property_name):
    """Extract CSS declarations from simple class-selector blocks."""
    matches = []
    for rule in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selectors = rule.group(1).strip()
        if not selectors.startswith(".workspace-mode"):
            continue
        for declaration in rule.group(2).split(";"):
            property_, colon, value = declaration.strip().partition(":")
            if colon and property_ == property_name:
                matches.append((selectors, value.strip()))
    return matches


def test_no_legacy_project_title_height_can_override_the_final_rule():
    rules = _declarations(CHROME_STYLE, "height")
    root = [(selector, value) for selector, value in rules
            if ".tree" in selector and ".pynix-project-header" in selector]
    assert root
    assert not any("31px" in value for _, value in root), root
    assert any(
        ".workspace-mode .tree .tree-title.pynix-project-header" in selector
        and value == "43px!important"
        for selector, value in root
    ), root
    assert any(
        ".workspace-mode .editor-tabs" in selector
        and value == "43px!important"
        for selector, value in rules
    )


def test_runtime_alignment_rule_matches_original_full_selector_specificity():
    selector = ".workspace-mode .tree .tree-title.pynix-project-header"
    assert selector in CHROME_STYLE
    assert selector in PROJECT_HEADER_SYNC_STYLE
    assert (
        "height:var(--pynix-project-header-height,43px)!important"
        in PROJECT_HEADER_SYNC_STYLE
    )
    assert (
        "min-height:var(--pynix-project-header-height,43px)!important"
        in PROJECT_HEADER_SYNC_STYLE
    )
    # Both layers have >=4 classes. A later rule of the same specificity
    # overrides the earlier !important value.
    assert selector.count(".") == 4
    full = apply_project_header_alignment(apply_pycharm_chrome(
        '<html><body class="workspace-mode"></body></html>', iconless=True
    ))
    assert full.index('id="pynix-project-header-alignment"') > full.index(
        'id="pynix-pycharm-chrome"'
    )


def test_project_header_height_does_not_change_when_rebuilding_tree():
    # RenderTree replaces only DOM nodes, the stylesheet is not replaced.
    from pynix_gui.ide_workspace_preview import workspace_bootstrap
    from pynix_gui.ide_workspace_session import WorkspaceSession
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "main.pnx").write_text("function main()\n", encoding="utf-8")
        js = workspace_bootstrap(WorkspaceSession(root))
        assert "heading.className='tree-title pynix-project-header';" in js
        assert "tree.replaceChildren();" in js
        assert ".pynix-project-header" in CHROME_STYLE
        assert ".tree-title.pynix-project-header" in PROJECT_HEADER_SYNC_STYLE

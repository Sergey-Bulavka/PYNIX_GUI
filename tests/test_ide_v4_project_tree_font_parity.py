"""Project file-name typography matches the actual 13px V4 code editor.

Only text should change: no changes to tree row height, file icons or
the Project toolbar and hover targets.
"""

import re
from pathlib import Path

from pynix_gui.ide_pycharm_chrome import CHROME_STYLE, apply_pycharm_chrome


def test_reference_editor_is_13px_in_edit_and_preview_modes():
    source=(Path(__file__).resolve().parents[1]/
            "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    # The active editable textarea/highlight layer and code preview agree.
    assert "font-size:13px!important;" in source
    assert "font:13px/23px ui-monospace" in source
    assert ".workspace-mode .pynix-editor-code .pynix-code-line" in source


def test_file_tree_names_and_path_match_editor_font_without_changing_row_geometry():
    marker="/* IDE V4 Project text size parity."
    assert marker in CHROME_STYLE
    layer=CHROME_STYLE.split(marker,1)[1]
    assert ".workspace-mode .tree .project-entry{" in layer
    assert ".workspace-mode .tree .project-entry .project-label," in layer
    assert ".workspace-mode .tree .project-entry .pynix-project-root-name," in layer
    assert ".workspace-mode .tree .project-entry .pynix-project-root-path{" in layer
    assert layer.count("font-size:13px!important;")==2
    assert "height:" not in layer
    assert "padding:" not in layer
    assert "width:" not in layer
    assert "svg" not in layer.lower()


def test_font_override_is_after_legacy_12px_rules_in_rendered_v4_document():
    html=apply_pycharm_chrome(
        '<html><head></head><body class="workspace-mode"></body></html>',
        iconless=True,
    )
    marker="IDE V4 Project text size parity."
    assert marker in html
    chrome=html[html.index('id="pynix-pycharm-chrome"'):]
    assert chrome.index(marker) > chrome.index(".workspace-mode .tree .project-root .pynix-project-root-path")
    # The highly specific root-path 12px rule must be superseded by an
    # equally specific later 13px !important declaration.
    selector=".workspace-mode .tree .project-entry .pynix-project-root-path"
    assert selector in chrome
    assert chrome.index(selector) > chrome.index(".workspace-mode .tree .project-root .pynix-project-root-path")


def test_existing_explorer_row_and_header_dimensions_remain_untouched():
    css=CHROME_STYLE
    assert ".workspace-mode .tree .tree-title.pynix-project-header{" in css
    assert "height:43px!important;min-height:43px!important;" in css
    font=css.split("/* IDE V4 Project text size parity.",1)[1]
    assert "project-header" not in font
    assert "project-chevron" not in font
    assert "project-glyph" not in font

"""Native IDE V4 toolbar stays in a single flow during continuous resizing.

Static regression guards for the original accidental overlap: the old
absolutely positioned 70% Run/Debug cluster and the 1160px position switch.
A macOS live resize still requires visual acceptance.
"""
from pathlib import Path

from pynix_gui.ide_pycharm_chrome import CHROME_SCRIPT, CHROME_STYLE, apply_pycharm_chrome


def test_toolbar_uses_one_continuous_flex_layout_at_all_window_widths():
    css=CHROME_STYLE
    begin=css.index("/* V4 live window-resize invariant:")
    layout=css[begin:]
    assert ".workspace-mode .workspace-toolbar{" in layout
    assert "display:flex!important;align-items:center!important;flex-wrap:nowrap!important" in layout
    assert ".workspace-mode .workspace-toolbar>.toolbar-spacer{" in layout
    assert "flex:1 1 0px!important;min-width:0!important" in layout
    for selector in (
        ".pynix-toolbar-identity{",
        ".pynix-pycharm-center{",
        ".pynix-pycharm-right{",
    ):
        assert selector in layout
    for declaration in (
        "position:relative!important;left:auto!important;top:auto!important;",
        "transform:none!important;flex:0 0 auto!important;",
        "min-width:0!important;margin:0!important",
        "position:relative!important;flex:0 1 auto!important;min-width:0!important;",
    ):
        assert declaration in layout
    assert layout.index("position:relative!important;left:auto!") > css[:begin].find(
        "position:absolute;left:70%"
    ) - begin
    # Only label lengths and gaps vary at CSS breakpoints; never positioning.
    for breakpoint in (1060,930):
        assert f"@media(max-width:{breakpoint}px)" in layout
    assert "position:static" not in layout
    assert "left:70%" not in layout
    assert "setTimeout" not in layout


def test_group_shrink_does_not_destroy_button_hitboxes_or_beta_information():
    layout=CHROME_STYLE.split("/* V4 live window-resize invariant:",1)[1]
    for constraint in (
        "min-width:31px!important;width:31px!important",
        "min-width:29px!important;width:29px!important",
        "flex:0 0 33px!important;min-width:33px!important;width:33px!important",
        "text-overflow:ellipsis!important",
        "content:attr(data-compact)",
        "font-size:0!important",
    ):
        assert constraint in layout, constraint
    assert "beta.dataset.compact='β · __IDE_VERSION__';" in CHROME_SCRIPT
    assert "beta.textContent='Beta Version · __IDE_VERSION__';" in CHROME_SCRIPT
    assert "right.append(search,settings,beta);" in CHROME_SCRIPT
    assert "toolbar.append(center,right);" in CHROME_SCRIPT
    assert "const left=document.createElement('div');" in CHROME_SCRIPT
    assert "left.append(project,branch);" in CHROME_SCRIPT


def test_default_and_icon_enabled_modes_use_the_same_geometry_rules():
    source='<html><body class="workspace-mode"><div class="workspace-toolbar"></div></body></html>'
    for iconless in (True,False):
        html=apply_pycharm_chrome(source,iconless=iconless)
        assert html.count('id="pynix-pycharm-chrome"')==1
        assert "V4 live window-resize invariant" in html
        assert "position:relative!important;left:auto!important;top:auto!important;" in html
        assert "beta.dataset.compact='β · 1.1.26-dev';" in html
    native=(Path(__file__).resolve().parents[1] /
            "examples/ide_native_v4.py").read_text(encoding="utf-8")
    assert "document = apply_pycharm_chrome(document, iconless=True)" in native
    assert "document = apply_pycharm_chrome(document)" in native
    assert "observer.observe(toolbar);" in native
    assert "window.addEventListener('resize', update);" in native

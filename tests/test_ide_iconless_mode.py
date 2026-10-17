"""Icon-free native shell contract: no icon painter, preserved real commands."""
from pathlib import Path

from pynix_gui.ide_iconless_mode import ICONLESS_STYLE, apply_iconless_mode
from pynix_gui.ide_edge_profile import apply_edge_profile, EDGE_PROFILE_SCRIPT
from pynix_gui.ide_pycharm_chrome import apply_pycharm_chrome, CHROME_SCRIPT


def test_iconless_document_style_is_reversible_and_idempotent():
    original = '<html><body class="workspace-mode">hello</body></html>'
    result = apply_iconless_mode(original)
    assert result != original
    assert result == apply_iconless_mode(result)
    assert '<body class="workspace-mode pynix-iconless">' in result
    assert result.count('id="pynix-iconless-style"') == 1
    assert "hello" in result
    assert apply_iconless_mode("ordinary text") == "ordinary text"


def test_iconless_css_removes_entire_icon_visual_system():
    for key in (
        ".workspace-mode svg", ".workspace-mode img",
        ".workspace-mode .project-glyph",
        ".workspace-mode .project-chevron",
        ".workspace-mode .pynix-tab-file-glyph",
        ".workspace-mode .file-mark",
        ".workspace-mode .pynix-project-dropdown-chevron",
        "display:none!important",
    ):
        assert key in ICONLESS_STYLE
    assert "pointer-events:none!important" not in ICONLESS_STYLE.split("/* Keep text-only")[0]


def test_sidebar_iconless_uses_labels_and_no_svg_payload():
    from pathlib import Path
    output = apply_edge_profile('<html><body class="workspace-mode"></body></html>',
                                directory=Path("/nonexistent-jetbrains-catalog"),
                                iconless=True)
    assert '__ICONLESS__' not in output
    assert "const iconless=true;" in output
    assert '"svg": null' in output
    assert "<svg" not in output
    assert "button.textContent=shortNames[entry.label]||entry.label" in EDGE_PROFILE_SCRIPT
    assert "if(!unavailable)button.addEventListener('click',()=>clickExisting(entry));" in EDGE_PROFILE_SCRIPT


def test_top_controls_use_text_instead_of_logo_svg():
    from pathlib import Path
    output = apply_pycharm_chrome(
        '<html><body class="workspace-mode"></body></html>',
        directory=Path("/nonexistent-jetbrains-catalog"), iconless=True
    )
    assert "const iconless=true;" in output
    assert "const icons={};" in output
    assert "<svg" not in output
    assert "else button.textContent=label;" in CHROME_SCRIPT
    assert "document.createTextNode('More')" in CHROME_SCRIPT
    assert "document.createTextNode('Fold')" in CHROME_SCRIPT


def test_native_ide_defaults_to_iconless_and_retains_opt_in_catalog():
    native = (Path(__file__).resolve().parents[1] /
              "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    assert 'parser.add_argument("--with-icons", action="store_true"' in native
    assert "if args.with_icons:" in native
    assert "document = apply_new_ui_icons(document)" in native
    assert "document = apply_edge_profile(document, iconless=True)" in native
    assert "document = apply_pycharm_chrome(document, iconless=True)" in native
    assert "document = apply_iconless_mode(document)" in native
    optin = native.index("if args.with_icons:")
    assert optin < native.index("document = apply_new_ui_icons(document)") 


def test_iconless_workspace_keeps_original_svg_for_left_top_more_only():
    assert '.pynix-tool-profile-popover[data-edge="left-top"]' in ICONLESS_STYLE
    assert ".pynix-more-item .pynix-menu-icon svg" in ICONLESS_STYLE
    assert "display:block!important" in ICONLESS_STYLE
    assert ".workspace-mode svg" in ICONLESS_STYLE

"""Checks for the new native macOS V4 approval surface.

No AppKit or WebKit imports take place when imported on Linux CI.
"""
from __future__ import annotations

import ast
from pathlib import Path

from examples import ide_native_v4 as app


def test_native_v4_source_parses():
    ast.parse(Path(app.__file__).read_text(encoding="utf-8"))


def test_native_v4_sources_approved_asset_preview():
    assert app.PREVIEW_PATH.name == "icon_direction_preview.html"
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    assert "GitHub Primer Octicons" in html
    assert "Lucide" in html
    assert "integrated-terminal" in html
    assert "SOURCE CONTROL" in html
    assert "git-actions-card" in html


def test_native_v4_window_lifecycle_and_local_assets():
    src = Path(app.__file__).read_text(encoding="utf-8")
    assert "applicationShouldTerminateAfterLastWindowClosed_" in src
    assert "loadHTMLString_baseURL_" in src
    assert '<body class="workspace-mode">' in src
    assert "WKWebView" in src
    assert "app.run()" in src


def test_native_v4_imports_portably():
    import sys
    if sys.platform != "darwin":
        assert "WebKit" not in sys.modules


def test_native_v4_workspace_resizes_instead_of_centering_gallery():
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    assert "body.workspace-mode" in html
    assert ".workspace-mode .ide{height:auto;min-height:0;flex:1;" in html
    assert ".workspace-mode .layout{display:block;max-width:none;" in html
    assert ".workspace-mode .tree{width:clamp(" in html
    assert ".workspace-mode .layout>.section{display:none}" in html


def test_v41_workspace_has_professional_panels_and_resizers():
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    for expected in ("workspace-toolbar", "editor-tabs", "right-tools",
                     "tree-resizer", "terminal-resizer", "--explorer-width",
                     "--terminal-height", "setPointerCapture",
                     "data-file=\"gui.pnx\"", "data-file=\"tooling.pnx\""):
        assert expected in html


def test_v41_resize_controls_are_keyboard_accessible():
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    assert 'aria-orientation="vertical"' in html
    assert 'aria-orientation="horizontal"' in html
    assert 'tabindex="0"' in html
    assert "ArrowRight" in html
    assert "ArrowUp" in html


def test_v41_gallery_stays_separate_from_workspace():
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    assert ".workspace-mode .layout>.section{display:none}" in html
    assert ".workspace-mode .editor-tabs{display:flex}" in html
    assert "One family" in html


def test_v41_right_rail_is_nested_inside_editor_workspace():
    from html.parser import HTMLParser

    class Hierarchy(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.ancestors = {}
        def handle_starttag(self, tag, attrs):
            if tag != "div":
                return
            cls = dict(attrs).get("class", "")
            for name in ("ide", "editor", "right-tools", "terminal-resizer", "integrated-terminal"):
                if name in cls.split():
                    self.ancestors[name] = list(self.stack)
            self.stack.append(cls)
        def handle_endtag(self, tag):
            if tag == "div" and self.stack:
                self.stack.pop()

    parser = Hierarchy()
    parser.feed(app.PREVIEW_PATH.read_text(encoding="utf-8"))
    assert "ide" in parser.ancestors["editor"]
    assert "ide" in parser.ancestors["right-tools"]
    assert "ide" not in parser.ancestors["terminal-resizer"]
    assert "ide" not in parser.ancestors["integrated-terminal"]


def test_native_window_accepts_first_mouse_click():
    source = Path(app.__file__).read_text(encoding="utf-8")
    assert "class FirstClickWebView(WebKit.WKWebView):" in source
    assert "def acceptsFirstMouse_(self, event):" in source
    assert "view = FirstClickWebView.alloc()" in source
    assert "window.makeFirstResponder_(view)" in source


def test_workspace_controls_use_single_click_events():
    source = app.PREVIEW_PATH.read_text(encoding="utf-8")
    assert "addEventListener('click'" in source
    assert "addEventListener('dblclick'" not in source


def test_default_launch_never_silently_uses_demo_tree():
    source = Path(app.__file__).read_text(encoding="utf-8")
    assert 'candidate = PREVIEW_PATH.resolve().parents[2] / "PYNIX"' in source
    assert 'project_path = args.project' in source
    assert 'raise SystemExit("No project selected.' in source
    assert 'session = WorkspaceSession(project_path)' in source


def test_v4_tab_close_available_on_hover_and_keyboard_focus():
    """Inactive tabs must offer a discoverable close control to mouse and keyboard users."""
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    assert ".pynix-editor-tab.active .pynix-editor-tab-close," in html
    assert ".pynix-editor-tab:hover .pynix-editor-tab-close," in html
    assert ".pynix-editor-tab:focus-within .pynix-editor-tab-close{" in html
    assert "visibility:visible;pointer-events:auto;" in html


def test_new_ui_precise_tab_title_and_close_geometry_are_scoped():
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    style = html.split("</style>", 1)[0]
    assert ".workspace-mode .editor-tabs .pynix-editor-tab .pynix-editor-tab-label{" in style
    assert ".workspace-mode .editor-tabs .pynix-editor-tab .pynix-editor-tab-close{" in style
    assert "flex:0 0 18px!important" in style
    assert ".pynix-editor-tab:is(.active,:hover,:focus-within) .pynix-editor-tab-close" in style
    assert "visibility:hidden!important;pointer-events:none!important" in style


def test_v52_workspace_geometry_keeps_adjustable_panel_sizes():
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    style = html.split("</style>", 1)[0]
    assert ".workspace-mode .layout{height:calc(100vh - 39px)!important}" in style
    assert "height:var(--terminal-height,235px)!important" in style
    assert "width:var(--explorer-width,220px)!important" in style
    assert ".workspace-mode .editor-tabs{height:35px!important" in style
    assert ".workspace-mode .bottom{height:22px!important" in style

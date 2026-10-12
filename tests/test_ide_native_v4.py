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

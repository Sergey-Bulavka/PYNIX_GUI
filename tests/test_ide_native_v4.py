"""Checks for the new native macOS V4 approval surface.

No AppKit or WebKit imports take place when imported on Linux CI.
"""
from __future__ import annotations

import ast
from pathlib import Path

from examples import ide_native_v4 as app


def _effective_css_rule(css: str, selector: str) -> str:
    """Merge same-selector CSS declarations in cascade order.

    Later rules only replace properties they actually specify. A final
    scrollbar-color declaration must not hide an earlier overflow setting.
    Within equal specificity, !important wins over non-important declarations.
    This helper checks only the scoped selectors used by our visual contracts;
    it is not a general-purpose CSS parser.
    """
    import re

    blocks = re.findall(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert blocks, f"missing visual selector: {selector}"
    properties: dict[str, str] = {}
    for block in blocks:
        for declaration in block.split(";"):
            name, separator, value = declaration.strip().partition(":")
            if not separator:
                continue
            name, value = name.strip(), value.strip()
            previous = properties.get(name)
            if previous is not None and previous.endswith("!important") and not value.endswith("!important"):
                continue
            properties[name] = value
    return ";".join(f"{name}:{value}" for name, value in properties.items())


def test_css_contract_merges_incremental_rules_by_property():
    css = (
        ".workspace-mode .tree{margin:0 5px 0 1px!important;"
        "overflow-y:auto!important}"
        ".workspace-mode .tree{scrollbar-width:auto!important}"
        ".workspace-mode .tree{margin:0!important}"
        ".workspace-mode .tree{overflow-y:hidden}"
    )
    properties = _effective_css_rule(css, ".workspace-mode .tree")
    assert "scrollbar-width:auto!important" in properties
    assert "margin:0!important" in properties
    assert "margin:0 5px 0 1px!important" not in properties
    assert "overflow-y:auto!important" in properties
    assert "overflow-y:hidden" not in properties



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


def test_native_v4_unifies_macos_titlebar_and_toolbar():
    native = Path(app.__file__).read_text(encoding="utf-8")
    css = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    assert "NSWindowStyleMaskFullSizeContentView" in native
    assert "setTitleVisibility_(AppKit.NSWindowTitleHidden)" in native
    assert "setTitlebarAppearsTransparent_(True)" in native
    assert "padding-left:86px!important" in css
    assert "height:calc(100vh - 44px)!important" in css


def test_v54_editor_gutter_stays_sticky_under_horizontal_scroll():
    style = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    assert ".workspace-mode .editor .code .source-line>.ln{" in style
    assert "position:sticky!important;left:0!important;z-index:5!important" in style
    assert "flex:0 0 64px!important;width:64px!important" in style
    assert ".workspace-mode .editor .code .source-line>.source-text{" in style
    assert "scrollbar-color:#585c64 transparent" in style


def test_v54_terminal_and_tool_rail_have_scoped_visual_contracts():
    style = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    assert ".workspace-mode .integrated-terminal{" in style
    assert ".workspace-mode .pynix-terminal-session-tab{" in style
    assert ".workspace-mode .right-tools{width:35px!important" in style
    assert ".workspace-mode .tree .project-entry.workspace-selected{" in style


def test_v55_window_drag_and_separate_editor_gutter_contract():
    native = Path(app.__file__).read_text(encoding="utf-8")
    style = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>",1)[0]
    assert "window.setMovableByWindowBackground_(False)" in native
    assert ".workspace-mode .pynix-editor-viewport{" in style
    assert ".workspace-mode .pynix-editor-gutter{" in style
    assert ".workspace-mode .pynix-editor-scroll{" in style
    assert ".workspace-mode .ide>.rail{" in style
    assert ".workspace-mode .integrated-terminal{margin-left:43px!important}" in style


def test_v56_native_window_drag_uses_appkit_background():
    source = Path(app.__file__).read_text(encoding="utf-8")
    assert "def mouseDownCanMoveWindow(self):" not in source
    assert "window.setMovableByWindowBackground_(False)" in source
    assert "class TitlebarDragArea" not in source
    assert "def hitTest_(self, point):" not in source


def test_v56_outer_editor_scroll_is_disabled_and_terminal_right_edge_aligned():
    style = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    assert "overflow-x:clip!important;overflow-y:clip!important" in style
    assert ".workspace-mode .integrated-terminal{margin-right:4px!important}" in style


def test_editable_editor_gutter_occludes_scrolling_highlight_layer():
    style = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    assert ".workspace-mode .pynix-edit-layer .pynix-edit-gutter{" in style
    assert "z-index:12!important;background:#1e1f22!important" in style
    assert ".workspace-mode .pynix-edit-layer .pynix-source-input{" in style
    assert "z-index:3!important;left:0!important;background:transparent!important" in style


def test_v58_side_rails_and_project_outline_share_shell_edges():
    style=app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>",1)[0]
    assert ".workspace-mode .ide>.rail{" in style
    assert "top:0!important;bottom:22px!important" in style
    assert "border:1px solid #34363c!important" in style
    assert "margin-left:43px!important;margin-right:39px!important" in style
    assert ".workspace-mode .right-tools{" in style


def test_native_host_no_longer_overrides_objc_mouse_dispatch():
    source = Path(app.__file__).read_text(encoding="utf-8")
    assert "class FirstClickWebView(WebKit.WKWebView):" in source
    assert "class ToolbarDragView(AppKit.NSView):" in source
    webview = source.split("class FirstClickWebView(WebKit.WKWebView):", 1)[1].split(
        "class ToolbarDragView(AppKit.NSView):", 1
    )[0]
    drag_view = source.split("class ToolbarDragView(AppKit.NSView):", 1)[1].split(
        "    app = AppKit.NSApplication.sharedApplication()", 1
    )[0]
    assert "def acceptsFirstMouse_(self, event):" in webview
    assert "def mouseDown_(self, event):" not in webview
    assert "def mouseDownCanMoveWindow(self):" not in webview
    assert "def mouseDown_(self, event):" in drag_view
    assert "self.window().performWindowDragWithEvent_(event)" in drag_view


def test_v515_rounded_surfaces_integrated_tabs_and_30px_status():
    # These rules are in the LAST chrome contract, not obsolete V5.x blocks.
    css = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    marker = "/* V5.15: measured three-surface New UI shell."
    assert css.count(marker) == 1
    final = css.split(marker, 1)[1]
    assert "/* V5.14 structural chrome:" not in final
    assert ".workspace-mode .ide{" in final
    assert "background:#2b2d30!important;padding-left:40px!important;padding-right:35px!important" in final
    assert "margin:0 5px 0 1px!important" in final
    assert "border:0!important;border-radius:9px!important" in final
    assert "margin:0!important" in final
    assert "height:43px!important;min-height:43px!important;max-height:43px!important" in final
    assert "align-items:flex-start!important;padding:5px 6px 9px!important" in final
    assert "height:29px!important;min-height:29px!important;max-height:29px!important" in final
    assert "border:0!important;border-radius:6px!important" in final
    assert "height:var(--terminal-height,315px)!important" in final
    assert "height:30px!important;min-height:30px!important;max-height:30px!important" in final
    assert "bottom:30px!important" in final
    # Gutter occlusion and independent editor scroll must survive chrome changes.
    assert "z-index:12!important;background:#1e1f22!important" in css
    assert ".workspace-mode .pynix-editor-scroll{" in css


def test_visual_diagnostics_are_read_only_and_include_computed_geometry():
    html = app.PREVIEW_PATH.read_text(encoding="utf-8")
    assert "window.pynixVisualMetrics=snapshot;" in html
    assert "getBoundingClientRect()" in html
    assert "getComputedStyle(el)" in html
    assert "canScrollVertically:el.scrollHeight>el.clientHeight+1" in html
    assert "canScrollHorizontally:el.scrollWidth>el.clientWidth+1" in html
    assert "['editor scroll','.pynix-editor-scroll']" in html
    assert "event.ctrlKey&&event.altKey&&event.shiftKey&&event.code==='KeyM'" in html
    assert "report.readOnly=true" in html
    assert "['terminal','.integrated-terminal']" in html
    assert "['active tab','.editor-tabs .pynix-editor-tab.active']" in html


def test_v516_no_panel_strokes_and_wider_project_editor_gap():
    # Verify the last scoped rule set, not historical visual experiments.
    css = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    final = css.split("/* V5.15: measured three-surface New UI shell.", 1)[1]

    def rule(selector):
        return _effective_css_rule(final, selector)

    tree = rule(".workspace-mode .tree")
    splitter = rule(".workspace-mode .tree-resizer")
    assert "margin:0 5px 0 1px!important" in tree
    assert "width:6px!important" in splitter
    assert "background:transparent!important" in splitter
    assert "border:0!important" in splitter
    assert "border:0!important" in rule(".workspace-mode .terminal-resizer")
    assert "background:transparent!important" in rule(".workspace-mode .terminal-resizer")
    assert "border-bottom:0!important" in rule(".workspace-mode .workspace-toolbar")
    assert "border-bottom:0!important" in rule(".workspace-mode .terminal-tabs")
    assert "border-top:0!important" in rule(".workspace-mode .bottom")
    assert "border-right:0!important" in rule(".workspace-mode .ide>.rail")
    assert "border-left:0!important" in rule(".workspace-mode .right-tools")


def test_v517_tab_divider_real_gutter_and_centered_project_chevron():
    css = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    final = css.split("/* V5.15: measured three-surface New UI shell.", 1)[1]

    def last_rule(selector):
        return _effective_css_rule(final, selector)

    tabs = last_rule(".workspace-mode .editor-tabs")
    assert "height:43px!important" in tabs
    assert "padding:5px 6px 9px!important" in tabs
    assert "border-bottom:1px solid #34363c!important" in tabs
    gutter = last_rule(".workspace-mode .pynix-edit-layer .pynix-edit-gutter")
    assert "text-align:left!important" in gutter
    assert "padding:15px 0 15px 8px!important" in gutter
    readonly_gutter = last_rule(".workspace-mode .pynix-editor-gutter .pynix-gutter-line")
    assert "text-align:left!important" in readonly_gutter
    assert "align-items:center!important" in last_rule(
        ".workspace-mode .workspace-toolbar .current-branch")
    assert "width:14px!important;height:14px!important" in last_rule(
        ".workspace-mode .workspace-toolbar .pynix-project-dropdown-chevron")


def test_v518_scroll_targets_are_real_independent_overflow_hosts():
    import re
    css=app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>",1)[0]
    marker="/* V5.18: explicit, independently scrollable Project and Editor surfaces."
    assert css.count(marker)==1
    final=css.split(marker,1)[1]

    def rule(selector):
        return _effective_css_rule(final, selector)

    tree=rule(".workspace-mode .tree")
    assert "overflow-y:auto!important" in tree
    assert "overflow-x:hidden!important" in tree
    layer=rule(".workspace-mode .pynix-edit-layer")
    assert "flex:1 1 auto!important" in layer
    assert "min-height:0!important" in layer
    textarea=rule(".workspace-mode .pynix-edit-layer .pynix-source-input")
    assert "overflow-x:auto!important" in textarea
    assert "overflow-y:auto!important" in textarea
    assert "scrollbar-width:auto!important" in textarea
    readonly=rule(".workspace-mode .pynix-editor-scroll")
    assert "height:100%!important" in readonly
    assert "overflow:auto!important" in readonly
    assert "left:64px!important" in final
    assert "width:calc(100% - 64px)!important" in final
    assert "padding-left:13px!important" in final

def test_v518_native_webview_does_not_capture_scrollbar_mouse_down_as_window_drag():
    native=Path(app.__file__).read_text(encoding="utf-8")
    assert "window.setMovableByWindowBackground_(False)" in native
    assert "def mouseDownCanMoveWindow(self):" not in native


def test_v519_toolbar_drag_frame_respects_only_blank_header():
    from examples.ide_native_v4 import toolbar_drag_frame

    area = {"x": 350, "y": 10, "width": 420, "height": 26}
    assert toolbar_drag_frame(1500, 950, area) == (350, 914, 420, 26)
    # An overlay whose TOP edge is 10 CSS points from the window top
    # must stay there through successive height-only resizes.
    assert toolbar_drag_frame(1500, 1100, area) == (350, 1064, 420, 26)
    assert toolbar_drag_frame(1500, 800, area) == (350, 764, 420, 26)

    # No region in Project, Editor, scrollbars, macOS top border or corner
    # can ever be interpreted as a dragging surface.
    assert toolbar_drag_frame(
        1500, 950, {"x": 30, "y": 10, "width": 420, "height": 26}) is None
    assert toolbar_drag_frame(
        1500, 950, {"x": 350, "y": 60, "width": 420, "height": 26}) is None
    assert toolbar_drag_frame(
        1500, 950, {"x": 350, "y": 3, "width": 420, "height": 26}) is None
    assert toolbar_drag_frame(
        1500, 950, {"x": 350, "y": 10, "width": 420, "height": 38}) is None
    assert toolbar_drag_frame(
        1500, 950, {"x": 350, "y": 10, "width": 11, "height": 26}) is None
    assert toolbar_drag_frame(
        760, 520, {"x": 700, "y": 10, "width": 10, "height": 26}) is None
    assert toolbar_drag_frame(
        1500, 950, {"x": 350, "y": 10, "width": float("nan"), "height": 26}) is None
    assert toolbar_drag_frame(1500, 950, {}) is None
    # The last 18px are reserved for the native window resize corner.
    assert toolbar_drag_frame(
        760, 520, {"x": 700, "y": 10, "width": 500, "height": 26}) == (700, 484, 42, 26)


def test_v519_native_free_drag_strips_are_above_webview_and_exclude_widgets():
    source=Path(app.__file__).read_text(encoding="utf-8")
    assert "class ToolbarDragView(AppKit.NSView):" in source
    assert "self.window().performWindowDragWithEvent_(event)" in source
    assert "content_view = window.contentView()" in source
    assert "content_view.addSubview_(view)" in source
    assert "toolbar_drag_areas = []" in source
    assert "content_view.addSubview_(drag_view)" in source
    assert source.index("content_view.addSubview_(view)") < source.index(
        "content_view.addSubview_(drag_view)")
    assert "window.setContentView_(container)" not in source
    assert "AppKit.NSWindowStyleMaskResizable" in source
    assert "drag_view.setHidden_(True)" in source
    assert "drag_view.setHidden_(False)" in source
    assert 'toolbar_drag_handler, "pynixToolbarDragRegion"' in source
    assert "window.setMovableByWindowBackground_(False)" in source

def test_v519_toolbar_drag_regions_cover_every_free_gap_not_buttons():
    source=Path(app.__file__).read_text(encoding="utf-8")
    script=app.TOOLBAR_DRAG_SCRIPT
    assert "toolbar.getBoundingClientRect()" in script
    assert "toolbar.querySelectorAll(selector)" in script
    assert "const minX=Math.max(86,bar.left+86)" in script
    assert "rect.left-5" in script and "rect.right+5" in script
    assert "blocked.sort((a,b)=>a[0]-b[0])" in script
    assert "if(end-start>=12)areas.push({" in script
    assert "pynixToolbarDragRegion?.postMessage(areas)" in script
    assert "new ResizeObserver(update)" in script
    assert "new MutationObserver(" in script
    assert "window.addEventListener('resize',update)" in script
    assert 'document.replace("</body>", TOOLBAR_DRAG_SCRIPT + "</body>", 1)' in source

def test_v520_native_resize_retains_webview_and_safe_drag_overlays():
    source=Path(app.__file__).read_text(encoding="utf-8")
    assert "content_view = window.contentView()" in source
    assert "view = FirstClickWebView.alloc().initWithFrame_(content_view.bounds())" in source
    assert "view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)" in source
    assert "content_view.addSubview_(view)" in source
    assert "content_view.addSubview_(drag_view)" in source
    assert "bounds = content_view.bounds().size" in source
    assert "toolbar_drag_frame(bounds.width, bounds.height, area)" in source
    assert "window.setContentView_(container)" not in source
    assert "AppKit.NSWindowStyleMaskResizable" in source
    assert "window.setMinSize_(AppKit.NSMakeSize(760, 520))" in source
    assert "self.window().performWindowDragWithEvent_(event)" in source
    assert "window.setMovableByWindowBackground_(False)" in source

def test_v521_drag_gaps_follow_resizes_and_never_cover_edges():
    source=Path(app.__file__).read_text(encoding="utf-8")
    script=app.TOOLBAR_DRAG_SCRIPT
    assert "drag_view.setAutoresizingMask_(AppKit.NSViewMinYMargin)" in source
    assert "drag_view.setFrame_(AppKit.NSMakeRect(*frame))" in source
    assert "drag_view.setHidden_(False)" in source
    assert "window.setMovableByWindowBackground_(False)" in source
    assert "AppKit.NSWindowStyleMaskResizable" in source
    assert "window.addEventListener('resize',update)" in script
    assert "observer.observe(toolbar)" in script
    assert "width:end-start" in script
    assert "height:Math.min(24,bar.height-18)" in script
    assert "bounds_width - x - 18" in source

def test_v522_no_fixed_drag_handle_can_intercept_project_controls():
    source=Path(app.__file__).read_text(encoding="utf-8")
    assert "title_drag_area = ToolbarDragView.alloc()" not in source
    assert 'drag_geometry = {"areas": []}' in source
    assert "for _ in range(20):" in source
    assert 'drag_geometry["areas"] = payload[:20] if isinstance(payload, list) else []' in source

def test_v522_native_resize_delegate_repositions_dynamic_drag_strips():
    source=Path(app.__file__).read_text(encoding="utf-8")
    assert "def windowDidResize_(self, notification):" in source
    assert 'update = drag_resize_callback["update"]' in source
    assert "if update is not None:" in source
    assert "window.setDelegate_(delegate)" in source
    assert 'drag_resize_callback["update"] = refresh_native_drag_areas' in source
    assert "refresh_native_drag_areas()" in source
    assert "drag_view.setAutoresizingMask_(AppKit.NSViewMinYMargin)" in source
    assert "content_view.addSubview_(drag_view)" in source
    assert 'areas = drag_geometry["areas"]' in source
    assert "toolbar_drag_frame(bounds.width, bounds.height, area)" in source
    assert 'drag_geometry["areas"] = payload[:20] if isinstance(payload, list) else []' in source
    assert "window.setMovableByWindowBackground_(False)" in source
    assert "self.window().performWindowDragWithEvent_(event)" in source
    assert "AppKit.NSWindowStyleMaskResizable" in source
    assert "window.setContentView_(container)" not in source

def test_v523_corner_resize_frame_is_independent_of_webkit_and_window_size():
    from examples.ide_native_v4 import corner_resize_geometry

    assert corner_resize_geometry(760, 520) == (736.0, 2.0, 22.0, 22.0)
    assert corner_resize_geometry(1500, 950) == (1476.0, 2.0, 22.0, 22.0)
    assert corner_resize_geometry(2400, 1400) == (2376.0, 2.0, 22.0, 22.0)


def test_v523_corner_resize_tracks_screen_pointer_and_keeps_top_left_anchor():
    from examples.ide_native_v4 import resized_window_frame

    initial = (100, 100, 1500, 950)
    pointer = (1600, 100)
    assert resized_window_frame(initial, pointer, (1800, 0)) == (
        100.0, 0.0, 1700.0, 1050.0
    )
    assert resized_window_frame(initial, pointer, (1400, 200)) == (
        100.0, 200.0, 1300.0, 850.0
    )
    # The same geometry applies across startup sizes, including wide windows.
    assert resized_window_frame((0, 300, 2400, 1400), (2400, 300), (2600, 200)) == (
        0.0, 200.0, 2600.0, 1500.0
    )
    # Clamping preserves the top-left corner rather than moving the whole IDE.
    assert resized_window_frame(initial, pointer, (0, 2000)) == (
        100.0, 530.0, 760.0, 520.0
    )
    assert resized_window_frame(initial, pointer, (float("nan"), 0)) is None


def test_v523_native_corner_grip_stays_responsive_through_relaunch_and_resize():
    source = Path(app.__file__).read_text(encoding="utf-8")
    assert "class CornerResizeView(AppKit.NSView):" in source
    assert "def mouseDown_(self, event):" in source
    assert "def mouseDragged_(self, event):" in source
    assert "def mouseUp_(self, event):" in source
    assert "AppKit.NSEvent.mouseLocation()" in source
    assert "self.window().setFrame_display_(AppKit.NSMakeRect(*frame), True)" in source
    assert "resized_window_frame(" in source
    assert "corner_resize_geometry(" in source
    assert "content_view.addSubview_(corner_resize)" in source
    assert "AppKit.NSViewMinXMargin | AppKit.NSViewMaxYMargin" in source
    assert "AppKit.NSWindowStyleMaskResizable" in source
    assert "window.setMovableByWindowBackground_(False)" in source
    assert "content_view.addSubview_(view)" in source
    assert "content_view.addSubview_(drag_view)" in source
    assert "title_drag_area = ToolbarDragView.alloc()" not in source


def test_v524_line_numbers_share_left_edge_without_changing_scroll_geometry():
    css = app.PREVIEW_PATH.read_text(encoding="utf-8").split("</style>", 1)[0]
    marker = "/* V5.24: true left-edge line numbers"
    assert css.count(marker) == 1
    final = css.split(marker, 1)[1]
    editable = _effective_css_rule(final, ".workspace-mode .pynix-edit-layer .pynix-edit-gutter")
    readonly = _effective_css_rule(final, ".workspace-mode .pynix-editor-gutter .pynix-gutter-line")
    fold = _effective_css_rule(final, ".workspace-mode .pynix-editor-gutter .pynix-gutter-fold-marker")
    assert "text-align:left!important" in editable
    assert "padding:15px 0 15px 8px!important" in editable
    assert "text-align:left!important" in readonly
    assert "padding:0 0 0 8px!important" in readonly
    assert "position:absolute" in fold
    assert "right:9px" in fold
    assert "pointer-events:none" in fold
    # The gutter is still a fixed independent pane; code scroll is unaffected.
    assert "grid-template-columns:62px minmax(0,1fr)" in css
    assert "width:64px!important" in css
    assert "overflow-x:auto!important;overflow-y:auto!important" in css

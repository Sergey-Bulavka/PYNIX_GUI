# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Icon-free native IDE surface.

This is a presentation contract: controls, routes, tree expansion, editor
content and keyboard shortcuts are untouched. The licensed icon library is
preserved but is not activated in icon-free native sessions.
"""
from __future__ import annotations

ICONLESS_STYLE = """<style id="pynix-iconless-style">
/* SVG rendering-quality contract for the entire native IDE.
   Keep vectors at their authored CSS sizes on the WKWebView backing surface;
   request antialiased curves/diagonals, not the aliased 'crispEdges' mode.
   Never rasterize SVGs into an upscaled PNG or enlarge the 20px tool glyph. */
.workspace-mode svg,
.workspace-mode svg path,
.workspace-mode svg circle,
.workspace-mode svg rect,
.workspace-mode svg line,
.workspace-mode svg polyline,
.workspace-mode svg polygon {
 shape-rendering:geometricPrecision!important;
 image-rendering:auto!important;
}
.workspace-mode.pynix-iconless .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool>svg,
.workspace-mode.pynix-iconless .pynix-extra-tools[data-edge="left-bottom"] .pynix-extra-tool>svg,
.workspace-mode.pynix-iconless .pynix-extra-tools[data-edge="right-top"] .pynix-extra-tool>svg{
 width:20px!important;height:20px!important;
 max-width:20px!important;max-height:20px!important;
 transform:none!important;
}
/* Hide legacy pictograms; restore only user-selected top/bottom left rails. */
.workspace-mode svg,
.workspace-mode img,
.workspace-mode .pynix-jetbrains-icon,
.workspace-mode .project-glyph,
.workspace-mode .pynix-tab-file-glyph,
.workspace-mode .file-mark,
.workspace-mode .project-chevron,
.workspace-mode .pynix-project-dropdown-chevron,
.workspace-mode .pynix-terminal-session-icon,
.workspace-mode .pynix-icon,
.workspace-mode .pynix-debug-panel-toolbar svg {
 display:none!important;
}
/* Packages is a functional native tool window, not a legacy pictogram.
   Its three controlled SVG glyphs must survive the global iconless
   "svg {display:none!important}" rule, just like Project tree glyphs.
   Keep this opt-in narrow so the rest of iconless chrome stays unchanged. */
.workspace-mode.pynix-iconless .pynix-packages-pane .pynix-packages-search-icon>svg,
.workspace-mode.pynix-iconless .pynix-packages-pane .pynix-packages-pypi>svg,
.workspace-mode.pynix-iconless .pynix-packages-pane .pynix-packages-cube>svg,
.workspace-mode.pynix-iconless .pynix-packages-pane .pynix-packages-update>svg {
 display:block!important;
 visibility:visible!important;
 opacity:1!important;
 flex:none!important;
}
.workspace-mode.pynix-iconless .pynix-packages-pane .pynix-packages-search-icon>svg,
.workspace-mode.pynix-iconless .pynix-packages-pane .pynix-packages-cube>svg {
 width:16px!important;height:16px!important;
 min-width:16px!important;min-height:16px!important;
}
.workspace-mode.pynix-iconless .pynix-packages-pane .pynix-packages-pypi>svg,
.workspace-mode.pynix-iconless .pynix-packages-pane .pynix-packages-update>svg {
 width:20px!important;height:20px!important;
 min-width:20px!important;min-height:20px!important;
}
/* Services buttons and service-type badges are real controls, not the legacy
   icon placeholders suppressed by the global native iconless rule.
   Restore only their explicitly owned SVGs; never unhide unrelated chrome. */
.workspace-mode.pynix-iconless .pynix-services-pane .pynix-services-header button>svg,
.workspace-mode.pynix-iconless .pynix-services-pane .pynix-services-toolbar>button>svg,
.workspace-mode.pynix-iconless .pynix-services-pane .pynix-services-item-icon>svg,
.workspace-mode.pynix-iconless .pynix-services-options-menu .pynix-services-option-mark>svg,
.workspace-mode.pynix-iconless .pynix-services-options-menu .pynix-services-option-arrow{
 display:block!important;
 visibility:visible!important;
 opacity:1!important;
 width:16px!important;height:16px!important;
 min-width:16px!important;min-height:16px!important;
 max-width:16px!important;max-height:16px!important;
 flex:0 0 16px!important;
 transform:none!important;
}
/* Options is portaled to body; restore original JetBrains 16x16 SVG sizes
   there as well, without exposing unrelated icons hidden by this theme. */
.workspace-mode.pynix-iconless .pynix-services-options-menu .pynix-services-option-mark>svg,
.workspace-mode.pynix-iconless .pynix-services-options-menu .pynix-services-option-arrow{
 display:block!important;visibility:visible!important;opacity:1!important;
 width:16px!important;height:16px!important;
 min-width:16px!important;min-height:16px!important;
 max-width:16px!important;max-height:16px!important;
 flex:0 0 16px!important;transform:none!important
}
/* Only the perimeter groups and two native project/Git buttons use icons.
   Other visual rails, tree badges and editor icons stay hidden. */
.workspace-mode.pynix-iconless
.pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool svg,
.workspace-mode.pynix-iconless
.pynix-extra-tools[data-edge="left-top"] .pynix-tool-profile-more svg,
.workspace-mode.pynix-iconless
.pynix-tool-profile-popover[data-edge="left-top"] .pynix-more-item .pynix-menu-icon svg,
.workspace-mode.pynix-iconless
.pynix-extra-tools[data-edge="left-bottom"] .pynix-extra-tool svg,
.workspace-mode.pynix-iconless
.pynix-extra-tools[data-edge="right-top"] .pynix-extra-tool svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-toolbar-project>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-toolbar-branch>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-current-config>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center>.pynix-run-action>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center>.pynix-tools-menu>summary>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center .pynix-run-with-params>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-right .pynix-ide-search>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-right .pynix-ide-settings>svg,
.workspace-mode.pynix-iconless .tree .pynix-project-header .pynix-project-quick-button>svg,
.workspace-mode.pynix-iconless .tree .pynix-project-header .pynix-project-header-button>svg{
 display:block!important;
}
/* The restored PyCharm Run/Debug SVGs use the verified JetBrains source
   palette. This selector only allows them to render; it does not change
   or recolor the source files. */
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center>.pynix-run-action>svg,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary>svg{
 width:19px!important;height:19px!important;max-width:19px!important;
 max-height:19px!important;transform:none!important;
}
/* The old shell also painted the PY badge, Run triangle and Debug bug
   through CSS pseudo-elements and data-URI backgrounds. They are icons too. */
.workspace-mode .workspace-toolbar>strong::before,
.workspace-mode .workspace-toolbar .pynix-run-action::before,
.workspace-mode .workspace-toolbar .pynix-debug-primary::before,
.workspace-mode .pynix-debug-primary::after {
 content:none!important;display:none!important;
 background-image:none!important;
}
.workspace-mode .workspace-toolbar .pynix-run-action,
.workspace-mode .workspace-toolbar .pynix-debug-primary {
 background-image:none!important;
}
/* Keep text-only controls readable and keyboard-operable. */
.workspace-mode .pynix-extra-tool,
.workspace-mode .pynix-pycharm-icon-button,
.workspace-mode .pynix-project-quick-button,
.workspace-mode .pynix-project-header-button,
.workspace-mode .pynix-tool-profile-more {
 font-family:system-ui,-apple-system,sans-serif!important;
 font-size:10px!important;font-weight:500!important;
 letter-spacing:0!important;line-height:1.1!important;
 text-transform:none!important;
}
.workspace-mode .ide>.rail,.workspace-mode .right-tools{overflow-x:hidden!important}
.workspace-mode .ide>.rail .pynix-extra-tool,
.workspace-mode .right-tools .pynix-extra-tool{
 font-size:9px!important;white-space:normal!important;
 word-break:normal!important;text-align:center!important;
 padding:2px!important;min-width:35px!important;
}
.workspace-mode .pynix-pycharm-icon-button{
 font-size:11px!important;width:auto!important;min-width:48px!important;
 padding:4px 6px!important;
}
.workspace-mode .pynix-project-quick-button{
 width:auto!important;min-width:26px!important;padding:3px 5px!important;
}
.workspace-mode .pynix-project-header-button{
 width:auto!important;min-width:44px!important;
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-action,
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary {
 font-size:11px!important;width:auto!important;min-width:43px!important;
 padding:4px 6px!important;
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-tools-menu>summary {
 font-size:11px!important;width:auto!important;
 padding:0 6px!important;
}
.workspace-mode .pynix-project-header-actions{gap:2px!important}
.workspace-mode .pynix-project-header-actions .pynix-project-quick-button{
 font-size:9px!important;
}
.workspace-mode .pynix-project-header:hover .pynix-project-header-actions,
.workspace-mode .pynix-project-header:focus-within .pynix-project-header-actions {
 opacity:1!important;pointer-events:auto!important
}
.workspace-mode .pynix-project-more-menu>summary{
 display:flex!important;align-items:center!important;justify-content:center!important;
 font-size:10px!important;
}
.workspace-mode .pynix-editor-tab-label{gap:0!important}
.workspace-mode .pynix-editor-tab .pynix-tab-file-glyph{display:none!important}
/* Project Explorer is not iconless: file extensions and folder disclosure
   must match the PyCharm tree in the normal, default IDE startup mode.
   Other old/iconless surfaces stay unchanged. */
.workspace-mode.pynix-iconless .tree .project-glyph{
 display:inline-flex!important;align-items:center!important;
 justify-content:center!important;width:16px!important;height:16px!important;
 min-width:16px!important;flex:0 0 16px!important;
}
.workspace-mode.pynix-iconless .tree .project-chevron{
 display:inline-flex!important;align-items:center!important;
 justify-content:center!important;width:14px!important;min-width:14px!important;
}
.workspace-mode.pynix-iconless .tree .project-glyph>svg,
.workspace-mode.pynix-iconless .tree .project-chevron>svg{
 display:block!important;width:16px!important;height:16px!important;
 max-width:16px!important;max-height:16px!important;
}
.workspace-mode.pynix-iconless .tree .project-chevron>svg{
 width:13px!important;height:13px!important;
}
.workspace-mode.pynix-iconless .tree .project-glyph>.file-mark{
 display:inline-flex!important;
}
.workspace-mode.pynix-iconless .tree .project-entry{gap:4px!important}
.workspace-mode .tree .project-entry{gap:2px!important}
.workspace-mode .pynix-tool-profile-more{font-size:10px!important}
.workspace-mode .pynix-status-breadcrumb::before{content:''!important}
</style>"""


def apply_iconless_mode(document: str) -> str:
    """Add the native no-icon contract once; do not alter application handlers."""
    if "</body>" not in document or 'id="pynix-iconless-style"' in document:
        return document
    return document.replace(
        "<body class=\"workspace-mode\">",
        '<body class="workspace-mode pynix-iconless">',
        1,
    ).replace("</body>", ICONLESS_STYLE + "</body>", 1)

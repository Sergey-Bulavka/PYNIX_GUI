# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Icon-free native IDE surface.

This is a presentation contract: controls, routes, tree expansion, editor
content and keyboard shortcuts are untouched. The licensed icon library is
preserved but is not activated in icon-free native sessions.
"""
from __future__ import annotations

ICONLESS_STYLE = """<style id="pynix-iconless-style">
/* No pictograms or file-type badges anywhere in the native IDE. */
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
/* The user explicitly restored icons for this one PyCharm-matched
   group only. No other SVG can escape the global iconless contract. */
.workspace-mode.pynix-iconless
.pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool svg{
 display:block!important;
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

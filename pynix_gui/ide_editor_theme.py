# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""V4 editor-specific JetBrains New UI (Darcula) inspired palette.

CSS-only layer: no editor geometry, selection, caret or source ownership changes.
"""

EDITOR_THEME_STYLE = """<style id="pynix-v4-editor-darcula">
/* Matching the subdued neutral typography seen in the PyCharm reference. */
.workspace-mode .tree .project-entry .project-label{
 color:#adafb6!important;font-weight:400!important;
}
.workspace-mode .tree .project-entry.project-root .project-label{
 color:#c7c9ce!important;font-weight:600!important;
}
.workspace-mode .tree .project-entry.workspace-selected .project-label{
 color:#c7c9cf!important;
}
.workspace-mode .pynix-editor-tab .pynix-editor-tab-label{
 color:#aeb0b7!important;font-weight:400!important;
}
.workspace-mode .pynix-editor-tab.active .pynix-editor-tab-label{
 color:#c9cbd1!important;font-weight:500!important;
}
/* Match PyCharm's quieter source text without disturbing the transparent
   textarea, caret alignment, gutter widths, scroll offsets or selections. */
.workspace-mode .pynix-edit-layer .pynix-edit-highlight{
 color:#bcbec4!important;
}
.workspace-mode .pynix-edit-plain,
.workspace-mode .pynix-edit-python-plain{color:#bcbec4!important}
.workspace-mode .pynix-edit-python-comment,
.workspace-mode .pynix-edit-comment{color:#7a7e85!important}
.workspace-mode .pynix-edit-python-keyword{color:#cf8e6d!important}
.workspace-mode .pynix-edit-python-string{color:#6aab73!important}
.workspace-mode .pynix-edit-python-number{color:#2aacb8!important}
.workspace-mode .pynix-edit-python-constant{color:#cf8e6d!important}
.workspace-mode .pynix-edit-python-decorator{color:#b3ae60!important}
.workspace-mode .pynix-edit-python-definition,
.workspace-mode .pynix-edit-python-class{color:#56a8f5!important}
.workspace-mode .pynix-edit-python-call{color:#a8bde1!important}
.workspace-mode .pynix-edit-python-builtin{color:#c6a8d6!important}
/* PYNIX has its own syntax, with the same reduced-intensity visual hierarchy.
   Language identity and highlighting categories are separate from Python. */
.workspace-mode .pynix-edit-keyword{color:#cf8e6d!important}
.workspace-mode .pynix-edit-definition{color:#56a8f5!important}
.workspace-mode .pynix-edit-string{color:#6aab73!important}
.workspace-mode .pynix-edit-number{color:#2aacb8!important}
.workspace-mode .pynix-edit-constant{color:#cf8e6d!important}
.workspace-mode .pynix-edit-type{color:#a8c1da!important}
.workspace-mode .pynix-edit-call{color:#a8bde1!important}
.workspace-mode .pynix-edit-builtin{color:#c6a8d6!important}
/* The read-only PYNIX preview uses Python-produced tokens, not the live
   textarea layer. Keep both views visually consistent. */
.workspace-mode .pnx-token.pnx-plain{color:#bcbec4!important}
.workspace-mode .pnx-token.pnx-keyword{color:#cf8e6d!important}
.workspace-mode .pnx-token.pnx-string{color:#6aab73!important}
.workspace-mode .pnx-token.pnx-number{color:#2aacb8!important}
.workspace-mode .pnx-token.pnx-comment{color:#7a7e85!important}
.workspace-mode .editor .code .source-text{color:#bcbec4!important}
</style>"""


def apply_editor_darcula(document: str) -> str:
    """Add subdued source/tree palette after existing V4 presentation rules."""
    if "</body>" not in document or 'id="pynix-v4-editor-darcula"' in document:
        return document
    return document.replace("</body>", EDITOR_THEME_STYLE + "</body>", 1)

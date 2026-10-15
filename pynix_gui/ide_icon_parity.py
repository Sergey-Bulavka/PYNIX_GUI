# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Activate licensed JetBrains New UI icons for existing PYNIX IDE controls.

This bridge replaces glyphs in place. It never changes buttons, handlers,
hit areas, focus semantics or window dragging. Missing icons retain the
previous PYNIX SVG so partial/full icon catalogs are both supported.
"""
from __future__ import annotations

import json
from pathlib import Path

from .ide_jetbrains_icons import JetBrainsIconCatalog

BUNDLED_ICONS = Path(__file__).parent / "assets" / "jetbrains_new_ui"

# The current V4 workspace rail has fixed semantic positions; future native
# UI controls should declare semantic data-pynix-icon attributes directly.
# Do not add icons for tools that do not yet have an actual control/action.
ICON_BINDINGS = (
    (".workspace-mode .rail > .rail-item:nth-child(1)", "toolwindows/project", True, False),
    (".workspace-mode .rail > .rail-item:nth-child(2)", "toolwindows/find", True, False),
    (".workspace-mode .rail > .rail-item:nth-child(3)", "toolwindows/vcs", True, False),
    (".workspace-mode .rail > .rail-item:nth-child(4)", "toolwindows/run", True, False),
    (".workspace-mode .rail > .rail-item:nth-child(6)", "general/settings", False, False),
    (".workspace-mode .workspace-toolbar > button[title='Visual preview']", "general/settings", False, True),
    (".workspace-mode .workspace-toolbar .pynix-run-action", "run/run", False, False),
    (".workspace-mode .workspace-toolbar .pynix-debug-primary", "run/debug", False, False),
    (".workspace-mode .right-tools > button[title='Outline']", "toolwindows/structure", True, True),
    (".workspace-mode .right-tools > button[title='Documentation']", "toolwindows/documentation", True, True),
    (".workspace-mode .bottom > span:nth-of-type(1)", "nodes/ideaProject", False, False),
    (".workspace-mode .pynix-debug-panel-toolbar [data-pynix-debug-action='continue']", "run/resume", False, False),
    (".workspace-mode .pynix-debug-panel-toolbar [data-pynix-debug-action='pause']", "run/pause", False, False),
    (".workspace-mode .pynix-debug-panel-toolbar [data-pynix-debug-action='stepInto']", "run/stepInto", False, False),
    (".workspace-mode .pynix-debug-panel-toolbar [data-pynix-debug-action='stepOver']", "run/stepOver", False, False),
    (".workspace-mode .pynix-debug-panel-toolbar [data-pynix-debug-action='stepOut']", "run/stepOut", False, False),
    (".workspace-mode .pynix-debug-panel-toolbar [data-pynix-debug-action='stop']", "run/stop", False, False),
)

# Keep extensions distinct even when the IDE model groups them as 'code'
# or 'settings'. The source and tab glyph slots expose data-extension.
# This covers file types shown by the actual Project Explorer, including
# those not yet eligible for editing in the source buffer.
EXTENSION_ICON_NAMES = (
    ("js", "fileTypes/javaScript"),
    ("ts", "fileTypes/typeScript"),
    ("css", "fileTypes/css"),
    ("html", "fileTypes/html"),
    ("htm", "fileTypes/html"),
    ("xml", "fileTypes/xml"),
    ("yaml", "fileTypes/yaml"),
    ("yml", "fileTypes/yaml"),
    ("toml", "fileTypes/toml"),
    ("sh", "fileTypes/shell"),
    ("bash", "fileTypes/shell"),
    ("zsh", "fileTypes/shell"),
    ("svg", "fileTypes/image"),
    ("png", "fileTypes/image"),
    ("jpg", "fileTypes/image"),
    ("jpeg", "fileTypes/image"),
    ("webp", "fileTypes/image"),
    ("zip", "fileTypes/archive"),
)

# Project Explorer is rebuilt on expansion/search; these icons require live binding.
# The native PYNIX and Python marks are kept; only standard file types use JB.
DYNAMIC_ICON_BINDINGS = (
    (".workspace-mode .project-glyph.folder-icon", "nodes/folder", False),
    (".workspace-mode .project-glyph.file-json", "fileTypes/json", False),
    (".workspace-mode .project-glyph.file-markdown", "fileTypes/markdown", False),
    (".workspace-mode .project-glyph.file-text", "fileTypes/text", False),
    (".workspace-mode .pynix-tab-file-glyph.file-json", "fileTypes/json", False),
    (".workspace-mode .pynix-tab-file-glyph.file-markdown", "fileTypes/markdown", False),
    (".workspace-mode .pynix-tab-file-glyph.file-text", "fileTypes/text", False),
) + tuple(
    (f".workspace-mode {slot}[data-extension='{extension}']", icon, False)
    for extension, icon in EXTENSION_ICON_NAMES
    for slot in (".project-glyph", ".pynix-tab-file-glyph")
)

ICON_BRIDGE_SCRIPT = r"""<script>
(() => {
 const items=__ICON_DATA__;
 const dynamic=__DYNAMIC_ICON_DATA__;
 const parsed=new Map();
 function activate(target,item){
  if(!target||target.dataset.pynixIcon===item.name)return;
  let source=parsed.get(item.name);
  if(!source){
   const xml=new DOMParser().parseFromString(item.svg,'image/svg+xml');
   source=xml.documentElement;
   if(source.localName!=='svg'||xml.querySelector('parsererror'))return;
   parsed.set(item.name,source);
  }
  const icon=document.importNode(source,true);
  icon.classList.add('pynix-jetbrains-icon');
  icon.setAttribute('aria-hidden','true');
  icon.setAttribute('focusable','false');
  const old=target.querySelector('svg');
  if(old){
   for(const name of old.classList)icon.classList.add(name);
   old.replaceWith(icon);
  }else if(item.replaceLabel){
   target.replaceChildren(icon);
  }else{
   target.prepend(icon);
  }
  target.dataset.pynixIcon=item.name;
 }
 for(const item of items)activate(document.querySelector(item.selector),item);
 // Project tree rows are recreated on folder expand, search and file changes.
 // Observe only that tree; avoid replacing click handlers or editor content.
 const tree=document.querySelector('.workspace-mode .tree');
 if(tree&&dynamic.length){
  const synchronize=()=>{
   for(const item of dynamic)
    for(const target of tree.querySelectorAll(item.selector))activate(target,item);
  };
  synchronize();
  new MutationObserver(synchronize).observe(tree,{childList:true,subtree:true});
 }
 // Open tabs are rebuilt when a source changes or tabs are reordered.
 const editorTabs=document.querySelector('.workspace-mode .editor-tabs');
 if(editorTabs&&dynamic.length){
  const synchronizeTabs=()=>{
   for(const item of dynamic)
    for(const target of editorTabs.querySelectorAll(item.selector))activate(target,item);
  };
  synchronizeTabs();
  new MutationObserver(synchronizeTabs).observe(editorTabs,{childList:true,subtree:true});
 }
})();
</script>"""


def apply_new_ui_icons(
    document: str,
    directory: Path = BUNDLED_ICONS,
    *,
    dark: bool = True,
) -> str:
    """Inject a no-op-safe icon substitution script at the end of the page.

    Existing click listeners and live workspace behavior remain unchanged.
    No network access is used; source SVG license headers are retained in
    the packed icon strings.
    """
    if "</body>" not in document:
        return document
    try:
        catalog = JetBrainsIconCatalog(directory)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return document
    data = []
    for selector, name, tool_window, replace_label in ICON_BINDINGS:
        source = catalog.svg(name, dark=dark, tool_window=tool_window)
        if source is None:
            continue
        data.append({
            "selector": selector,
            "name": name,
            "svg": source,
            "replaceLabel": replace_label,
        })
    dynamic = []
    for selector, name, replace_label in DYNAMIC_ICON_BINDINGS:
        source = catalog.svg(name, dark=dark)
        if source is not None:
            dynamic.append({
                "selector": selector, "name": name,
                "svg": source, "replaceLabel": replace_label,
            })
    if not data and not dynamic:
        return document
    serialized = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")
    serialized_dynamic = json.dumps(dynamic, ensure_ascii=True).replace("<", "\\u003c")
    script = ICON_BRIDGE_SCRIPT.replace("__ICON_DATA__", serialized).replace(
        "__DYNAMIC_ICON_DATA__", serialized_dynamic
    )
    return document.replace("</body>", script + "</body>", 1)

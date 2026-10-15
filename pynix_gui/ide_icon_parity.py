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
)

ICON_BRIDGE_SCRIPT = r"""<script>
(() => {
 const items = __ICON_DATA__;
 for(const item of items){
  const target=document.querySelector(item.selector);
  if(!target)continue;
  const parsed=new DOMParser().parseFromString(item.svg,'image/svg+xml');
  const source=parsed.documentElement;
  if(source.localName!=='svg'||parsed.querySelector('parsererror'))continue;
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
    if not data:
        return document
    serialized = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")
    script = ICON_BRIDGE_SCRIPT.replace("__ICON_DATA__", serialized)
    return document.replace("</body>", script + "</body>", 1)

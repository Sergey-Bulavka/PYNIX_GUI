# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""PyCharm New UI tool-window placement profile for the native PYNIX shell.

JetBrains tools are contextual, not all 787 icons simultaneously visible.
The roster below describes their canonical edge and an explicit readiness
state. Disabled entries never impersonate supported PYNIX functionality.
"""
from __future__ import annotations

import json
from pathlib import Path
from .ide_jetbrains_icons import JetBrainsIconCatalog
from .ide_icon_parity import BUNDLED_ICONS

# (label, licensed icon key, edge, availability)
# The existing Project, Find, VCS, Run, Terminal and Settings hosts keep
# their original implementation, accessibility and event handlers.
TOOL_WINDOW_PROFILE = (
    ("Project", "toolwindows/project", "left-top", "existing"),
    ("Search", "toolwindows/find", "left-top", "existing"),
    ("Version Control", "toolwindows/vcs", "left-top", "existing"),
    ("Run", "toolwindows/run", "left-top", "existing"),
    ("Commit", "toolwindows/commit", "left-top", "unavailable"),
    ("Bookmarks", "toolwindows/bookmarks", "left-top", "unavailable"),
    ("Structure", "toolwindows/structure", "right-top", "existing"),
    ("Documentation", "toolwindows/documentation", "right-top", "existing"),
    ("Database", "toolwindows/services", "right-top", "unavailable"),
    ("Services", "toolwindows/services", "right-top", "unavailable"),
    ("Notifications", "toolwindows/notifications", "right-bottom", "unavailable"),
    ("Problems", "toolwindows/problems", "left-bottom", "existing"),
    ("Debug", "toolwindows/debug", "left-bottom", "existing"),
    ("Terminal", "toolwindows/messages", "left-bottom", "existing"),
    ("TODO", "toolwindows/todo", "left-bottom", "unavailable"),
    ("Build", "toolwindows/build", "left-bottom", "unavailable"),
    ("Profiler", "toolwindows/profiler", "right-bottom", "unavailable"),
)

EDGE_PROFILE_STYLE = """<style id="pynix-edge-profile-style">
.workspace-mode .rail,.workspace-mode .right-tools{
 display:flex!important;flex-direction:column!important;align-items:center!important;
 overflow-y:auto!important;overflow-x:hidden!important;scrollbar-width:none
}
.workspace-mode .rail::-webkit-scrollbar,.workspace-mode .right-tools::-webkit-scrollbar{display:none}
.workspace-mode .rail>.rail-item:nth-child(-n+4){order:0!important;flex-shrink:0!important}
.workspace-mode .rail>.pynix-extra-tools[data-edge="left-top"]{order:1!important}
.workspace-mode .rail>.pynix-extra-tools[data-edge="left-bottom"]{order:2!important}
.workspace-mode .rail>.rail-item:nth-child(n+5){order:3!important;flex-shrink:0!important}
.workspace-mode .right-tools>button{order:0!important;flex-shrink:0!important}
.workspace-mode .right-tools>.pynix-extra-tools[data-edge="right-top"]{order:1!important}
.workspace-mode .right-tools>.pynix-extra-tools[data-edge="right-bottom"]{order:2!important}
.workspace-mode .rail>.pynix-extra-tools[data-edge="left-bottom"],
.workspace-mode .right-tools>.pynix-extra-tools[data-edge="right-bottom"]{
 margin-top:auto!important
}
.workspace-mode .pynix-extra-tools{display:flex;flex-direction:column;
 align-items:center;gap:3px;width:100%;box-sizing:border-box}

.workspace-mode .pynix-extra-tool{display:flex;align-items:center;
 justify-content:center;width:32px;height:32px;min-width:32px;
 padding:5px;border:0;border-radius:6px;background:transparent;color:#868a93}
.workspace-mode .pynix-extra-tool:disabled{opacity:.46;cursor:not-allowed}
.workspace-mode .pynix-extra-tool svg{width:20px;height:20px;flex:none}
.workspace-mode .pynix-extra-tool:focus-visible{outline:2px solid #80b8f4}
.workspace-mode .pynix-tool-profile-more{font:12px system-ui;color:#a9abb2;
 background:transparent;border:0;border-radius:5px;padding:3px 5px}
.workspace-mode .pynix-tool-profile-more:hover{background:#393b40}
.workspace-mode .pynix-tool-profile-popover{position:fixed;z-index:600;
 width:210px;max-height:55vh;overflow:auto;padding:7px;
 border:1px solid #484a50;border-radius:8px;background:#292b30;
 box-shadow:0 9px 24px #0008;color:#dedfe2}
.workspace-mode .pynix-tool-profile-popover[hidden]{display:none}
.workspace-mode .pynix-tool-profile-popover div{font:12px/1.6 system-ui;
 padding:3px 7px}
</style>"""

EDGE_PROFILE_SCRIPT = r"""<script>
(() => {
 const entries=__PROFILE_DATA__;
 const place=(edge,host)=>{
  if(!host)return;
  if(host.querySelector('[data-edge="'+edge+'"]'))return;
  const container=document.createElement('div');
  container.className='pynix-extra-tools';
  container.dataset.edge=edge;
  for(const entry of entries.filter(x=>x.edge===edge&&x.state==='unavailable')){
   const button=document.createElement('button');
   button.type='button';
   button.className='pynix-extra-tool';
   button.disabled=true;
   button.title=entry.label+' — not implemented in PYNIX IDE';
   button.setAttribute('aria-label',button.title);
   if(entry.svg){
    const xml=new DOMParser().parseFromString(entry.svg,'image/svg+xml');
    if(xml.documentElement.localName==='svg'&&!xml.querySelector('parsererror')){
     const node=document.importNode(xml.documentElement,true);
     node.setAttribute('aria-hidden','true');
     button.appendChild(node);
    }
   }
   container.appendChild(button);
  }
  const more=document.createElement('button');
  more.type='button';
  more.className='pynix-tool-profile-more';
  more.textContent='⋯';
  more.title='More tool windows';
  more.setAttribute('aria-label','More tool windows');
  const popover=document.createElement('div');
  popover.className='pynix-tool-profile-popover';
  popover.hidden=true;
  popover.setAttribute('role','group');
  popover.setAttribute('aria-label','Available and planned tool windows');
  for(const entry of entries.filter(x=>x.edge===edge)){
   const row=document.createElement('div');
   row.textContent=entry.label+(entry.state==='unavailable'?' (not available)':'');
   popover.appendChild(row);
  }
  more.setAttribute('aria-expanded','false');
  more.setAttribute('aria-controls','pynix-more-'+edge);
  popover.id='pynix-more-'+edge;
  const setOpen=open=>{
   if(open){
    const bounds=more.getBoundingClientRect();
    const width=210;
    const height=Math.min(window.innerHeight*0.55,entries.filter(x=>x.edge===edge).length*27+16);
    const left=edge.startsWith('left')?bounds.right+7:bounds.left-width-7;
    popover.style.left=Math.max(4,Math.min(window.innerWidth-width-4,left))+'px';
    popover.style.top=Math.max(4,Math.min(window.innerHeight-height-4,bounds.top))+'px';
   }
   popover.hidden=!open;
   more.setAttribute('aria-expanded',String(open));
  };
  more.addEventListener('click',()=>setOpen(popover.hidden));
  more.addEventListener('keydown',event=>{
   if(event.key==='Escape'){setOpen(false);more.focus();}
  });
  document.addEventListener('pointerdown',event=>{
   if(!container.contains(event.target))setOpen(false);
  });
  container.append(more,popover);
  host.appendChild(container);
 };
 const mount=()=>{
  place('left-top',document.querySelector('.workspace-mode .rail'));
  place('left-bottom',document.querySelector('.workspace-mode .rail'));
  place('right-top',document.querySelector('.workspace-mode .right-tools'));
  place('right-bottom',document.querySelector('.workspace-mode .right-tools'));
 };
 mount();
})();
</script>"""


def apply_edge_profile(document: str, directory: Path = BUNDLED_ICONS, *,
                       dark: bool = True) -> str:
    if '</body>' not in document or 'id="pynix-edge-profile-style"' in document:
        return document
    try:
        catalog = JetBrainsIconCatalog(directory)
        entries = [{
            "label": label, "name": key, "edge": edge, "state": state,
            "svg": catalog.svg(key, dark=dark, tool_window=True),
        } for label, key, edge, state in TOOL_WINDOW_PROFILE]
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return document
    payload = json.dumps(entries, ensure_ascii=True).replace("<", "\\u003c")
    return document.replace('</body>',
        EDGE_PROFILE_STYLE + EDGE_PROFILE_SCRIPT.replace('__PROFILE_DATA__', payload)
        + '</body>', 1)

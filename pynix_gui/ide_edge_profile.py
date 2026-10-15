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
from .ide_native_tool_icons import native_tool_icon

# (label, licensed icon key, edge, availability)
# The existing Project, Find, VCS, Run, Terminal and Settings hosts keep
# their original implementation, accessibility and event handlers.
TOOL_WINDOW_PROFILE = (
    ("Project", "toolwindows/project", "left-top", "existing"),
    ("Search", "toolwindows/find", "left-top", "existing"),
    ("Version Control", "toolwindows/vcs", "left-top", "existing"),
    ("Structure", "toolwindows/structure", "left-top", "unavailable"),
    ("Commit", "toolwindows/commit", "left-top", "unavailable"),
    ("Bookmarks", "toolwindows/bookmarks", "left-top", "unavailable"),
    ("Run", "toolwindows/run", "left-bottom", "existing"),
    ("Python Console", "toolwindows/messages", "left-bottom", "unavailable"),
    ("Packages", "nodes/services", "left-bottom", "unavailable"),
    ("Debug", "toolwindows/debug", "left-bottom", "existing"),
    ("Terminal", "toolwindows/messages", "left-bottom", "existing"),
    ("Problems", "toolwindows/problems", "left-bottom", "existing"),
    ("Git", "toolwindows/vcs", "left-bottom", "existing"),
    ("Build", "toolwindows/build", "left-bottom", "unavailable"),
    ("TODO", "toolwindows/todo", "left-bottom", "unavailable"),
    ("Notifications", "toolwindows/notifications", "right-top", "unavailable"),
    ("AI Assistant", "toolwindows/learn", "right-top", "unavailable"),
    ("Documentation", "toolwindows/documentation", "right-top", "unavailable"),
    ("Services", "toolwindows/services", "right-bottom", "unavailable"),
    ("Profiler", "toolwindows/profiler", "right-bottom", "unavailable"),
)

# Matched to the supplied PyCharm screenshot. Tools not pinned remain in
# More Tool Windows, where unavailable capabilities are clearly marked.
PINNED_TOOLS = frozenset({
    "Project", "Search", "Version Control", "Structure",
    "Run", "Python Console", "Packages", "Debug",
    "Terminal", "Problems", "Git", "Notifications", "AI Assistant",
})

# Existing native actions are invoked rather than copying event listeners.
EXISTING_ACTIONS = {
    "Project": "rail:0", "Search": "rail:1",
    "Version Control": "rail:2", "Run": "rail:3",
    "Terminal": "rail:4", "Git": "rail:2",
    "Debug": "dock:DEBUG CONSOLE", "Problems": "dock:PROBLEMS",
}

EDGE_PROFILE_STYLE = """<style id="pynix-edge-profile-style">
/* Single owner for every visible side icon: this JetBrains catalog.
   Hidden legacy controls preserve commands and keyboard shortcuts. */
.workspace-mode .ide>.rail,.workspace-mode .right-tools{
 display:flex!important;flex-direction:column!important;align-items:center!important;
 gap:1px!important;overflow-y:auto!important;overflow-x:hidden!important;
 scrollbar-width:none!important;box-sizing:border-box!important
}
.workspace-mode .ide>.rail::-webkit-scrollbar,
.workspace-mode .right-tools::-webkit-scrollbar{display:none}
/* All former rail elements remain DOM-only command proxies. Neither
   their Lucide artwork nor their CSS can paint over the new strip. */
.workspace-mode .ide>.rail>.rail-item{display:none!important}
.workspace-mode .right-tools>button{display:none!important}
.workspace-mode .ide>.rail>.pynix-extra-tools[data-edge="left-top"]{order:1!important}
.workspace-mode .ide>.rail>.pynix-extra-tools[data-edge="left-bottom"]{
 order:2!important;margin-top:auto!important
}
.workspace-mode .right-tools>.pynix-extra-tools[data-edge="right-top"]{order:0!important}
.workspace-mode .right-tools>.pynix-extra-tools[data-edge="right-bottom"]{
 order:1!important;margin-top:auto!important
}
.workspace-mode .pynix-extra-tools{
 display:flex;flex-direction:column;align-items:center;gap:1px;
 flex:0 0 auto;width:100%;box-sizing:border-box
}
.workspace-mode .pynix-extra-tool{
 display:flex;align-items:center;justify-content:center;
 width:35px;height:37px;min-width:35px;min-height:37px;
 padding:7px;border:0;border-radius:6px;
 color:#afb2bb;background:transparent
}
.workspace-mode .pynix-extra-tool:not(:disabled){cursor:pointer}
.workspace-mode .pynix-extra-tool:not(:disabled):hover{background:#3a3d45}
.workspace-mode .pynix-extra-tool[aria-pressed="true"]{
 background:#3574d6;color:#ffffff
}
.workspace-mode .pynix-extra-tool[aria-pressed="true"] svg [stroke]{
 stroke:#ffffff!important
}
.workspace-mode .pynix-extra-tool[aria-pressed="true"] svg [fill]:not([fill="none"]){
 fill:#ffffff!important
}
.workspace-mode .pynix-extra-tool:disabled{opacity:.56;cursor:not-allowed}
.workspace-mode .pynix-extra-tool svg{display:block;width:20px;height:20px;flex:0 0 20px}
.workspace-mode .pynix-extra-tool:focus-visible,
.workspace-mode .pynix-tool-profile-more:focus-visible{
 outline:2px solid #80b8f4;outline-offset:-2px
}
.workspace-mode .pynix-tool-profile-more{
 display:flex;align-items:center;justify-content:center;
 width:33px;height:30px;margin:0;padding:0;
 font:17px system-ui;color:#a9abb2;
 background:transparent;border:0;border-radius:6px;cursor:pointer
}
.workspace-mode .pynix-tool-profile-more:hover{background:#393b40}
.workspace-mode .pynix-tool-profile-popover{
 position:fixed;z-index:600;width:220px;max-height:55vh;overflow-y:auto;
 padding:6px;border:1px solid #484a50;border-radius:8px;
 background:#292b30;box-shadow:0 9px 24px #0008;color:#dedfe2
}
.workspace-mode .pynix-tool-profile-popover[hidden]{display:none}
.workspace-mode .pynix-tool-profile-popover button{
 display:block;width:100%;padding:6px 9px;text-align:left;
 font:12px/1.4 system-ui;background:transparent;color:inherit;
 border:0;border-radius:5px
}
.workspace-mode .pynix-tool-profile-popover button:hover:not(:disabled){background:#3c414d}
.workspace-mode .pynix-tool-profile-popover button:disabled{opacity:.55}
@media(max-height:720px){
 .workspace-mode .pynix-extra-tool{height:30px;min-height:30px}
}
</style>"""

EDGE_PROFILE_SCRIPT = r"""<script>
(() => {
 const entries=__PROFILE_DATA__;
 const clickExisting=entry=>{
  const command=entry.action||'';
  if(command.startsWith('rail:')){
   const index=Number(command.slice(5));
   document.querySelectorAll('.workspace-mode .rail>.rail-item')[index]?.click();
  }else if(command.startsWith('dock:')){
   const label=command.slice(5);
   const tab=[...document.querySelectorAll('.workspace-mode .terminal-tabs>span,.workspace-mode .terminal-tabs>strong')]
    .find(el=>el.textContent.trim()===label);
   if(tab){
    const collapsed=document.querySelector('.workspace-mode .integrated-terminal.pynix-tool-window-collapsed');
    if(collapsed)document.querySelector('.workspace-mode .pynix-tool-window-restore')?.click();
    tab.click();
   }
  }
 };
 // The old buttons are retained only as JS command targets. Strip all
 // legacy SVG markup so a second icon renderer cannot show through.
 for(const host of document.querySelectorAll('.workspace-mode .rail,.workspace-mode .right-tools')){
  for(const button of host.children){
   if(button.matches('.rail-item,button'))button.querySelectorAll('svg').forEach(svg=>svg.remove());
  }
 }
 const place=(edge,host)=>{
  if(!host||host.querySelector('[data-edge="'+edge+'"]'))return;
  const container=document.createElement('div');
  container.className='pynix-extra-tools';
  container.dataset.edge=edge;
  for(const entry of entries.filter(x=>x.edge===edge&&x.pinned)){
   const button=document.createElement('button');
   button.type='button';
   button.className='pynix-extra-tool';
   button.disabled=entry.state==='unavailable';
   button.title=entry.label+(button.disabled?' — not implemented in PYNIX IDE':'');
   button.setAttribute('aria-label',button.title);
   // PyCharm's Python Console uses the Python identity mark, not the
   // generic Messages icon. Reuse the exact Python glyph from source tabs.
   const visual=entry.label==='Python Console'?
     (window.pynixPythonFileIcon?.()||entry.svg):entry.svg;
   if(visual){
    const xml=new DOMParser().parseFromString(visual,'image/svg+xml');
    if(xml.documentElement.localName==='svg'&&!xml.querySelector('parsererror')){
     const node=document.importNode(xml.documentElement,true);
     node.setAttribute('aria-hidden','true');
     node.setAttribute('focusable','false');
     button.appendChild(node);
    }
   }
   if(!button.disabled)button.addEventListener('click',()=>clickExisting(entry));
   if(entry.action?.startsWith('rail:')){
    const index=Number(entry.action.slice(5));
    const target=document.querySelectorAll('.workspace-mode .rail>.rail-item')[index];
    const sync=()=>{
     const active=!!target?.classList.contains('active');
     button.setAttribute('aria-pressed',String(active));
    };
    sync();
    if(target)new MutationObserver(sync).observe(target,{attributes:true,attributeFilter:['class']});
   }
   container.appendChild(button);
  }
  // The right-bottom group has no pinned controls in the user's reference.
  if(!entries.some(x=>x.edge===edge&&x.pinned)&&edge.endsWith('bottom'))return;
  const more=document.createElement('button');
  more.type='button';
  more.className='pynix-tool-profile-more';
  more.textContent='⋯';
  more.title='More tool windows';
  more.setAttribute('aria-label','More tool windows');
  more.setAttribute('aria-expanded','false');
  more.setAttribute('aria-controls','pynix-more-'+edge);
  const popover=document.createElement('div');
  popover.className='pynix-tool-profile-popover';
  popover.hidden=true;
  popover.id='pynix-more-'+edge;
  popover.setAttribute('role','group');
  popover.setAttribute('aria-label','Available and planned tool windows');
  for(const entry of entries.filter(x=>x.edge===edge)){
   const row=document.createElement('button');
   row.type='button';
   row.disabled=entry.state==='unavailable';
   row.textContent=entry.label+(row.disabled?' (not available)':'');
   row.addEventListener('click',()=>{clickExisting(entry);setOpen(false);});
   popover.appendChild(row);
  }
  const setOpen=open=>{
   if(open){
    const bounds=more.getBoundingClientRect();
    const width=220;
    const height=Math.min(window.innerHeight*.55,popover.childElementCount*30+14);
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
            "svg": native_tool_icon(label, dark=dark) or catalog.svg(key, dark=dark, tool_window=True),
            "pinned": label in PINNED_TOOLS,
            "action": EXISTING_ACTIONS.get(label, ""),
        } for label, key, edge, state in TOOL_WINDOW_PROFILE]
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return document
    payload = json.dumps(entries, ensure_ascii=True).replace("<", "\\u003c")
    return document.replace('</body>',
        EDGE_PROFILE_STYLE + EDGE_PROFILE_SCRIPT.replace('__PROFILE_DATA__', payload)
        + '</body>', 1)

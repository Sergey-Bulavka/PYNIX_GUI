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
from .ide_local_jetbrains_icons import original_endpoints_svg
from .ide_icon_parity import BUNDLED_ICONS

# (label, licensed icon key, edge, availability)
# The existing Project, Find, VCS, Run, Terminal and Settings hosts keep
# their original implementation, accessibility and event handlers.
TOOL_WINDOW_PROFILE = (
    # The top-left order is pinned to the six supplied PyCharm references.
    # The separator and More Tool Windows are structural controls, not tools.
    ("Project", "toolwindows/project", "left-top", "existing"),
    ("Commit", "toolwindows/commit", "left-top", "unavailable"),
    ("Pull Requests", "github/pullRequests", "left-top", "unavailable"),
    ("Structure", "toolwindows/structure", "left-top", "unavailable"),
    ("Search", "toolwindows/find", "left-top", "existing"),
    ("Version Control", "toolwindows/vcs", "left-top", "existing"),
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
    "Project", "Commit", "Pull Requests", "Structure",
    "Run", "Python Console", "Packages", "Debug",
    "Terminal", "Problems", "Git", "Notifications", "AI Assistant",
})

# The left-top More Tool Windows menu follows the supplied PyCharm screenshot.
# (label, exact original JetBrains icon key or None, displayed macOS shortcut,
#  implemented command). None means NO substituted or invented icon.
MORE_TOOL_WINDOWS = (
    ("Bookmarks", "toolwindows/bookmarks", "⌘2", ""),
    ("Find", "toolwindows/find", "⌘3", "rail:1"),
    ("Debug", "toolwindows/debug", "⌘5", "dock:DEBUG CONSOLE"),
    ("Coverage", "toolwindows/coverage", "", ""),
    ("Endpoints", "localJetBrains/endpoints", "", ""),
    ("Hierarchy", "toolwindows/hierarchy", "", ""),
    ("Learn", "toolwindows/learn", "", ""),
    ("Python Process Output", "pythonProcessOutput/process", "", ""),
    ("TODO", "toolwindows/todo", "", ""),
)

# Only this group is iconographic in the native iconless preview.
TOP_LEFT_ICONS = frozenset({"Project", "Commit", "Pull Requests", "Structure"})

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
/* A screenshot-matched JetBrains tool stripe; other rails stay text-only. */
.workspace-mode.pynix-iconless .pynix-extra-tools[data-edge="left-top"]{
 gap:7px!important;padding-top:5px!important
}
.workspace-mode.pynix-iconless .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool{
 display:flex!important;align-items:center!important;justify-content:center!important;
 width:36px!important;height:36px!important;
 min-width:36px!important;min-height:36px!important;
 padding:8px!important;border-radius:8px!important;
 font-size:0!important;flex:0 0 36px!important
}
.workspace-mode.pynix-iconless .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool:disabled{
 opacity:.82!important
}
.workspace-mode.pynix-iconless .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool svg{
 width:20px!important;height:20px!important;flex:0 0 20px!important;
}
.workspace-mode .pynix-tool-profile-more svg{
 display:block;width:20px;height:20px;flex:0 0 20px
}
/* Theme is determined by JetBrains' original _dark/_light SVG variant.
   Window key status is a separate state: soften the EXISTING vectors, never
   switch themes or edit the licensed artwork on focus changes. */
.workspace-mode .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool svg,
.workspace-mode .pynix-extra-tools[data-edge="left-top"] .pynix-tool-profile-more svg{
 transition:opacity 120ms ease;
}
.workspace-mode.pynix-window-inactive .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool svg,
.workspace-mode.pynix-window-inactive .pynix-extra-tools[data-edge="left-top"] .pynix-tool-profile-more svg{
 opacity:.48!important;
}
.workspace-mode.pynix-window-inactive .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool[aria-pressed="true"]{
 background:#3a3b41!important;
}
.workspace-mode.pynix-window-inactive .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool:hover,
.workspace-mode.pynix-window-inactive .pynix-extra-tools[data-edge="left-top"] .pynix-tool-profile-more:hover{
 background:transparent!important;
}
@media(prefers-reduced-motion:reduce){
 .workspace-mode .pynix-extra-tools[data-edge="left-top"] .pynix-extra-tool svg,
 .workspace-mode .pynix-extra-tools[data-edge="left-top"] .pynix-tool-profile-more svg{
  transition:none!important;
 }
}
.workspace-mode .pynix-extra-separator{
 width:24px;height:1px;min-height:1px;flex:0 0 1px;
 background:#4a4c52;border-radius:1px;margin:2px 0 3px
}
.workspace-mode.pynix-iconless .pynix-extra-tools[data-edge="left-top"] .pynix-tool-profile-more{
 width:36px!important;height:36px!important;min-height:36px!important;
 padding:0!important;border-radius:8px!important;
 font-size:17px!important;letter-spacing:2px!important
}
.workspace-mode .pynix-tool-profile-popover{
 position:fixed;z-index:600;width:220px;max-height:55vh;overflow-y:auto;
 padding:6px;border:1px solid #484a50;border-radius:8px;
 background:#292b30;box-shadow:0 9px 24px #0008;color:#dedfe2
}
/* PyCharm-style left-top More popup: icon / label / optional shortcut. */
.workspace-mode .pynix-tool-profile-popover[data-edge="left-top"]{
 width:296px!important;max-width:calc(100vw - 20px)!important;
 max-height:min(55vh,410px)!important;
 padding:8px!important;background:#28292c!important;
 border:1px solid #575a62!important;border-radius:12px!important;
 box-shadow:0 14px 30px #0007!important;
}
.workspace-mode .pynix-tool-profile-popover[data-edge="left-top"] .pynix-more-item{
 display:flex!important;align-items:center!important;gap:10px!important;
 box-sizing:border-box!important;
 min-height:24px!important;height:24px!important;width:100%!important;
 padding:2px 10px!important;border:0!important;border-radius:7px!important;
 font:13px/1.25 system-ui,-apple-system,sans-serif!important;
 white-space:nowrap!important;color:#d2d3d7!important;
 opacity:1!important;
}
.workspace-mode .pynix-tool-profile-popover[data-edge="left-top"] .pynix-more-item.is-highlighted{
 background:#2d4978!important;color:#f2f5fa!important;
}
.workspace-mode .pynix-tool-profile-popover[data-edge="left-top"] .pynix-more-item:hover:not(:disabled){
 background:#3b4b64!important;color:#f2f5fa!important;
}
.workspace-mode .pynix-more-item .pynix-menu-icon{
 display:flex;align-items:center;justify-content:center;
 flex:0 0 20px;width:20px;height:20px;
}
.workspace-mode .pynix-more-item .pynix-menu-icon svg{
 display:block;width:20px;height:20px;
}
.workspace-mode .pynix-more-item .pynix-more-label{
 min-width:0;flex:1 1 auto;overflow:hidden;text-overflow:ellipsis;
 text-align:left;
}
.workspace-mode .pynix-more-item .pynix-more-shortcut{
 flex:0 0 auto;margin-left:auto;color:#a9acb4;
 font:12px/1.2 system-ui,-apple-system,sans-serif;
}
.workspace-mode .pynix-more-item.is-highlighted .pynix-more-shortcut{
 color:#bdc9e0;
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
 const iconless=__ICONLESS__;
 const moreIcon=__MORE_ICON_DATA__;
 const leftTopMore=__MORE_WINDOW_DATA__;
 // NSWindow key state is authoritative in the macOS host. The focus/blur
 // handlers also cover HTML previews and non-native test harnesses.
 const setWindowActive=active=>{
  const workspace=document.querySelector('.workspace-mode');
  if(workspace)workspace.classList.toggle('pynix-window-inactive',!active);
 };
 window.pynixSetWindowActive=setWindowActive;
 window.addEventListener('focus',()=>setWindowActive(true));
 window.addEventListener('blur',()=>setWindowActive(false));
 document.addEventListener('visibilitychange',()=>{
  if(document.hidden)setWindowActive(false);
  else setWindowActive(document.hasFocus());
 });
 setWindowActive(document.hasFocus());

 const shortNames={
  'Project':'Proj','Search':'Find','Version Control':'Git',
  'Structure':'Struct','Run':'Run','Python Console':'Py',
  'Packages':'Pkg','Debug':'Debug','Terminal':'Term',
  'Problems':'Err','Notifications':'Alerts','AI Assistant':'AI',
  'Commit':'Commit','Bookmarks':'Marks','Git':'Git'
 };
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
   // Native icon-free mode has one deliberate exception: the four
   // screenshot-matched, icon-only buttons at the top left.
   const pictogram=iconless&&edge==='left-top';
   if(iconless&&!pictogram)button.textContent=shortNames[entry.label]||entry.label;
   const visual=(iconless&&!pictogram)?null:entry.svg;
   if(visual){
    const xml=new DOMParser().parseFromString(visual,'image/svg+xml');
    if(xml.documentElement.localName==='svg'&&!xml.querySelector('parsererror')){
     const node=document.importNode(xml.documentElement,true);
     node.setAttribute('aria-hidden','true');
     node.setAttribute('focusable','false');
     button.appendChild(node);
    }
   }
   if(!visual&&pictogram)button.textContent=shortNames[entry.label]||entry.label;
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
   if(edge==='left-top'&&entry.label==='Pull Requests'){
    const separator=document.createElement('div');
    separator.className='pynix-extra-separator';
    separator.setAttribute('role','separator');
    separator.setAttribute('aria-orientation','horizontal');
    container.appendChild(separator);
   }
  }
  // The right-bottom group has no pinned controls in the user's reference.
  if(!entries.some(x=>x.edge===edge&&x.pinned)&&edge.endsWith('bottom'))return;
  const more=document.createElement('button');
  more.type='button';
  more.className='pynix-tool-profile-more';
  // The three-dot glyph is the actual JetBrains general/moreHorizontal SVG.
  // In icon-free zones retain the accessible text label.
  if(moreIcon&&(!iconless||edge==='left-top')){
   const xml=new DOMParser().parseFromString(moreIcon,'image/svg+xml');
   if(xml.documentElement.localName==='svg'&&!xml.querySelector('parsererror')){
    const node=document.importNode(xml.documentElement,true);
    node.setAttribute('aria-hidden','true');
    node.setAttribute('focusable','false');
    more.appendChild(node);
   }else more.textContent='More';
  }else more.textContent='More';
  more.title='More tool windows';
  more.setAttribute('aria-label','More tool windows');
  more.setAttribute('aria-expanded','false');
  more.setAttribute('aria-controls','pynix-more-'+edge);
  const popover=document.createElement('div');
  popover.className='pynix-tool-profile-popover';
  popover.hidden=true;
  popover.id='pynix-more-'+edge;
  popover.dataset.edge=edge;
  popover.setAttribute('role','group');
  popover.setAttribute('aria-label','Available and planned tool windows');
  if(edge==='left-top'){
   // Each icon is an original, checksummed JetBrains SVG from the catalog.
   // Missing upstream Endpoints art intentionally remains an empty icon slot.
   for(const entry of leftTopMore){
    const row=document.createElement('button');
    row.type='button';
    row.className='pynix-more-item';
    row.disabled=!entry.action;
    if(row.disabled)row.title=entry.label+' — not implemented in PYNIX IDE';
    row.setAttribute('aria-label',entry.label+(entry.shortcut?' '+entry.shortcut:''));
    if(entry.label==='Bookmarks')row.classList.add('is-highlighted');
    const icon=document.createElement('span');
    icon.className='pynix-menu-icon';
    icon.setAttribute('aria-hidden','true');
    if(entry.svg){
     const xml=new DOMParser().parseFromString(entry.svg,'image/svg+xml');
     if(xml.documentElement.localName==='svg'&&!xml.querySelector('parsererror'))
      icon.appendChild(document.importNode(xml.documentElement,true));
    }
    const label=document.createElement('span');
    label.className='pynix-more-label';
    label.textContent=entry.label;
    row.append(icon,label);
    if(entry.shortcut){
     const shortcut=document.createElement('span');
     shortcut.className='pynix-more-shortcut';
     shortcut.textContent=entry.shortcut;
     row.appendChild(shortcut);
    }
    if(!row.disabled)row.addEventListener('click',()=>{clickExisting(entry);setOpen(false);});
    popover.appendChild(row);
   }
  }else{
   for(const entry of entries.filter(x=>x.edge===edge)){
    const row=document.createElement('button');
    row.type='button';
    row.disabled=entry.state==='unavailable';
    row.textContent=entry.label+(row.disabled?' (not available)':'');
    row.addEventListener('click',()=>{clickExisting(entry);setOpen(false);});
    popover.appendChild(row);
   }
  }
  const setOpen=open=>{
   if(open){
    const bounds=more.getBoundingClientRect();
    const width=edge==='left-top'?296:220;
    const height=Math.min(window.innerHeight*.55,
      popover.childElementCount*(edge==='left-top'?24:30)+18);
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
                       dark: bool = True, iconless: bool = False) -> str:
    if '</body>' not in document or 'id="pynix-edge-profile-style"' in document:
        return document
    try:
        # Other regions remain truly iconless. Resolve just four SVGs for
        # the requested top-left group, without running the legacy icon bridge.
        catalog = JetBrainsIconCatalog(directory) if directory.is_dir() else None
        if catalog is None and not iconless:
            return document

        def glyph(label: str, key: str, edge: str) -> str | None:
            if iconless and (edge != "left-top" or label not in TOP_LEFT_ICONS):
                return None
            # Fail closed: never synthesize or substitute another icon.
            return catalog.svg(key, dark=dark, tool_window=True) if catalog else None

        entries = [{
            "label": label, "name": key, "edge": edge, "state": state,
            "svg": glyph(label, key, edge),
            "pinned": label in PINNED_TOOLS,
            "action": EXISTING_ACTIONS.get(label, ""),
        } for label, key, edge, state in TOOL_WINDOW_PROFILE]
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return document
    more_svg = catalog.svg("general/moreHorizontal", dark=dark,
                           tool_window=True) if catalog is not None else None
    # No missing-icon fallbacks: use only verified original SVGs.
    menu_entries = [{
        "label": label, "name": name, "shortcut": shortcut, "action": action,
        "svg": (original_endpoints_svg(dark=dark) if label == "Endpoints"
               else catalog.svg(name, dark=dark, tool_window=True)
               if name and catalog is not None else None),
    } for label, name, shortcut, action in MORE_TOOL_WINDOWS]
    payload = json.dumps(entries, ensure_ascii=True).replace("<", "\\u003c")
    more_payload = json.dumps(more_svg, ensure_ascii=True).replace("<", "\\u003c")
    menu_payload = json.dumps(menu_entries, ensure_ascii=True).replace("<", "\\u003c")
    return document.replace('</body>',
        EDGE_PROFILE_STYLE + EDGE_PROFILE_SCRIPT.replace('__PROFILE_DATA__', payload).replace(
            '__ICONLESS__', 'true' if iconless else 'false').replace(
            '__MORE_ICON_DATA__', more_payload).replace(
            '__MORE_WINDOW_DATA__', menu_payload)
        + '</body>', 1)

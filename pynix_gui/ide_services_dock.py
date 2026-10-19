"""Services dock with Run Configuration and MCP SSE transport session views.

Use unchanged Apache-2.0 JetBrains SVG assets from the already bundled,
integrity-checked New UI icon catalog rather than approximating their paths.
"""
from __future__ import annotations

import json
from functools import lru_cache

from .ide_icon_parity import BUNDLED_ICONS
from .ide_jetbrains_icons import JetBrainsIconCatalog


SERVICES_JETBRAINS_ICON_NAMES = {
    "add": "general/add",
    "group": "general/show",
    "newMcp": "general/openNewTab",
    "expand": "general/expandAll",
    "collapse": "general/collapseAll",
    "dropdown": "general/dropdown",
    "refresh": "general/locate",
    "settings": "general/settings",
    "checked": "actions/checked",
    "chevronRight": "general/chevronRight",
    "help": "general/help",
    "options": "general/moreVertical",
    "hide": "general/hide",
    "run": "toolwindows/run",
    "mcp": "nodes/services",
}


@lru_cache(maxsize=1)
def services_jetbrains_icons_json() -> str:
    """Original dark JetBrains SVGs, checked against bundled license manifest."""
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    source = {}
    for key, name in SERVICES_JETBRAINS_ICON_NAMES.items():
        svg = catalog.svg(name, dark=True, compact=True)
        if svg is None:
            raise FileNotFoundError(f"Bundled JetBrains Services SVG is missing: {name}")
        source[key] = svg
    return json.dumps(source, ensure_ascii=False).replace("</", "<\\/")


SERVICES_DOCK_JS = r"""
  const servicesPane=document.createElement('section');
  servicesPane.className='pynix-services-pane';
  servicesPane.hidden=true;
  servicesPane.innerHTML=`
   <header class="pynix-services-header">
    <strong>Services</strong><span class="pynix-services-fill"></span>
    <button data-sv="refresh" title="Select Active Service" aria-label="Select Active Service"></button>
    <button data-sv="options" title="Options"></button>
    <div data-sv="optionsMenu" class="pynix-services-options-menu" role="menu" hidden></div>
    <button data-sv="hide" title="Hide Services"></button></header>
   <div class="pynix-services-content">
    <div class="pynix-services-sidebar"><nav class="pynix-services-toolbar" data-sv="toolbar">
     <button data-sv="add" title="Add Service"></button>
     <button data-sv="group" title="Group by Type"></button>
     <button data-sv="newMcp" title="Add MCP SSE Connection" aria-label="Add MCP SSE Connection"></button>
     <span class="pynix-services-toolbar-separator" aria-hidden="true"></span>
     <button data-sv="expand" title="Expand All" aria-label="Expand All"></button>
     <button data-sv="collapse" title="Collapse All" aria-label="Collapse All"></button>
     <div data-sv="menu" class="pynix-services-menu" role="menu" hidden></div>
    </nav><div data-sv="tree" class="pynix-services-tree" role="tree"></div></div>
    <div class="pynix-services-main"><nav class="pynix-services-tabs">
     <button data-sv="sessionTab" class="active" aria-selected="true">Session</button>
     <button data-sv="callsTab" aria-selected="false">Tool Calls</button>
    </nav><div class="pynix-services-details">
     <div data-sv="empty" class="pynix-services-empty">Select a service to view its session</div>
     <div data-sv="session" hidden></div><div data-sv="calls" hidden></div>
    </div></div>
   </div>`;
  terminal.appendChild(servicesPane);
  const sv=key=>servicesPane.querySelector('[data-sv="'+key+'"]');
  // Exact licensed JetBrains New UI assets, inserted by the Python workspace
  // bootstrap after SHA-256 verification by JetBrainsIconCatalog.
  const svIcons=__PYNIX_SERVICES_JETBRAINS_ICONS__;
  const svIcon=key=>{
   const source=svIcons[key];
   if(typeof source!=='string')return null;
   const parsed=new DOMParser().parseFromString(source,'image/svg+xml');
   if(parsed.documentElement.localName!=='svg'||parsed.querySelector('parsererror'))return null;
   const svg=document.importNode(parsed.documentElement,true);
   svg.classList.add('pynix-services-jb-icon');
   svg.setAttribute('aria-hidden','true');
   svg.setAttribute('focusable','false');
   return svg;
  };
  for(const key of ['add','group','newMcp','expand','collapse','refresh','options','hide']){
   const vector=svIcon(key);
   if(vector)sv(key).replaceChildren(vector);
  }
  // The little bottom-right menu corners in PyCharm are separate JetBrains
  // dropdown assets, not drawn triangles or CSS-generated glyphs.
  for(const key of ['add','group']){
   const dropdown=svIcon('dropdown');
   if(dropdown){
    dropdown.classList.add('pynix-services-dropdown');
    sv(key).appendChild(dropdown);
   }
  }
  sv('add').setAttribute('aria-label','Add Service');
  sv('group').setAttribute('aria-label','Group by Type');
  sv('refresh').setAttribute('aria-label','Select Active Service');
  sv('options').setAttribute('aria-label','Options');
  sv('hide').setAttribute('aria-label','Hide Services');
  let svProfiles=[],svSelected='',svTab='session',svGrouped=true;
  const svCollapsed=new Set();
  const svRunStates=new Map();
  let svIncluded=new Set();
  try{
   const stored=JSON.parse(localStorage.getItem('pynix.services.run-types')||'[]');
   if(Array.isArray(stored))for(const id of stored)
    if(['file','run','check'].includes(id))svIncluded.add(id);
  }catch(_){}
  const svNames={file:'Current File',run:'Run Project',check:'Check Project'};
  const svSave=()=>{try{localStorage.setItem('pynix.services.run-types',JSON.stringify([...svIncluded]));}catch(_){}};
  const svPreferences={
   singleClick:true,alwaysSelectOpened:false,alwaysSelectActive:true,
   showTree:true,doubleClickRun:true,showToolbar:true
  };
  try{
   const stored=JSON.parse(localStorage.getItem('pynix.services.options')||'{}');
   if(stored&&typeof stored==='object')
    for(const key of Object.keys(svPreferences))
     if(typeof stored[key]==='boolean')svPreferences[key]=stored[key];
  }catch(_){}
  const svSavePreferences=()=>{
   try{localStorage.setItem('pynix.services.options',JSON.stringify(svPreferences));}catch(_){}
  };
  const svApplyPreferences=()=>{
   servicesPane.classList.toggle('hide-tree',!svPreferences.showTree);
   servicesPane.classList.toggle('hide-toolbar',!svPreferences.showToolbar);
  };
  svApplyPreferences();
  const svcSelectedActive=()=>{
   sv('tree').querySelector('.pynix-services-item[aria-selected="true"]')?.scrollIntoView({block:'nearest'});
  };
  const svSelectItem=id=>{
   svSelected=id;
   for(const item of sv('tree').querySelectorAll('.pynix-services-item'))
    item.setAttribute('aria-selected',String(item.dataset.serviceId===id));
   svDetail();
  };
  const svSend=(action,extra={})=>{
   const bridge=window.webkit?.messageHandlers?.pynixServices;
   if(!bridge){sv('empty').textContent='Services requires native PYNIX IDE.';return false;}
   bridge.postMessage({action,...extra});return true;
  };
  const svRefresh=()=>svSend('list');
  const svRunConfiguration=mode=>{
   const select=document.querySelector('.pynix-run-mode');
   if(!select)return;
   select.value=mode;
   select.dispatchEvent(new Event('change',{bubbles:true}));
   document.querySelector('.pynix-run-action')?.click();
  };
  const svItems=()=>[
   ...Object.keys(svNames).filter(id=>svIncluded.has(id)).map(id=>({
    id:'run:'+id,name:svNames[id],type:'run',state:(svRunStates.get(id)?.state||'idle')
   })),...svProfiles
  ];
  const svDuration=seconds=>{
   let count=Math.max(0,Math.floor(seconds));
   const days=Math.floor(count/86400);count%=86400;
   const hours=Math.floor(count/3600);count%=3600;
   const mins=Math.floor(count/60);count%=60;
   return [days?days+' d':null,hours?hours+' h':null,
    mins?mins+' m':null,count+' s'].filter(Boolean).join(' ');
  };
  const svField=(host,key,value)=>{
   const row=document.createElement('div');row.className='pynix-services-field';
   const k=document.createElement('span');k.textContent=key;
   const v=document.createElement('span');v.textContent=String(value??'—');
   row.append(k,v);host.appendChild(row);
  };
  const svAction=(host,text,handler,disabled=false)=>{
   const button=document.createElement('button');button.type='button';
   button.className='pynix-services-action';button.textContent=text;
   button.disabled=disabled;button.addEventListener('click',handler);
   host.appendChild(button);
  };
  const svDetail=()=>{
   const item=svItems().find(x=>x.id===svSelected);
   sv('empty').hidden=!!item;
   sv('session').hidden=!item||svTab!=='session';
   sv('calls').hidden=!item||svTab!=='calls';
   for(const [id,active] of [['sessionTab',svTab==='session'],['callsTab',svTab==='calls']]){
    sv(id).classList.toggle('active',active);
    sv(id).setAttribute('aria-selected',String(active));
   }
   const session=sv('session'),calls=sv('calls');
   session.replaceChildren();calls.replaceChildren();
   if(!item)return;
   if(item.type==='run'){
    svField(session,'Configuration',item.name);
    const run=svRunStates.get(item.id.slice(4))||{state:'idle',since:0};
    svField(session,'Status',run.state);
    if(run.since&&run.state==='running')
     svField(session,'Duration',svDuration((Date.now()-run.since)/1000));
    const actions=document.createElement('div');actions.className='pynix-services-actions';
    svAction(actions,'Run',()=>svRunConfiguration(item.id.slice(4)),
     run.state==='running');
    svAction(actions,'Stop',()=>document.querySelector('.pynix-stop-action')?.click(),run.state!=='running');
    svAction(actions,'Open Run',()=>window.pynixTerminalDock?.showRun?.());
    svAction(actions,'Remove from Services',()=>{
     svIncluded.delete(item.id.slice(4));svSave();svSelected='';svDraw();
    });
    session.appendChild(actions);
    calls.textContent='Run configurations do not expose MCP tool calls.';
    return;
   }
   svField(session,'Client',item.client||'PYNIX IDE');
   svField(session,'Version',item.version||'—');
   svField(session,'Transport',item.transport||'SSE');
   svField(session,'Status',item.state||'disconnected');
   svField(session,'Endpoint',item.url);
   if(item.since)svField(session,'Duration',svDuration(Date.now()/1000-item.since));
   if(item.error)svField(session,'Error',item.error);
   svField(session,'Discovered tools',(item.tools||[]).length);
   if(item.tools?.length)svField(session,'Available',item.tools.join(', '));
   const actions=document.createElement('div');actions.className='pynix-services-actions';
   svAction(actions,'Connect',()=>svSend('connect',{id:item.id}),['connected','connecting'].includes(item.state));
   svAction(actions,'Disconnect',()=>svSend('disconnect',{id:item.id}),!['connected','connecting'].includes(item.state));
   svAction(actions,'Remove',()=>{
    if(window.confirm('Remove service '+item.name+'?'))svSend('remove',{id:item.id});
   });
   session.appendChild(actions);
   for(const event of item.events||[]){
    const row=document.createElement('div');row.className='pynix-services-call';
    const time=document.createElement('time');time.textContent=new Date(event.time*1000).toLocaleTimeString();
    const kind=document.createElement('strong');kind.textContent=event.type;
    const text=document.createElement('span');text.textContent=event.detail;
    row.append(time,kind,text);calls.appendChild(row);
   }
   if(!calls.children.length)calls.textContent='No MCP protocol events yet. Connect to an SSE server.';
  };
  const svDraw=()=>{
   const tree=sv('tree');const previousScroll=tree.scrollTop;
   tree.replaceChildren();
   const items=svItems();
   if(svSelected&&!items.some(x=>x.id===svSelected))svSelected='';
   if(!svSelected&&items.length)svSelected=items[0].id;
   if(!items.length){
    const hint=document.createElement('div');hint.className='pynix-services-muted';
    hint.textContent='No services. Click + to add a Run configuration or MCP SSE connection.';
    tree.appendChild(hint);
   }
   for(const [label,group] of [
    ['Run Configurations',items.filter(x=>x.type==='run')],
    ['MCP SSE',items.filter(x=>x.type!=='run')]
   ]){
    if(!group.length)continue;
    if(svGrouped){
     const title=document.createElement('button');
     title.type='button';title.className='pynix-services-group';
     title.textContent=(svCollapsed.has(label)?'▸ ':'▾ ')+label;
     title.setAttribute('aria-expanded',String(!svCollapsed.has(label)));
     title.addEventListener('click',()=>{
      if(svCollapsed.has(label))svCollapsed.delete(label);
      else svCollapsed.add(label);
      svDraw();
     });
     tree.appendChild(title);
     if(svCollapsed.has(label))continue;
    }
    for(const item of group){
     const button=document.createElement('button');button.type='button';
     button.className='pynix-services-item';
     button.setAttribute('role','treeitem');
     button.dataset.serviceId=item.id;
     button.setAttribute('aria-selected',String(item.id===svSelected));
     const icon=document.createElement('span');icon.className='pynix-services-item-icon';
     const typeIcon=svIcon(item.type==='run'?'run':'mcp');
     if(typeIcon)icon.appendChild(typeIcon);
     const name=document.createElement('span');name.textContent=item.name;
     const state=document.createElement('span');state.className='pynix-services-status';
     state.textContent=['connected','running'].includes(item.state)?'●':
      item.state==='connecting'?'◌':item.state==='error'?'!':'';
     state.title=item.state||'';
     button.append(icon,name,state);
     button.addEventListener('click',()=>{
      if(svPreferences.singleClick)svSelectItem(item.id);
     });
     button.addEventListener('dblclick',()=>{
      svSelectItem(item.id);
      if(item.type==='run'&&svPreferences.doubleClickRun)
       svRunConfiguration(item.id.slice(4));
     });
     tree.appendChild(button);
    }
   }
   svDetail();tree.scrollTop=previousScroll;
  };
  const menu=sv('menu');
  const menuAction=(title,callback)=>{
   const button=document.createElement('button');button.type='button';
   button.textContent=title;button.setAttribute('role','menuitem');
   button.addEventListener('click',()=>{menu.hidden=true;callback();});
   menu.appendChild(button);
  };
  for(const [id,name] of Object.entries(svNames))
   menuAction('Run Configuration → '+name,()=>{
    svIncluded.add(id);svSave();svSelected='run:'+id;svDraw();
   });
  const svAddMcp=()=>{
   const name=window.prompt('Service name:');
   if(name===null)return;
   const url=window.prompt('MCP SSE URL (HTTPS or localhost HTTP):');
   if(url!==null)svSend('add',{name,url});
  };
  menuAction('MCP SSE Connection…',svAddMcp);
  sv('add').addEventListener('click',()=>menu.hidden=!menu.hidden);
  sv('newMcp').addEventListener('click',svAddMcp);
  // The JetBrains popup is a true overlay; clipping it to the dock would
  // cut off the long list and its submenus at the bottom tool-window edge.
  const optionsMenu=sv('optionsMenu');
  document.body.appendChild(optionsMenu);
  optionsMenu.setAttribute('aria-label','Services Options');
  const svDivider=()=>{
   const divider=document.createElement('div');
   divider.className='pynix-services-options-divider';
   divider.setAttribute('role','separator');
   optionsMenu.appendChild(divider);
  };
  const svOption=(label,callback,config={})=>{
   const parent=config.parent||optionsMenu;
   const row=document.createElement('div');row.className='pynix-services-option-wrap';
   const button=document.createElement('button');
   button.type='button';button.className='pynix-services-option';
   button.setAttribute('role',config.key?'menuitemcheckbox':'menuitem');
   button.disabled=!!config.disabled;
   if(config.disabled){
    button.title=config.reason||'Not supported in this version of PYNIX IDE';
    button.setAttribute('aria-disabled','true');
   }
   const mark=document.createElement('span');mark.className='pynix-services-option-mark';
   if(config.icon){
    const svg=svIcon(config.icon);
    if(svg)mark.appendChild(svg);
   }else if(config.checked){
    // Check marks are also original 16px JetBrains New UI icons.
    const check=svIcon('checked');
    if(check)mark.appendChild(check);
    button.setAttribute('aria-checked','true');
   }else if(config.key)button.setAttribute('aria-checked','false');
   const text=document.createElement('span');
   text.className='pynix-services-option-label';text.textContent=label;
   button.append(mark,text);
   if(config.shortcut){
    const hint=document.createElement('span');hint.className='pynix-services-option-shortcut';
    if(config.shortcut==='⇧⌘T'){
     // These are macOS keyboard modifiers, not toolbar SVG icons.
     // Isolate each glyph so JetBrains-like metrics don't depend on
     // WebKit kerning a mixed-symbol text run as a single font fallback.
     hint.classList.add('pynix-services-shortcut-keys');
     hint.setAttribute('aria-label','Shift Command T');
     for(const [key,glyph] of [['shift','⇧'],['command','⌘'],['letter','T']]){
      const part=document.createElement('span');
      part.className='pynix-services-shortcut-key pynix-services-shortcut-'+key;
      part.textContent=glyph;
      part.setAttribute('aria-hidden','true');
      hint.appendChild(part);
     }
    }else hint.textContent=config.shortcut;
    button.appendChild(hint);
   }
   if(config.submenu){
    row.classList.add('has-submenu');
    const arrow=svIcon('chevronRight');
    if(arrow){arrow.classList.add('pynix-services-option-arrow');button.appendChild(arrow);}
   }
   row.appendChild(button);parent.appendChild(row);
   if(config.submenu){
    const children=document.createElement('div');
    children.className='pynix-services-submenu';
    children.setAttribute('role','menu');row.appendChild(children);
    config.submenu(children);
    button.setAttribute('aria-haspopup','menu');
    button.setAttribute('aria-expanded','false');
    row.addEventListener('mouseenter',()=>button.setAttribute('aria-expanded','true'));
    row.addEventListener('mouseleave',()=>button.setAttribute('aria-expanded','false'));
    button.addEventListener('click',()=>row.classList.toggle('submenu-open'));
   }else if(callback&&!config.disabled){
    button.addEventListener('click',()=>{
     optionsMenu.hidden=true;callback();
    });
   }
   return row;
  };
  const svIsPinned=()=>{
   try{return localStorage.getItem('pynix.services.unpinned')!=='true';}
   catch(_){return true;}
  };
  const svSetPinned=pinned=>{
   try{localStorage.setItem('pynix.services.unpinned',String(!pinned));}catch(_){}
   window.dispatchEvent(new CustomEvent('pynix:services-pin',{detail:{pinned}}));
  };
  // We only advertise actually supported tool-window mode/placement here.
  // Floating and other-edge docking require a separate native window host.
  const svResizeDock=change=>{
   if(change==='restore'){
    terminal.style.removeProperty('height');
    terminal.style.removeProperty('flex-basis');
    return;
   }
   const current=terminal.getBoundingClientRect().height;
   const target=Math.max(145,Math.min(window.innerHeight*0.55,
    Math.round(current+(change==='increase'?70:-70))));
   terminal.style.setProperty('height',target+'px','important');
   terminal.style.setProperty('flex-basis',target+'px','important');
  };
  const svShowOptions=()=>{
   optionsMenu.replaceChildren();
   const toggle=(label,key,handler,shortcut)=>{
    svOption(label,()=>{svPreferences[key]=!svPreferences[key];
      svSavePreferences();svApplyPreferences();
      if(handler)handler();
    },{key,checked:svPreferences[key],shortcut});
   };
   toggle('Navigate with Single Click','singleClick');
   toggle('Always Select Opened Element','alwaysSelectOpened');
   toggle('Always Select Active Service','alwaysSelectActive');
   toggle('Show Services Tree','showTree',null,'⇧⌘T');
   svOption('Configure Services Tool Window',()=>{
    menu.hidden=false;
    sv('add').focus();
   },{icon:'settings'});
   toggle('Double Click to Run Configuration','doubleClickRun');
   svDivider();
   toggle('Show Toolbar','showToolbar');
   svOption('View Mode',null,{submenu:host=>{
    svOption('Docked',()=>{},{parent:host,checked:true});
    svOption('Floating',null,{parent:host,disabled:true});
    svOption('Windowed',null,{parent:host,disabled:true});
   }});
   svOption('Move to',null,{submenu:host=>{
    svOption('Bottom',()=>{},{parent:host,checked:true});
    svOption('Left',null,{parent:host,disabled:true});
    svOption('Right',null,{parent:host,disabled:true});
   }});
   svOption('Resize',null,{submenu:host=>{
    svOption('Increase Height',()=>svResizeDock('increase'),{parent:host});
    svOption('Decrease Height',()=>svResizeDock('decrease'),{parent:host});
    svOption('Restore Height',()=>svResizeDock('restore'),{parent:host});
   }});
   svDivider();
   svOption(svIsPinned()?'Remove from Sidebar':'Restore to Sidebar',
    ()=>svSetPinned(!svIsPinned()));
   svDivider();
   svOption('Help',()=>{
    window.open('https://www.jetbrains.com/help/pycharm/services-tool-window.html',
     '_blank','noopener');
   },{icon:'help'});
  };
  const svPlaceOptions=()=>{
   const rect=sv('options').getBoundingClientRect();
   const width=optionsMenu.offsetWidth||322;
   const height=optionsMenu.offsetHeight||540;
   optionsMenu.style.left=Math.max(8,Math.min(rect.right-width,
    window.innerWidth-width-8))+'px';
   optionsMenu.style.top=Math.max(8,Math.min(rect.bottom+5,
    window.innerHeight-height-8))+'px';
  };
  sv('options').setAttribute('aria-haspopup','menu');
  sv('options').setAttribute('aria-expanded','false');
  sv('options').addEventListener('click',()=>{
   const opening=optionsMenu.hidden;
   menu.hidden=true;
   if(opening)svShowOptions();
   optionsMenu.hidden=!opening;
   sv('options').setAttribute('aria-expanded',String(opening));
   if(opening)svPlaceOptions();
  });
  sv('group').addEventListener('click',()=>{svGrouped=!svGrouped;svDraw();});
  sv('expand').addEventListener('click',()=>{svGrouped=true;svCollapsed.clear();svDraw();});
  sv('collapse').addEventListener('click',()=>{
   svGrouped=true;svCollapsed.add('Run Configurations');svCollapsed.add('MCP SSE');svDraw();
  });
  // PyCharm's bullseye selects an active item; refresh occurs independently.
  sv('refresh').addEventListener('click',()=>{
   const active=svItems().find(item=>['connected','connecting','running'].includes(item.state));
   if(active){svSelected=active.id;svDraw();svcSelectedActive();}else svRefresh();
  });
  sv('hide').addEventListener('click',()=>setToolWindowVisible(false));
  sv('sessionTab').addEventListener('click',()=>{svTab='session';svDetail();});
  sv('callsTab').addEventListener('click',()=>{svTab='calls';svDetail();});
  document.addEventListener('pointerdown',event=>{
   if(!sv('toolbar').contains(event.target)&&!sv('options').contains(event.target))
    menu.hidden=true;
   if(!optionsMenu.contains(event.target)&&!sv('options').contains(event.target)){
    optionsMenu.hidden=true;
    sv('options').setAttribute('aria-expanded','false');
   }
  });
  window.pynixServicesResult=result=>{
   if(result?.error){
    sv('empty').textContent='Services error: '+String(result.error);
    sv('empty').hidden=false;return;
   }
   if(Array.isArray(result?.services)){
    svProfiles=result.services;
    if(svPreferences.alwaysSelectActive){
     const active=svProfiles.find(item=>['connected','connecting'].includes(item.state));
     if(active&&svSelected!==active.id)svSelected=active.id;
    }
    svDraw();
   }
  };
  window.pynixServicesRunEvent=(packet,request)=>{
   const state=packet?.state;
   const key=request?.source?'file':request?.mode;
   if(!['file','run','check'].includes(key))return;
   const previous=svRunStates.get(key)||{state:'idle',since:0};
   if(state==='running'){
    svRunStates.set(key,{state:'running',since:Date.now()});
    if(svPreferences.alwaysSelectOpened&&svIncluded.has(key))
     svSelected='run:'+key;
   }
   if(['finished','error','idle'].includes(state))
    svRunStates.set(key,{state,since:previous.since});
   if(!servicesPane.hidden&&state!=='output'){svDraw();}
  };
  window.addEventListener('pynix:terminal-change',event=>{
   if(event.detail?.scope!=='services'||!event.detail?.visible){
    optionsMenu.hidden=true;menu.hidden=true;
    sv('options').setAttribute('aria-expanded','false');
   }
  });
  const servicesOnShow=()=>{svDraw();svRefresh();};
  window.setInterval(()=>{
   if(!servicesPane.hidden){svRefresh();svDetail();}
  },2500);
"""
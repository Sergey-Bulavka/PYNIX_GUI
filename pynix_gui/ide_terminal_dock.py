# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Independent system-shell sessions and PYNIX Console in native IDE V4.

The dock host is shared for layout only. The two tools have distinct icons,
commands, buffers, inputs and lifecycle; stdout from run/debug stays separate.
"""

TERMINAL_DOCK_JS = r"""
 if(terminal&&toolTabs){
  const header=document.createElement('div');
  header.className='pynix-terminal-dock-bar';
  header.setAttribute('role','toolbar');
  const title=document.createElement('span');
  title.className='pynix-terminal-dock-title';
  const sessions=document.createElement('div');
  sessions.className='pynix-terminal-session-tabs';
  const newSession=document.createElement('button');
  newSession.type='button';newSession.className='pynix-terminal-dock-action pynix-terminal-new';
  newSession.textContent='+';newSession.title='';newSession.dataset.hint='New Tab (⌘T)';
  newSession.setAttribute('aria-label','New Terminal Tab');
  const chevron=document.createElement('details');
  chevron.className='pynix-terminal-shell-dropdown';
  const summary=document.createElement('summary');
  summary.className='pynix-terminal-dock-action pynix-terminal-shell-chevron';
  summary.setAttribute('aria-label','Choose Terminal Shell');
  summary.title='';summary.dataset.hint='Choose Terminal Shell';
  summary.innerHTML='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3.3 5.9 4.7 4.7 4.7-4.7" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const popup=document.createElement('div');popup.className='pynix-terminal-dock-popup';
  popup.setAttribute('role','menu');
  chevron.append(summary,popup);
  const overflow=document.createElement('details');
  overflow.className='pynix-terminal-tab-overflow';
  overflow.hidden=true;
  const overflowToggle=document.createElement('summary');
  overflowToggle.className='pynix-terminal-dock-action';
  overflowToggle.innerHTML='<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="m3.5 6 4.5 4.5L12.5 6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  overflowToggle.setAttribute('aria-label','More Tabs');
  overflowToggle.dataset.hint='More Tabs';
  const overflowPopup=document.createElement('div');
  overflowPopup.className='pynix-terminal-dock-popup';overflowPopup.setAttribute('role','menu');
  overflow.append(overflowToggle,overflowPopup);
  const gap=document.createElement('span');gap.className='pynix-terminal-dock-gap';
  const tools=document.createElement('details');tools.className='pynix-terminal-options-menu';
  const more=document.createElement('summary');
  more.className='pynix-terminal-dock-action';more.textContent='⋮';
  more.title='';more.dataset.hint='Options';more.setAttribute('aria-label','Options');
  const toolsPopup=document.createElement('div');
  toolsPopup.className='pynix-terminal-dock-popup';toolsPopup.setAttribute('role','menu');
  tools.append(more,toolsPopup);
  const hide=document.createElement('button');hide.type='button';
  hide.className='pynix-terminal-dock-action pynix-terminal-dock-hide';
  hide.textContent='−';hide.title='Hide Tool Window';
  hide.setAttribute('aria-label','Hide Tool Window');
  hide.addEventListener('click',()=>setToolWindowVisible(false));
  header.append(title,sessions,newSession,overflow,chevron,gap,tools,hide);
  terminal.insertBefore(header,debugPanelBar.nextSibling);

  const hintStyle=document.createElement('style');
  hintStyle.textContent='.pynix-terminal-dock-bar [data-hint]{position:relative}.pynix-terminal-dock-bar [data-hint]:hover::after,.pynix-terminal-dock-bar [data-hint]:focus-visible::after{content:attr(data-hint);position:absolute;z-index:300;top:calc(100% + 7px);left:50%;transform:translateX(-50%);background:#383a40;border:1px solid #575a63;border-radius:6px;color:#e5e6ea;padding:6px 9px;font:12px/17px -apple-system,sans-serif;white-space:nowrap;pointer-events:none;box-shadow:0 4px 14px #0006}';
  hintStyle.textContent+=`
  .pynix-terminal-dock-bar{display:flex;align-items:center;min-width:0}
  .pynix-terminal-dock-title,.pynix-terminal-new,.pynix-terminal-tab-overflow,
  .pynix-terminal-options-menu,.pynix-terminal-dock-hide{flex-shrink:0}
  .pynix-terminal-session-tabs{display:flex!important;align-items:center;min-width:0!important;width:auto!important;max-width:none!important;overflow:hidden;flex:1 1 auto!important}
  .pynix-terminal-dock-gap{flex:0 0 0!important;width:0!important;margin:0!important}
  .pynix-terminal-tab-overflow>summary{width:27px;height:28px;display:flex!important;align-items:center;justify-content:center;padding:0!important;line-height:1!important;list-style:none}
  .pynix-terminal-tab-overflow>summary::-webkit-details-marker{display:none}
  .pynix-terminal-tab-overflow>summary svg{display:block;flex:none}
  .pynix-terminal-new{order:0}
  .pynix-terminal-session-tab{flex-shrink:0}\n  .pynix-terminal-session-tab[hidden]{display:none!important}
  .pynix-terminal-tab-overflow{position:relative;flex-shrink:0}
  .pynix-terminal-tab-overflow[hidden]{display:none!important}
  .pynix-terminal-tab-overflow>.pynix-terminal-dock-popup{right:0;left:auto;min-width:175px;max-height:320px;overflow-y:auto}
  .pynix-terminal-tab-overflow .pynix-overflow-entry{display:block;width:100%;text-align:left}
  .pynix-terminal-options-menu .pynix-terminal-menu-divider{height:1px;background:#41434a;margin:6px 2px}
  .pynix-terminal-options-menu .pynix-terminal-menu-sub{padding-left:16px}
  .pynix-terminal-options-menu .pynix-terminal-menu-disabled{opacity:.5}
  `;
  document.head.appendChild(hintStyle);
  const makePanel=(cls,label)=>{
   const panel=document.createElement('div');panel.className=cls;
   panel.setAttribute('aria-label',label);
   const log=document.createElement('pre');log.className='pynix-terminal-log';
   const input=document.createElement('textarea');
   input.className='pynix-terminal-input';input.rows=1;
   input.setAttribute('aria-label',label+' input');
   input.setAttribute('spellcheck','false');input.setAttribute('autocomplete','off');
   panel.append(log,input);terminal.appendChild(panel);
   return {panel,log,input};
  };
  const system=makePanel('pynix-system-terminal','System Terminal');
  const pynix=makePanel('pynix-language-terminal','PYNIX Console');
  pynix.log.textContent='PYNIX Console — type help for supported commands.\n';
  const shellTabs=new Map();
  let activeId=null,scope='other',serial=0,pynixBusy=false;
  const pynixTabs=new Map();let pynixId=null,pynixSerial=0,pynixPending=null,shellCreating=false;
  let defaultShell='zsh';
  try{defaultShell=localStorage.getItem('pynix.ide.defaultShell')||'zsh';}catch(_){}
  if(!['bash','zsh'].includes(defaultShell))defaultShell='zsh';
  const native=(message)=>{
   const handler=window.webkit?.messageHandlers?.pynixTerminalSession;
   if(!handler){
    if(message.scope==='shell')system.log.textContent+='Native macOS terminal unavailable.\n';
    else pynix.log.textContent+='PYNIX compiler bridge unavailable.\n';
    return;
   }
   handler.postMessage(message);
  };
  const append=(log,data)=>{
   if(!data)return;
   // Native output only ever becomes text, never HTML.
   log.textContent+=String(data).replace(/\x1b\[[0-9;?]*[ -/]*[@-~]/g,'');
   if(log.textContent.length>250000)log.textContent=log.textContent.slice(-200000);
   log.scrollTop=log.scrollHeight;
  };
  const isVisible=()=>!terminal.classList.contains('pynix-tool-window-collapsed');
  const publish=()=>{
   const detail={scope,visible:isVisible()};
   window.dispatchEvent(new CustomEvent('pynix:terminal-change',{detail}));
  };
  const sync=()=>{
   const visible=isVisible();
   system.panel.hidden=!visible||scope!=='system';
   pynix.panel.hidden=!visible||scope!=='pynix';
   toolConsole.hidden=scope!=='other';
   const legacy=document.querySelectorAll('.workspace-mode .rail>.rail-item')[4];
   legacy?.classList.toggle('active',visible&&scope==='system');
   legacy?.setAttribute('aria-pressed',String(visible&&scope==='system'));
   title.textContent=scope==='pynix'?'PYNIX Console':scope==='system'?'Terminal':(
    selectedTool==='TERMINAL'?'Run':selectedTool[0]+selectedTool.slice(1).toLowerCase());
   sessions.hidden=scope==='other';
   newSession.hidden=scope==='other'||!showToolbar;
   newSession.dataset.hint=scope==='pynix'?'New Console Tab (⌘T)':'New Tab (⌘T)';
   paintSessions();
   chevron.hidden=scope!=='system'||!showToolbar;
   renderOptions();
   publish();
  };
  const select=id=>{
   if(!['system','pynix'].includes(id))return;
   if(scope===id&&isVisible()){setToolWindowVisible(false);return;}
   scope=id;setToolWindowVisible(true);
   if(id==='system'&&!shellTabs.size)createShell(defaultShell);
   if(id==='pynix'&&!pynixTabs.size)createPynixTab();
   if(id==='system')system.input.focus();else pynix.input.focus();
  };
  window.pynixTerminalDock={
   sync,select,state:()=>({scope,visible:isVisible()}),
   show:()=>select('system'),hide:()=>setToolWindowVisible(false),
   toggle:()=>select('system')
  };
  // One legacy sidebar proxy is kept for keyboard compatibility; its
  // PYNIX-branded neighbor uses the separate direct edge action.
  const legacy=document.querySelectorAll('.workspace-mode .rail>.rail-item')[4];
  legacy?.addEventListener('click',()=>select('system'));
  legacy?.addEventListener('keydown',event=>{
   if(event.key==='Enter'||event.key===' '){event.preventDefault();select('system');}
  });

  const updateOverflow=()=>{
   if(scope==='other'){overflow.hidden=true;return;}
   // Reserve the right-side controls before measuring the tab viewport.
   const active=scope==='pynix'?pynixId:activeId;
   const items=[...sessions.children];
   for(const item of items)item.hidden=false;
   overflow.hidden=true;
   const natural=items.reduce((total,item)=>total+item.getBoundingClientRect().width,0);
   if(sessions.clientWidth<1)return;
   if(natural<=sessions.clientWidth+1)return;
   overflow.hidden=false;
   const room=sessions.clientWidth;
   if(room<1)return;
   let used=0;
   const hidden=[];
   for(let index=0;index<items.length;index++){
    const item=items[index],width=item.getBoundingClientRect().width;
    if(used+width>room+0.5){item.hidden=true;hidden.push(index);}
    else used+=width;
   }
   overflowPopup.replaceChildren();
   const tabs=[...(scope==='pynix'?pynixTabs:shellTabs).entries()];
   for(const index of hidden){
    const [id,tab]=tabs[index];
    const entry=document.createElement('button');entry.type='button';
    entry.className='pynix-overflow-entry';entry.setAttribute('role','menuitem');
    entry.textContent=(id===active?'✓ ':'')+tab.label;
    entry.addEventListener('click',()=>{
     overflow.open=false;
     if(scope==='pynix'){
      if(pynixTabs.has(pynixId))pynixTabs.get(pynixId).draft=pynix.input.value;
      pynixId=id;paintSessions();paintPynix();
     }else{activeId=id;paintSessions();paintShell();}
    });
    overflowPopup.appendChild(entry);
   }
  };
  const paintSessions=()=>{
   sessions.replaceChildren();
   const isPynix=scope==='pynix', tabs=isPynix?pynixTabs:shellTabs;
   const active=isPynix?pynixId:activeId;
   for(const [id,tab] of tabs){
    const item=document.createElement('div');
    item.className='pynix-terminal-session-tab'+(id===active?' active':'');
    const button=document.createElement('button');button.type='button';
    button.className='pynix-terminal-session-select';button.textContent=tab.label;
    button.title=isPynix?'PYNIX Console':tab.shell;
    button.setAttribute('aria-selected',String(id===active));
    button.addEventListener('click',()=>{
     if(isPynix){if(pynixTabs.has(pynixId))pynixTabs.get(pynixId).draft=pynix.input.value;pynixId=id;paintSessions();paintPynix();}
     else{activeId=id;paintSessions();paintShell();}
    });
    const close=document.createElement('button');close.type='button';
    close.className='pynix-terminal-session-close';close.textContent='×';
    close.setAttribute('aria-label','Close '+tab.label);
    close.addEventListener('click',()=>{
     if(isPynix){
      if(pynixTabs.has(pynixId))pynixTabs.get(pynixId).draft=pynix.input.value;
      pynixTabs.delete(id);
      if(pynixId===id)pynixId=[...pynixTabs.keys()].at(-1)||null;
      if(!pynixTabs.size)createPynixTab();
      paintSessions();paintPynix();
     }else native({scope:'shell',action:'close',id});
    });
    item.append(button,close);sessions.appendChild(item);
   }
   requestAnimationFrame(updateOverflow);
  };
  const paintShell=()=>{
   const tab=shellTabs.get(activeId);
   system.log.textContent=tab?.buffer||'';
   system.log.scrollTop=system.log.scrollHeight;
  };
  const paintPynix=()=>{
   const tab=pynixTabs.get(pynixId);
   pynix.log.textContent=tab?.buffer||'';
   pynix.input.value=tab?.draft||'';
   pynix.log.scrollTop=pynix.log.scrollHeight;
  };
  function createPynixTab(){
   if(pynixTabs.has(pynixId))pynixTabs.get(pynixId).draft=pynix.input.value;
   const id='pynix-'+(++pynixSerial);
   pynixTabs.set(id,{label:pynixSerial===1?'Local':'Local '+pynixSerial,
    buffer:'PYNIX Console — type help for supported commands.\n',draft:''});
   pynixId=id;paintSessions();paintPynix();pynix.input.focus();
  }
  function createShell(shell){
   if(!shellTabs.size&&shellCreating)return;
   if(!shellTabs.size)shellCreating=true;
   native({scope:'shell',action:'create',shell});
  }
  newSession.addEventListener('click',()=>{
   if(scope==='pynix')createPynixTab();
   else if(scope==='system')createShell(defaultShell);
  });
  const menuDivider=host=>{
   const line=document.createElement('div');line.className='pynix-terminal-menu-divider';
   line.setAttribute('role','separator');host.appendChild(line);
  };
  let showToolbar=true,viewMode='Docked';
  const renderOptions=()=>{
   toolsPopup.replaceChildren();
   const option=(label,action)=>menuButton(toolsPopup,label,action);
   if(scope==='system'){
    option('Terminal Engine  ›',()=>{renderOptionsSub('Engine');tools.open=true;});
    option((showAiAgents?'✓ ':'')+'Show AI Agents in Toolbar',()=>{
     showAiAgents=!showAiAgents;renderOptions();
    });
    option('⚙ Settings',()=>{chevron.open=true;renderShellMenu(true);});
    menuDivider(toolsPopup);
   }
   option('Close All',()=>{
    if(scope==='pynix'){pynixTabs.clear();pynixId=null;createPynixTab();}
    else if(scope==='system'){
     for(const id of shellTabs.keys())native({scope:'shell',action:'close',id});
    }else setToolWindowVisible(false);
   });
   option((showToolbar?'✓ ':'')+'Show Toolbar',()=>{
    showToolbar=!showToolbar;
    newSession.hidden=!showToolbar||scope==='other';
    chevron.hidden=!showToolbar||scope!=='system';
    renderOptions();
   });
   option('View Mode  ›',()=>{renderOptionsSub('View Mode');tools.open=true;});
   option('Move to  ›',()=>{renderOptionsSub('Move to');tools.open=true;});
   option('Resize  ›',()=>{renderOptionsSub('Resize');tools.open=true;});
   menuDivider(toolsPopup);
   option('Remove from Sidebar',()=>{
    const rail=document.querySelectorAll('.workspace-mode .rail>.rail-item')[scope==='pynix'?5:4];
    if(rail)rail.hidden=true;
   });
  };
  let showAiAgents=true;
  const renderOptionsSub=kind=>{
   toolsPopup.replaceChildren();
   menuButton(toolsPopup,'← Back',()=>{renderOptions();tools.open=true;});
   tools.open=true;
   if(kind==='Engine'){
    for(const shell of ['zsh','bash'])
     menuButton(toolsPopup,(shell===defaultShell?'✓ ':'')+shell,()=>{
      defaultShell=shell;setDefaultShell(shell);
     });
   }else if(kind==='View Mode'){
    for(const mode of ['Docked','Floating'])
     menuButton(toolsPopup,(viewMode===mode?'✓ ':'')+mode,()=>{
      viewMode=mode;
      terminal.classList.toggle('pynix-terminal-floating',mode==='Floating');
      renderOptions();
     });
   }else if(kind==='Move to'){
    for(const side of ['Bottom','Top'])
     menuButton(toolsPopup,side,()=>{
      terminal.style.order=side==='Top'?'-1':'';
      renderOptions();
     });
   }else if(kind==='Resize'){
    for(const direction of ['Larger','Smaller'])
     menuButton(toolsPopup,direction,()=>{
      const height=terminal.getBoundingClientRect().height;
      terminal.style.setProperty('--terminal-height',Math.max(90,Math.min(window.innerHeight*.55,height+(direction==='Larger'?80:-80)))+'px');
      renderOptions();
     });
   }
  };
  const menuButton=(host,label,callback)=>{
   const button=document.createElement('button');button.type='button';
   button.setAttribute('role','menuitem');button.textContent=label;
   button.addEventListener('click',()=>{
    chevron.open=false;tools.open=false;callback();
   });host.appendChild(button);return button;
  };
  const setDefaultShell=shell=>{
   defaultShell=shell;
   try{localStorage.setItem('pynix.ide.defaultShell',shell);}catch(_){}
   renderShellMenu();
  };
  const renderShellMenu=(settings=false)=>{
   popup.replaceChildren();
   if(settings){
    menuButton(popup,'← Back',()=>{renderShellMenu();chevron.open=true;});
    for(const shell of ['bash','zsh'])
     menuButton(popup,(shell===defaultShell?'✓ ':'')+'Default: '+shell,
       ()=>setDefaultShell(shell));
    return;
   }
   for(const shell of ['bash','zsh'])menuButton(popup,shell,()=>createShell(shell));
   const divider=document.createElement('div');
   divider.className='pynix-terminal-dock-menu-separator';
   divider.setAttribute('role','separator');popup.appendChild(divider);
   menuButton(popup,'Settings',()=>{renderShellMenu(true);chevron.open=true;});
  };
  renderShellMenu();
  chevron.addEventListener('toggle',()=>{if(!chevron.open)renderShellMenu();});
  renderOptions();
  document.addEventListener('pointerdown',event=>{
   for(const details of [chevron,tools,overflow])
    if(details.open&&!details.contains(event.target))details.open=false;
  });
  document.addEventListener('keydown',event=>{
   if(event.key==='Escape'){
    for(const details of [chevron,tools,overflow])details.open=false;
   }
   if((event.metaKey||event.ctrlKey)&&!event.altKey&&event.key.toLowerCase()==='t'&&
     ['system','pynix'].includes(scope)&&isVisible()&&terminal.contains(document.activeElement)){
    event.preventDefault();if(scope==='pynix')createPynixTab();else createShell(defaultShell);
   }
  },true);
  system.input.addEventListener('keydown',event=>{
   if(event.key!=='Enter'||event.shiftKey)return;
   event.preventDefault();
   if(activeId&&system.input.value)native({
    scope:'shell',action:'write',id:activeId,data:system.input.value+'\n'
   });
   system.input.value='';
  });
  pynix.input.addEventListener('keydown',event=>{
   if(event.key!=='Enter'||event.shiftKey)return;
   event.preventDefault();
   const command=pynix.input.value.trim();
   if(!command||pynixBusy)return;
   pynix.input.value='';
   const tab=pynixTabs.get(pynixId);if(!tab)return;
   tab.draft='';tab.buffer+='pynix> '+command+'\n';paintPynix();
   pynixPending=pynixId;pynixBusy=true;
   native({scope:'pynix',action:'execute',command});
  });
  window.pynixTerminalNativeEvent=event=>{
   if(!event||typeof event!=='object')return;
   if(event.scope==='pynix'){
    pynixBusy=false;
    const tab=pynixTabs.get(pynixPending);
    if(tab)tab.buffer+=String(event.data||event.error||'')+'\n';
    pynixPending=null;if(scope==='pynix')paintPynix();
    return;
   }
   if(event.scope!=='shell')return;
   if(event.error){shellCreating=false;append(system.log,'[Terminal] '+event.error+'\n');return;}
   if(event.kind==='created'){
    shellCreating=false;serial++;
    const id=event.id;
    shellTabs.set(id,{shell:event.shell,label:serial===1?'Local':event.shell+' '+serial,buffer:''});
    activeId=id;paintSessions();paintShell();system.input.focus();
   }else if(event.kind==='closed'){
    shellTabs.delete(event.id);
    if(activeId===event.id)activeId=[...shellTabs.keys()].at(-1)||null;
    paintSessions();paintShell();
    if(!shellTabs.size&&scope==='system'&&isVisible())createShell(defaultShell);
   }else if(event.kind==='output'){
    const tab=shellTabs.get(event.id);if(!tab)return;
    tab.buffer=(tab.buffer+(event.data||'')).slice(-200000);
    if(event.id===activeId)paintShell();
    if(event.exited&&!tab.exited){
     tab.exited=true;tab.label+=' (exited)';paintSessions();
    }
   }
  };
  // Poll all sessions; inactive tabs still drain their own PTY buffers.
  setInterval(()=>{
   if(!shellTabs.size)return;
   for(const id of shellTabs.keys())native({scope:'shell',action:'poll',id});
  },160);
  toolTabs.addEventListener('click',event=>{
   if(event.target.closest('[role="tab"]')){
    scope='other';sync();
   }
  });
  let overflowResizePending=false;
  new ResizeObserver(()=>{
   if(overflowResizePending)return;
   overflowResizePending=true;
   requestAnimationFrame(()=>{overflowResizePending=false;updateOverflow();});
  }).observe(terminal);
  window.addEventListener('resize',updateOverflow);
  // Initial dock is collapsed, without taking space from Project/editor.
  setToolWindowVisible(false);
 }
"""
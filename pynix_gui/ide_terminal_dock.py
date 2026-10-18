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
  const gap=document.createElement('span');gap.className='pynix-terminal-dock-gap';
  const tools=document.createElement('details');tools.className='pynix-terminal-options-menu';
  const more=document.createElement('summary');
  more.className='pynix-terminal-dock-action';more.textContent='⋮';
  more.title='Tool Window Options';
  const toolsPopup=document.createElement('div');
  toolsPopup.className='pynix-terminal-dock-popup';toolsPopup.setAttribute('role','menu');
  tools.append(more,toolsPopup);
  const hide=document.createElement('button');hide.type='button';
  hide.className='pynix-terminal-dock-action pynix-terminal-dock-hide';
  hide.textContent='−';hide.title='Hide Tool Window';
  hide.setAttribute('aria-label','Hide Tool Window');
  hide.addEventListener('click',()=>setToolWindowVisible(false));
  header.append(title,sessions,newSession,chevron,gap,tools,hide);
  terminal.insertBefore(header,debugPanelBar.nextSibling);

  const hintStyle=document.createElement('style');
  hintStyle.textContent='.pynix-terminal-dock-bar [data-hint]{position:relative}.pynix-terminal-dock-bar [data-hint]:hover::after,.pynix-terminal-dock-bar [data-hint]:focus-visible::after{content:attr(data-hint);position:absolute;z-index:300;top:calc(100% + 7px);left:50%;transform:translateX(-50%);background:#383a40;border:1px solid #575a63;border-radius:6px;color:#e5e6ea;padding:6px 9px;font:12px/17px -apple-system,sans-serif;white-space:nowrap;pointer-events:none;box-shadow:0 4px 14px #0006}';
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
   newSession.hidden=scope==='other';
   newSession.dataset.hint=scope==='pynix'?'New Console Tab (⌘T)':'New Tab (⌘T)';
   paintSessions();
   chevron.hidden=scope!=='system';
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
     if(isPynix){pynixId=id;paintSessions();paintPynix();}
     else{activeId=id;paintSessions();paintShell();}
    });
    const close=document.createElement('button');close.type='button';
    close.className='pynix-terminal-session-close';close.textContent='×';
    close.setAttribute('aria-label','Close '+tab.label);
    close.addEventListener('click',()=>{
     if(isPynix){
      pynixTabs.delete(id);
      if(pynixId===id)pynixId=[...pynixTabs.keys()].at(-1)||null;
      if(!pynixTabs.size)createPynixTab();
      paintSessions();paintPynix();
     }else native({scope:'shell',action:'close',id});
    });
    item.append(button,close);sessions.appendChild(item);
   }
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
   pynixTabs.set(id,{label:pynixSerial===1?'PYNIX':'PYNIX '+pynixSerial,
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
  for(const [name,id] of [['Terminal','system'],['PYNIX Console','pynix']])
   menuButton(toolsPopup,name,()=>select(id));
  menuButton(toolsPopup,'Hide Tool Window',()=>setToolWindowVisible(false));
  document.addEventListener('pointerdown',event=>{
   for(const details of [chevron,tools])
    if(details.open&&!details.contains(event.target))details.open=false;
  });
  document.addEventListener('keydown',event=>{
   if(event.key==='Escape'){
    for(const details of [chevron,tools])details.open=false;
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
  // Initial dock is collapsed, without taking space from Project/editor.
  setToolWindowVisible(false);
 }
"""
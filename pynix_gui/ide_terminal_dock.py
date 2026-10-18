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
  newSession.textContent='+';newSession.title='New Tab (⌘T)';
  newSession.setAttribute('aria-label','New Terminal Tab');
  const chevron=document.createElement('details');
  chevron.className='pynix-terminal-shell-dropdown';
  const summary=document.createElement('summary');
  summary.className='pynix-terminal-dock-action pynix-terminal-shell-chevron';
  summary.setAttribute('aria-label','Choose Terminal Shell');
  summary.title='Choose Terminal Shell';
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
   title.textContent=scope==='pynix'?'PYNIX Terminal':scope==='system'?'Terminal':(
    selectedTool==='TERMINAL'?'Run':selectedTool[0]+selectedTool.slice(1).toLowerCase());
   sessions.hidden=scope!=='system';
   newSession.hidden=scope!=='system';
   chevron.hidden=scope!=='system';
   publish();
  };
  const select=id=>{
   if(!['system','pynix'].includes(id))return;
   if(scope===id&&isVisible()){setToolWindowVisible(false);return;}
   scope=id;setToolWindowVisible(true);
   if(id==='system'&&!shellTabs.size)createShell(defaultShell);
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
   for(const [id,tab] of shellTabs){
    const item=document.createElement('div');
    item.className='pynix-terminal-session-tab'+(id===activeId?' active':'');
    const button=document.createElement('button');button.type='button';
    button.className='pynix-terminal-session-select';button.textContent=tab.label;
    button.title=tab.shell;button.setAttribute('aria-selected',String(id===activeId));
    button.addEventListener('click',()=>{activeId=id;paintSessions();paintShell();});
    const close=document.createElement('button');close.type='button';
    close.className='pynix-terminal-session-close';close.textContent='×';
    close.setAttribute('aria-label','Close '+tab.label);
    close.addEventListener('click',()=>native({scope:'shell',action:'close',id}));
    item.append(button,close);sessions.appendChild(item);
   }
  };
  const paintShell=()=>{
   const tab=shellTabs.get(activeId);
   system.log.textContent=tab?.buffer||'';
   system.log.scrollTop=system.log.scrollHeight;
  };
  function createShell(shell){
   native({scope:'shell',action:'create',shell});
  }
  newSession.addEventListener('click',()=>createShell(defaultShell));
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
  for(const [name,id] of [['Terminal','system'],['PYNIX Terminal','pynix']])
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
     scope==='system'&&isVisible()&&terminal.contains(document.activeElement)){
    event.preventDefault();createShell(defaultShell);
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
   const command=pynix.input.value.trim();pynix.input.value='';
   if(!command||pynixBusy)return;
   append(pynix.log,'pynix> '+command+'\n');pynixBusy=true;
   native({scope:'pynix',action:'execute',command});
  });
  window.pynixTerminalNativeEvent=event=>{
   if(!event||typeof event!=='object')return;
   if(event.scope==='pynix'){
    pynixBusy=false;
    append(pynix.log,(event.data||event.error||'')+'\n');
    return;
   }
   if(event.scope!=='shell')return;
   if(event.error){append(system.log,'[Terminal] '+event.error+'\n');return;}
   if(event.kind==='created'){
    serial++;
    const id=event.id;
    shellTabs.set(id,{shell:event.shell,label:serial===1?'Local':event.shell+' '+serial,buffer:''});
    activeId=id;paintSessions();paintShell();system.input.focus();
   }else if(event.kind==='closed'){
    shellTabs.delete(event.id);
    if(activeId===event.id)activeId=[...shellTabs.keys()].at(-1)||null;
    paintSessions();paintShell();
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
# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Visual PyCharm-style terminal dock using the EXISTING V4 tool state."""

TERMINAL_DOCK_JS = r"""
 if(terminal&&toolTabs){
  const header=document.createElement('div');
  header.className='pynix-terminal-dock-bar';
  header.setAttribute('role','toolbar');
  header.setAttribute('aria-label','Terminal tool window');
  const title=document.createElement('span');
  title.className='pynix-terminal-dock-title';title.textContent='Terminal';
  const session=document.createElement('div');
  session.className='pynix-terminal-dock-session';
  const local=document.createElement('span');local.textContent='Local';
  const closeSession=document.createElement('button');
  closeSession.type='button';closeSession.textContent='×';
  closeSession.className='pynix-terminal-dock-action';
  closeSession.title='Hide Terminal';closeSession.setAttribute('aria-label','Hide Terminal');
  closeSession.addEventListener('click',()=>setToolWindowVisible(false));
  session.append(local,closeSession);
  const add=document.createElement('button');
  add.type='button';add.textContent='+';add.disabled=true;
  add.className='pynix-terminal-dock-action';
  add.title='Multiple terminal sessions not implemented';
  add.setAttribute('aria-label','New Terminal (unavailable)');
  const dropdown=(className,glyph,label)=>{
   const details=document.createElement('details');details.className=className;
   const summary=document.createElement('summary');
   summary.className='pynix-terminal-dock-action';summary.textContent=glyph;
   summary.title=label;summary.setAttribute('aria-label',label);
   const popup=document.createElement('div');
   popup.className='pynix-terminal-dock-popup';popup.setAttribute('role','menu');
   details.append(summary,popup);
   details.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&details.open){
     event.preventDefault();details.open=false;summary.focus();
    }
   });
   return {details,popup};
  };
  const views=[['Terminal','TERMINAL'],['Problems','PROBLEMS'],
   ['Output','OUTPUT'],['Debug Console','DEBUG CONSOLE']];
  const viewMenu=dropdown('pynix-terminal-view-menu','⌄','Select Tool Window');
  const options=dropdown('pynix-terminal-options-menu','⋮','Terminal Options');
  const choose=name=>{
   const tab=[...toolTabs.querySelectorAll('strong,span')]
     .find(node=>node.textContent.trim()===name);
   tab?.click();
  };
  for(const [label,name] of views)for(const menu of [viewMenu,options]){
   const item=document.createElement('button');item.type='button';
   item.textContent=label;item.setAttribute('role','menuitem');
   item.addEventListener('click',()=>{
    viewMenu.details.open=false;options.details.open=false;choose(name);
   });
   menu.popup.appendChild(item);
  }
  const hideOption=document.createElement('button');
  hideOption.type='button';hideOption.textContent='Hide Tool Window';
  hideOption.setAttribute('role','menuitem');
  hideOption.addEventListener('click',()=>{
   options.details.open=false;setToolWindowVisible(false);
  });
  options.popup.appendChild(hideOption);
  const agents=document.createElement('button');
  agents.type='button';agents.className='pynix-terminal-dock-agents';
  agents.textContent='AI Agents⌄';agents.disabled=true;
  agents.title='AI Agents are not yet available';
  const spacer=document.createElement('span');spacer.className='pynix-terminal-dock-gap';
  const hide=document.createElement('button');
  hide.type='button';hide.textContent='−';hide.title='Hide Tool Window';
  hide.className='pynix-terminal-dock-action pynix-terminal-dock-hide';
  hide.setAttribute('aria-label','Hide Tool Window');
  hide.addEventListener('click',()=>setToolWindowVisible(false));
  header.append(title,session,add,viewMenu.details,spacer,agents,options.details,hide);
  terminal.insertBefore(header,debugPanelBar.nextSibling);
  const railTerminal=document.querySelectorAll('.workspace-mode .rail>.rail-item')[4];
  const visible=()=>!terminal.classList.contains('pynix-tool-window-collapsed');
  const sync=()=>{
   const open=visible(),selected=selectedTool==='TERMINAL';
   railTerminal?.classList.toggle('active',open&&selected);
   railTerminal?.setAttribute('aria-pressed',String(open&&selected));
   railTerminal?.setAttribute('aria-expanded',String(open));
   title.textContent=selected?'Terminal':
     (views.find(pair=>pair[1]===selectedTool)?.[0]||'Terminal');
   session.hidden=!selected;
   for(const tab of toolTabs.querySelectorAll('[role="tab"]'))tab.tabIndex=-1;
  };
  railTerminal?.setAttribute('role','button');
  railTerminal?.setAttribute('tabindex','0');
  railTerminal?.setAttribute('aria-label','Toggle Terminal tool window');
  railTerminal?.setAttribute('title','Terminal (⌘⌥4 / Ctrl+Alt+4)');
  railTerminal?.addEventListener('click',()=>{
   if(visible()&&selectedTool==='TERMINAL')setToolWindowVisible(false);
   else choose('TERMINAL');
  });
  railTerminal?.addEventListener('keydown',event=>{
   if(event.key==='Enter'||event.key===' '){
    event.preventDefault();railTerminal.click();
   }
  });
  toolTabs.addEventListener('click',sync);
  document.addEventListener('pointerdown',event=>{
   for(const menu of [viewMenu,options])
    if(menu.details.open&&!menu.details.contains(event.target))menu.details.open=false;
  });
  window.pynixTerminalDock={sync,show:()=>choose('TERMINAL'),
   hide:()=>setToolWindowVisible(false),toggle:()=>railTerminal?.click()};
  // No dock panel consumes editor height before explicitly requested.
  setToolWindowVisible(false);
 }
"""
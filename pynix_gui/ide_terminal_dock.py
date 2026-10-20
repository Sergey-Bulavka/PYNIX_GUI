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
  summary.innerHTML='<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M4.5 6.25 8 9.75 11.5 6.25" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const popup=document.createElement('div');popup.className='pynix-terminal-dock-popup';
  popup.setAttribute('role','menu');
  chevron.append(summary,popup);
  // Use an ordinary button, independent of <details>/summary WebKit styling.
  const overflow=document.createElement('div');
  overflow.className='pynix-tab-overflow-control';
  const overflowToggle=document.createElement('button');
  overflowToggle.type='button';
  overflowToggle.className='pynix-terminal-dock-action pynix-tab-overflow-trigger';
  // Same vector chevron for Shell and Hidden Tabs: matching geometry and centering.
  overflowToggle.innerHTML='<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M4.5 6.25 8 9.75 11.5 6.25" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  overflowToggle.setAttribute('aria-label','More Tabs');
  overflowToggle.setAttribute('aria-haspopup','menu');
  overflowToggle.setAttribute('aria-expanded','false');
  overflowToggle.dataset.hint='More Tabs';
  const overflowPopup=document.createElement('div');
  overflowPopup.className='pynix-terminal-dock-popup pynix-tab-overflow-popup';
  overflowPopup.setAttribute('role','menu');
  overflowPopup.hidden=true;
  const closeOverflow=()=>{
   overflowPopup.hidden=true;
   overflowToggle.setAttribute('aria-expanded','false');
  };
  overflowToggle.addEventListener('click',()=>{
   if(!overflow.classList.contains('has-hidden-tabs'))return;
   const nextOpen=overflowPopup.hidden;
   overflowPopup.hidden=!nextOpen;
   overflowToggle.setAttribute('aria-expanded',String(nextOpen));
  });
  overflow.append(overflowToggle,overflowPopup);
  const gap=document.createElement('span');gap.className='pynix-terminal-dock-gap';
  // Run uses the same bottom dock without becoming a shell or PYNIX console.
  const runActions=document.createElement('div');
  runActions.className='pynix-run-dock-actions';
  runActions.hidden=true;
  const dockRerun=document.createElement('button');
  dockRerun.type='button';dockRerun.className='pynix-run-dock-rerun';
  dockRerun.title='Run / Rerun current configuration';
  dockRerun.setAttribute('aria-label','Run or rerun');
  dockRerun.innerHTML='<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M12.7 7A5 5 0 1 0 13 9" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M13 3.5V7.5H9" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const dockRunStop=document.createElement('button');
  dockRunStop.type='button';dockRunStop.className='pynix-run-dock-stop';
  dockRunStop.title='Stop running process';dockRunStop.disabled=true;
  dockRunStop.setAttribute('aria-label','Stop run');
  dockRunStop.innerHTML='<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><rect x="4" y="4" width="8" height="8" rx="1.25" fill="currentColor"/></svg>';
  let hadRun=false;
  dockRerun.addEventListener('click',()=>{
   document.querySelector(hadRun?'.pynix-restart-action':'.pynix-run-action')?.click();
  });
  dockRunStop.addEventListener('click',()=>{
   document.querySelector('.pynix-stop-action')?.click();
  });
  runActions.append(dockRerun,dockRunStop);
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
  header.append(title,sessions,newSession,chevron,gap,overflow,tools,hide);
  header.insertBefore(runActions,gap);
  terminal.insertBefore(header,debugPanelBar.nextSibling);

  const hintStyle=document.createElement('style');
  hintStyle.textContent='.pynix-terminal-dock-bar [data-hint]{position:relative}.pynix-terminal-dock-bar [data-hint]:hover::after,.pynix-terminal-dock-bar [data-hint]:focus-visible::after{content:attr(data-hint);position:absolute;z-index:300;top:calc(100% + 7px);left:50%;transform:translateX(-50%);background:#383a40;border:1px solid #575a63;border-radius:6px;color:#e5e6ea;padding:6px 9px;font:12px/17px -apple-system,sans-serif;white-space:nowrap;pointer-events:none;box-shadow:0 4px 14px #0006}';
  hintStyle.textContent+=`
  .pynix-terminal-dock-bar{display:flex;align-items:center;min-width:0}
  .pynix-terminal-dock-title,.pynix-terminal-new,
  .pynix-terminal-options-menu,.pynix-terminal-dock-hide{flex-shrink:0}
  .workspace-mode .integrated-terminal .pynix-tab-overflow-control{
   box-sizing:border-box!important;position:relative!important;
   flex:0 0 27px!important;width:27px!important;min-width:27px!important;
   display:flex!important;align-items:center!important;justify-content:center!important;
   visibility:hidden!important;pointer-events:none!important
  }
  /* Keep the class selector separate: unsupported :has must never
     invalidate the primary visibility rule on older WebKit builds. */
  .workspace-mode .integrated-terminal .pynix-tab-overflow-control.has-hidden-tabs{
   display:flex!important;visibility:visible!important;
   opacity:1!important;pointer-events:auto!important
  }
  .workspace-mode .integrated-terminal .pynix-terminal-dock-bar:has(.pynix-terminal-session-tab[hidden]) .pynix-tab-overflow-control{
   display:flex!important;visibility:visible!important;
   opacity:1!important;pointer-events:auto!important
  }
  .workspace-mode .pynix-tab-overflow-trigger,
  .workspace-mode .pynix-terminal-shell-chevron{
   box-sizing:border-box!important;
   width:27px!important;height:27px!important;min-width:27px!important;
   display:inline-flex!important;align-items:center!important;justify-content:center!important;
   padding:0!important;margin:0!important;line-height:0!important;
   color:#c6c8d0!important
  }
  .workspace-mode .pynix-tab-overflow-trigger{
   opacity:1!important;visibility:visible!important;pointer-events:auto!important
  }
  .workspace-mode .pynix-tab-overflow-trigger svg,
  .workspace-mode .pynix-terminal-shell-chevron svg{
   display:block!important;width:16px!important;height:16px!important;
   min-width:16px!important;min-height:16px!important;flex:0 0 16px!important;
   margin:0!important;vertical-align:middle!important
  }
  .workspace-mode .pynix-tab-overflow-popup{
   position:absolute!important;top:calc(100% + 7px)!important;
   right:0!important;left:auto!important;z-index:900!important;
   min-width:175px!important;max-height:320px;overflow-y:auto
  }
  .workspace-mode .pynix-tab-overflow-popup[hidden]{display:none!important}
  .workspace-mode .pynix-tab-overflow-popup:not([hidden]){display:block!important}
  .pynix-tab-overflow-popup .pynix-overflow-entry{display:block;width:100%;text-align:left}
  .workspace-mode .pynix-run-dock-actions{
   display:inline-flex!important;align-items:center!important;gap:4px!important;
   flex:0 0 auto!important;margin-left:6px!important
  }
  .workspace-mode .pynix-run-dock-actions[hidden]{display:none!important}
  .workspace-mode .pynix-run-dock-actions button{
   box-sizing:border-box;width:26px;height:26px;min-width:26px;
   display:flex;align-items:center;justify-content:center;
   border:0;background:transparent;color:#c1c5cd;border-radius:5px;cursor:pointer
  }
  .workspace-mode .pynix-run-dock-actions button:disabled{opacity:.4;cursor:default}
  .workspace-mode .pynix-run-dock-actions button:hover:not(:disabled){background:#3a3d45}
  .workspace-mode .pynix-run-dock-actions svg{display:block;flex:0 0 16px}
  .pynix-terminal-new{order:0}
  .pynix-terminal-session-tab{flex-shrink:0}
  .pynix-terminal-session-tab[hidden]{display:none!important}
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
   const detail={scope,tool:selectedTool,visible:isVisible()};
   window.dispatchEvent(new CustomEvent('pynix:terminal-change',{detail}));
  };
  __PYNIX_PACKAGES_DOCK__
  __PYNIX_SERVICES_DOCK__
  const sync=()=>{
   const visible=isVisible();
   system.panel.hidden=!visible||scope!=='system';
   pynix.panel.hidden=!visible||scope!=='pynix';
   toolConsole.hidden=scope!=='other';
   packagesPane.hidden=!(visible&&scope==='packages');
   servicesPane.hidden=!(visible&&scope==='services');
   header.hidden=visible&&(scope==='packages'||scope==='services');
   const legacy=document.querySelectorAll('.workspace-mode .rail>.rail-item')[4];
   legacy?.classList.toggle('active',visible&&scope==='system');
   legacy?.setAttribute('aria-pressed',String(visible&&scope==='system'));
   title.textContent=scope==='pynix'?'PYNIX Console':scope==='system'?'Terminal':(
    selectedTool==='TERMINAL'?'Run':selectedTool[0]+selectedTool.slice(1).toLowerCase());
   sessions.hidden=scope==='other';
   newSession.hidden=scope==='other'||!showToolbar;
   newSession.dataset.hint=scope==='pynix'?'New Console Tab (⌘T)':'New Tab (⌘T)';
   runActions.hidden=!(scope==='other'&&selectedTool==='TERMINAL');
   paintSessions();
   chevron.hidden=scope!=='system'||!showToolbar;
   renderOptions();
   publish();
  };
  const select=id=>{
   if(!['system','pynix','packages','services'].includes(id))return;
   if(scope===id&&isVisible()){setToolWindowVisible(false);return;}
   scope=id;setToolWindowVisible(true);
   if(id==='packages')packagesOnShow();
   if(id==='services')servicesOnShow();
   if(id==='system'&&!shellTabs.size)createShell(defaultShell);
   if(id==='pynix'&&!pynixTabs.size)createPynixTab();
   if(id==='system')system.input.focus();
   else if(id==='pynix')pynix.input.focus();
  };
  const showRun=()=>{
   // Run is a bottom tool window. Never click a left rail proxy: its
   // gallery handler replaces the Project explorer DOM.
   scope='other';
   activateToolView('TERMINAL');
   if(toolTabs){
    for(const tab of toolTabs.children){
     const selected=tab.textContent.trim()==='TERMINAL'&&tab.getAttribute('role')==='tab';
     if(tab.getAttribute('role')==='tab'){
      tab.classList.toggle('pynix-active-tab',selected);
      tab.setAttribute('aria-selected',String(selected));
     }
    }
   }
   debugPanelBar.hidden=true;
   setToolWindowVisible(true);
  };
  const showProblems=()=>{
   // Problems is an independent tool view, not the system Terminal/Run buffer.
   scope='other';
   activateToolView('PROBLEMS');
   if(toolTabs){
    for(const tab of toolTabs.children){
     if(tab.getAttribute('role')!=='tab')continue;
     const active=tab.textContent.trim()==='PROBLEMS';
     tab.classList.toggle('pynix-active-tab',active);
     tab.setAttribute('aria-selected',String(active));
    }
   }
   debugPanelBar.hidden=true;
   setToolWindowVisible(true);
  };
  const showGit=()=>{
   scope='other';
   activateToolView('GIT');
   if(toolTabs){
    for(const tab of toolTabs.children){
     if(tab.getAttribute('role')!=='tab')continue;
     tab.classList.remove('pynix-active-tab');
     tab.setAttribute('aria-selected','false');
    }
   }
   debugPanelBar.hidden=true;
   setToolWindowVisible(true);
  };
  const toggleGit=()=>{
   if(scope==='other'&&selectedTool==='GIT'&&isVisible())setToolWindowVisible(false);
   else showGit();
  };
  const toggleProblems=()=>{
   if(scope==='other'&&selectedTool==='PROBLEMS'&&isVisible())setToolWindowVisible(false);
   else showProblems();
  };
  const toggleRun=()=>{
   if(scope==='other'&&selectedTool==='TERMINAL'&&isVisible())
    setToolWindowVisible(false);
   else showRun();
  };
  const togglePackages=()=>select('packages');
  const toggleServices=()=>select('services');
  window.pynixTerminalDock={
   sync,select,showRun,toggleRun,showProblems,toggleProblems,showGit,toggleGit,togglePackages,toggleServices,
   state:()=>({scope,tool:selectedTool,visible:isVisible()}),
   tabLayout:()=>({...tabOverflowDebug}),
   setRunState:running=>{
    if(running)hadRun=true;
    dockRerun.disabled=!!running;
    dockRunStop.disabled=!running;
   },
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

  // The strip and the right-hand actions share a flex row. The browser can
  // clip the strip *outside* its own reported viewport on WKWebView, so relying
  // on scrollWidth/clientWidth or individual bounding rects alone is unsound.
  // Reserve the fixed sibling widths explicitly and clamp the strip itself.
  // JetBrains-style tab overflow: select the tabs that fit in the visible
  // strip, then put every other tab in the right-hand dropdown. Never infer
  // missing tabs from scrollWidth or stale scrolling coordinates.
  let tabOverflowDebug={};
  const updateOverflow=()=>{
   const setOverflow=hiddenTabs=>{
    const hasHidden=hiddenTabs.length>0;
    // The class drives !important CSS in WKWebView, avoiding conflicting
    // inline visibility state from previous layout passes.
    overflow.classList.toggle('has-hidden-tabs',hasHidden);
    header.classList.toggle('has-overflow-tabs',hasHidden);
    // Keep the chevron's slot stable while unconditionally applying its
    // computed state. Both the class and :has([hidden]) independently reveal it.
    overflow.style.setProperty('display','flex','important');
    overflow.style.setProperty('visibility',hasHidden?'visible':'hidden','important');
    overflow.style.setProperty('opacity',hasHidden?'1':'0','important');
    overflow.style.setProperty('pointer-events',hasHidden?'auto':'none','important');
    if(!hasHidden)closeOverflow();
    header.dataset.overflowTabs=String(hasHidden);
    overflowToggle.dataset.hint='More Tabs ('+hiddenTabs.length+')';
    overflowToggle.setAttribute('aria-label',
      'Show Hidden Tabs ('+hiddenTabs.length+')');
   };
   if(scope==='other'||sessions.hidden){
    overflowPopup.replaceChildren();setOverflow([]);return;
   }
   const tabs=[...(scope==='pynix'?pynixTabs:shellTabs).entries()];
   const items=[...sessions.children];
   if(!items.length){
    overflowPopup.replaceChildren();setOverflow([]);return;
   }
   // Reset the preceding pass; there must be exactly one size and one
   // visibility decision for each session at this point.
   for(const item of items)item.hidden=false;
   for(const property of ['width','flex','max-width'])
    sessions.style.removeProperty(property);
   sessions.scrollLeft=0;
   const widths=items.map(item=>item.getBoundingClientRect().width);
   const innerGap=parseFloat(getComputedStyle(sessions).columnGap)||0;
   const headerStyle=getComputedStyle(header);
   const outerGap=parseFloat(headerStyle.columnGap)||0;
   const padding=(parseFloat(headerStyle.paddingLeft)||0)+
                 (parseFloat(headerStyle.paddingRight)||0);
   const controls=[...header.children].filter(el=>
    el!==sessions&&getComputedStyle(el).display!=='none');
   const fixed=controls.reduce((total,el)=>
    total+(el===gap?0:el.getBoundingClientRect().width),0);
   const available=Math.max(0,header.clientWidth-padding-fixed-
     outerGap*controls.length);
   const active=scope==='pynix'?pynixId:activeId;
   const activeIndex=Math.max(0,tabs.findIndex(([id])=>id===active));
   const shown=new Set();
   let filled=0;
   const include=i=>{
    if(i<0||i>=items.length||shown.has(i))return false;
    const increment=widths[i]+(shown.size?innerGap:0);
    if(shown.size&&filled+increment>available+0.5)return false;
    shown.add(i);filled+=increment;return true;
   };
   include(activeIndex);
   for(let i=activeIndex-1;i>=0;i--)if(!include(i))break;
   for(let i=activeIndex+1;i<items.length;i++)if(!include(i))break;
   const hidden=[];
   items.forEach((item,i)=>{
    item.hidden=!shown.has(i);
    if(item.hidden)hidden.push(i);
   });
   // Shrink the tab viewport to the visible subset: the plus button stays
   // adjacent to the last tab, and the gap pins More/Options/Hide to the right.
   const stripWidth=Math.min(available,Math.max(0,filled));
   for(const [prop,value] of [
    ['width',stripWidth+'px'],['max-width',stripWidth+'px'],
    ['flex','0 0 '+stripWidth+'px']
   ])sessions.style.setProperty(prop,value,'important');
   overflowPopup.replaceChildren();
   for(const i of hidden){
    const [id,tab]=tabs[i];
    if(!tab)continue;
    const entry=document.createElement('button');
    entry.type='button';
    entry.className='pynix-overflow-entry';
    entry.dataset.sessionId=id;
    entry.setAttribute('role','menuitem');
    entry.textContent=tab.label;
    entry.addEventListener('click',()=>{
     closeOverflow();
     if(scope==='pynix'){
      if(pynixTabs.has(pynixId))
       pynixTabs.get(pynixId).draft=pynix.input.value;
      pynixId=id;paintSessions();paintPynix();
     }else{
      activeId=id;paintSessions();paintShell();
     }
    });
    overflowPopup.appendChild(entry);
   }
   setOverflow(hidden);
   // In a native WebKit render pass an ancestor may clip the strip even
   // when a width estimate said all items fit. A fully missing earlier tab
   // must still make the overflow control visible.
   requestAnimationFrame(()=>{
    if(scope==='other'||sessions.hidden)return;
    const hiddenNow=[...sessions.children].map((el,i)=>({el,i})).filter(({el})=>{
     const rect=el.getBoundingClientRect();
     const box=sessions.getBoundingClientRect();
     return el.hidden||rect.right<box.left-0.5||rect.left>box.right+0.5;
    });
    // Reconcile the popup itself, not merely its button. Some WebKit builds
    // report the initial flex width before the last layout pass.
    const existing=new Set([...overflowPopup.children].map(el=>el.dataset.sessionId));
    for(const {i} of hiddenNow){
     const [id,tab]=tabs[i]||[];
     if(!id||existing.has(id))continue;
     const entry=document.createElement('button');
     entry.type='button';entry.className='pynix-overflow-entry';
     entry.dataset.sessionId=id;
     entry.setAttribute('role','menuitem');
     entry.textContent=tab.label;
     entry.addEventListener('click',()=>{
      closeOverflow();
      if(scope==='pynix'){
       if(pynixTabs.has(pynixId))
        pynixTabs.get(pynixId).draft=pynix.input.value;
       pynixId=id;paintSessions();paintPynix();
      }else{activeId=id;paintSessions();paintShell();}
     });
     overflowPopup.appendChild(entry);existing.add(id);
    }
    if(hiddenNow.length){
     setOverflow([...overflowPopup.children]);
     tabOverflowDebug.hidden=[...overflowPopup.children].map(el=>el.textContent);
     tabOverflowDebug.arrowVisibility=getComputedStyle(overflow).visibility;
    }
   });
   tabOverflowDebug={
    scope,tabs:tabs.length,available,filled,activeIndex,
    shown:[...shown].sort((a,b)=>a-b),
    hidden:hidden.map(i=>tabs[i][1].label),
    arrowClass:overflow.className,
    arrowDisplay:getComputedStyle(overflow).display,
    arrowVisibility:getComputedStyle(overflow).visibility,
    arrowWidth:overflow.getBoundingClientRect().width,
    tabWidth:sessions.getBoundingClientRect().width
   };
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
   pynixTabs.set(id,{label:pynixTabs.size===0?'Local':'Local '+pynixSerial,
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
   option('Tab Layout Diagnostics',()=>{
    const info=window.pynixTerminalDock.tabLayout();
    const labels=[...sessions.children].map(el=>({
     label:el.textContent.trim(),hidden:el.hidden,
     left:Math.round(el.getBoundingClientRect().left),
     right:Math.round(el.getBoundingClientRect().right)
    }));
    const report=JSON.stringify({...info,labels,arrowDisplay:getComputedStyle(overflow).display,
     arrowVisibility:getComputedStyle(overflow).visibility,hiddenAttribute:overflow.hasAttribute('hidden')});
    if(scope==='pynix')pynix.log.textContent+='\n[Tab layout] '+report+'\n';
    else system.log.textContent+='\n[Tab layout] '+report+'\n';
   });
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
   for(const details of [chevron,tools])
    if(details.open&&!details.contains(event.target))details.open=false;
   if(!overflow.contains(event.target))closeOverflow();
  });
  document.addEventListener('keydown',event=>{
   if(event.key==='Escape'){
    for(const details of [chevron,tools])details.open=false;
    closeOverflow();
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
    shellTabs.set(id,{shell:event.shell,label:shellTabs.size===0?'Local':'Local '+serial,buffer:''});
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
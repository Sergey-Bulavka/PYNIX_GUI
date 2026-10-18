"""Real V4 tab strip controls, embedded in workspace bootstrap IIFE."""

from .ide_editor_tab_advanced import TAB_ADVANCED_JS

TAB_CONTROL_JS = r"""
 const planTabOverflow=(widths,available,active)=>{
  if(widths.reduce((a,b)=>a+b,0)<=available)return [];
  const order=widths.map((_,i)=>i).sort((a,b)=>Math.abs(a-active)-Math.abs(b-active)||a-b);
  const keep=new Set();let left=Math.max(0,available);
  for(const i of order){
   if(i===active){keep.add(i);left=Math.max(0,left-Math.min(widths[i],available));}
   else if(widths[i]<=left){keep.add(i);left-=widths[i];}
  }
  return widths.map((_,i)=>i).filter(i=>!keep.has(i));
 };
 window.pynixPlanTabOverflow=planTabOverflow;
 const tabControls=(()=>{
  const strip=document.createElement('div');strip.className='pynix-tabs-strip';
  const actions=document.createElement('div');actions.className='pynix-tabs-actions';
  const button=(cls,label,svg)=>{
   const el=document.createElement('button');el.type='button';
   el.className='pynix-tabs-action '+cls;el.dataset.pynixTooltip=label;
   el.setAttribute('aria-label',label);el.setAttribute('aria-haspopup','menu');
   el.setAttribute('aria-expanded','false');el.innerHTML=svg;return el;
  };
  const hiddenButton=button('pynix-tabs-hidden','Show Hidden Tabs',
    '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="m5 7 5 5 5-5" stroke="currentColor" fill="none" stroke-width="1.6"/></svg>');
  const moreButton=button('pynix-tabs-more','Recent Files, Tab Actions, and More',
    '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="4" r="1.5" fill="currentColor"/><circle cx="10" cy="10" r="1.5" fill="currentColor"/><circle cx="10" cy="16" r="1.5" fill="currentColor"/></svg>');
  hiddenButton.hidden=true;actions.append(hiddenButton,moreButton);
  tabs.replaceChildren(strip,actions);
  const popup=document.createElement('div');popup.className='pynix-tabs-popup';
  popup.setAttribute('role','menu');popup.hidden=true;document.body.appendChild(popup);
  const recent=[],closed=[],locations=[];let hidden=[],menu=null,frame=0,bulk=[];
  const recordLocation=()=>{
   if(!current||!editorInput.value)return;
   const start=editorInput.selectionStart||0;
   const line=editorInput.value.slice(0,start).split('\n').length;
   if(locations[0]?.name===current&&locations[0]?.line===line)return;
   locations.unshift({name:current,line});if(locations.length>50)locations.pop();
  };
  editorInput.addEventListener('keyup',recordLocation);
  editorInput.addEventListener('mouseup',recordLocation);
  const visited=name=>{
   const i=recent.indexOf(name);if(i>=0)recent.splice(i,1);
   recent.unshift(name);if(recent.length>50)recent.pop();
  };
  const dismiss=()=>{
   menu=null;popup.hidden=true;
   hiddenButton.setAttribute('aria-expanded','false');
   moreButton.setAttribute('aria-expanded','false');
  };
  const position=()=>{
   if(!menu)return;
   const rect=(menu==='hidden'?hiddenButton:moreButton).getBoundingClientRect();
   popup.style.left=Math.max(5,Math.min(rect.right-popup.offsetWidth,
    document.documentElement.clientWidth-popup.offsetWidth-5))+'px';
   popup.style.top=Math.max(5,Math.min(rect.bottom+5,
    document.documentElement.clientHeight-popup.offsetHeight-5))+'px';
  };
  const divider=()=>{
   const line=document.createElement('div');line.className='pynix-tabs-divider';
   line.setAttribute('role','separator');popup.appendChild(line);
  };
  const row=(label,run,{disabled=false,shortcut='',icon='',active=false}={})=>{
   const host=document.createElement('div');
   host.className='pynix-tabs-menu-row'+(active?' active':'');
   const el=document.createElement('button');el.type='button';
   el.className='pynix-tabs-menu-item';el.setAttribute('role','menuitem');
   el.disabled=disabled;if(disabled)el.title='Not yet implemented';
   if(icon){
    const img=document.createElement('span');img.className='pynix-tab-file-glyph file-'+icon;
    img.innerHTML=fileIconMarkup(icon);img.setAttribute('aria-hidden','true');el.appendChild(img);
   }
   const name=document.createElement('span');name.className='pynix-tabs-menu-label';
   name.textContent=label;el.appendChild(name);
   if(shortcut){
    const hint=document.createElement('span');hint.className='pynix-tabs-menu-shortcut';
    hint.textContent=shortcut;el.appendChild(hint);
   }
   el.addEventListener('click',()=>{if(disabled)return;dismiss();run?.();});
   for(const type of ['pointerenter','focus'])el.addEventListener(type,()=>{
    popup.querySelectorAll('.pynix-tabs-menu-row.pynix-keyboard-selected')
      .forEach(other=>other.classList.remove('pynix-keyboard-selected'));
    host.classList.add('pynix-keyboard-selected');
   });
   host.appendChild(el);popup.appendChild(host);return host;
  };
  const nextBulk=()=>{
   while(bulk.length&&!openTabs.includes(bulk[0]))bulk.shift();
   if(bulk.length)requestCloseTab(bulk.shift());
  };
  const startBulk=names=>{bulk=names.filter(x=>openTabs.includes(x));nextBulk();};
  __PYNIX_ADVANCED_TABS__
  const paint=()=>{
   popup.replaceChildren();
   if(menu==='hidden'){
    for(const name of hidden){
     const file=byName.get(name);
     const item=row(name.split('/').pop()+(file?.dirty?' *':''),()=>show(name),
       {icon:file?.icon||'file',active:name===current});
     item.firstChild.title=name;
     const close=document.createElement('button');close.type='button';
     close.className='pynix-tabs-menu-close';close.textContent='×';
     close.setAttribute('aria-label','Close '+name);
     close.addEventListener('click',()=>{dismiss();requestCloseTab(name);});
     item.appendChild(close);
    }return;
   }
   if(menu==='locations'){
    const entries=locations.filter(x=>byName.has(x.name)).slice(0,30);
    if(!entries.length)row('No recent locations',null,{disabled:true});
    for(const entry of entries)
     row(entry.name+':'+entry.line,()=>{
      show(entry.name);
      requestAnimationFrame(()=>selectNavigationLocation({
       source:entry.name,line:entry.line,column:1
      }));
     },{icon:byName.get(entry.name)?.icon||'file'});
    return;
   }
   if(menu==='bookmarks'){paintBookmarks();return;}
   if(menu==='preferences'){paintPreferences();return;}
   if(menu==='recent'){
    const entries=recent.filter(x=>byName.has(x)).slice(0,30);
    if(!entries.length)row('No recent files',null,{disabled:true});
    for(const name of entries)
     row(name,()=>show(name),{icon:byName.get(name)?.icon||'file',active:name===current});
    return;
   }
   row('Recent Files',()=>openMenu('recent'),{shortcut:'⌘E'});
   row('Recent Locations',()=>openMenu('locations'),{shortcut:'⇧⌘E'});
   row('Go to File...',()=>window.pynixOpenSearchEverywhere?.(),{shortcut:'⇧⌘O'});
   divider();
   row('Close All Tabs',()=>startBulk([...openTabs]),{disabled:!openTabs.length});
   row('Close Unmodified Tabs',()=>startBulk(openTabs.filter(x=>!byName.get(x)?.dirty)),
     {disabled:!openTabs.some(x=>!byName.get(x)?.dirty)});
   row('Reopen Closed Tab',()=>{
    const name=closed.find(x=>byName.has(x)&&!openTabs.includes(x));if(name)show(name);
   },{disabled:!closed.some(x=>byName.has(x)&&!openTabs.includes(x))});
   divider();
   row('Bookmark Open Tabs...',bookmarkOpenTabs,{disabled:!openTabs.length});
   if(bookmarked.length)row('Open Bookmarked Tabs...',()=>openMenu('bookmarks'));
   divider();
   row('Configure Editor Tabs...',()=>openMenu('preferences'));
   row(pref.minimap?'Hide Minimap':'Show Minimap',toggleMinimap);
  };
  const openMenu=kind=>{
   if(kind==='hidden'&&!hidden.length)return;
   menu=kind;paint();popup.hidden=false;
   hiddenButton.setAttribute('aria-expanded',String(kind==='hidden'));
   moreButton.setAttribute('aria-expanded',String(kind!=='hidden'));
   position();popup.querySelector('.pynix-tabs-menu-item:not(:disabled)')?.focus();
  };
  hiddenButton.addEventListener('click',()=>menu==='hidden'?dismiss():openMenu('hidden'));
  moreButton.addEventListener('click',()=>menu==='actions'?dismiss():openMenu('actions'));
  document.addEventListener('pointerdown',event=>{
   if(menu&&!popup.contains(event.target)&&!hiddenButton.contains(event.target)
      &&!moreButton.contains(event.target))dismiss();
  },true);
  document.addEventListener('keydown',event=>{
   if(event.key==='Escape'&&menu){
    event.preventDefault();event.stopPropagation();
    const target=menu==='hidden'?hiddenButton:moreButton;dismiss();target.focus();return;
   }
   if(event.metaKey&&!event.ctrlKey&&!event.altKey){
    const key=event.key.toLowerCase();
    if(key==='e'){
     event.preventDefault();openMenu(event.shiftKey?'locations':'recent');return;
    }
    if(key==='o'&&event.shiftKey){
     event.preventDefault();dismiss();window.pynixOpenSearchEverywhere?.();return;
    }
   }
   if(!menu||!popup.contains(document.activeElement))return;
   const items=[...popup.querySelectorAll('.pynix-tabs-menu-item:not(:disabled)')];
   if(!items.length)return;
   if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
    event.preventDefault();const index=items.indexOf(document.activeElement);
    const next=event.key==='Home'?0:event.key==='End'?items.length-1:
     (index+(event.key==='ArrowDown'?1:-1)+items.length)%items.length;
    items[next]?.focus();
   }
  },true);
  const sync=()=>{
   frame=0;if(!tabs.isConnected)return;
   hiddenButton.hidden=true;for(const node of strip.children)node.hidden=false;
   const elements=[...strip.children];
   const widths=elements.map(node=>Math.ceil(node.getBoundingClientRect().width)+4);
   if(widths.reduce((a,b)=>a+b,0)<=strip.clientWidth){
    hidden=[];if(menu==='hidden')dismiss();return;
   }
   hiddenButton.hidden=false;
   const indexes=planTabOverflow(widths,strip.clientWidth,openTabs.indexOf(current));
   hidden=indexes.map(i=>openTabs[i]).filter(Boolean);
   elements.forEach((node,i)=>{if(indexes.includes(i))node.hidden=true;});
   if(menu==='hidden')paint();
   if(menu)position();
  };
  const schedule=()=>{if(!frame)frame=requestAnimationFrame(sync);};
  new ResizeObserver(schedule).observe(tabs);
  window.addEventListener('resize',schedule);
  const tabDidClose=name=>{
   const i=closed.indexOf(name);if(i>=0)closed.splice(i,1);
   closed.unshift(name);if(closed.length>30)closed.pop();
   if(bulk.length)queueMicrotask(nextBulk);schedule();
  };
  return {strip,schedule,visited,recordLocation,tabDidClose,
   updateMinimap:scheduleMinimap,stopBulk:()=>{bulk=[];}};
 })();
""".replace("__PYNIX_ADVANCED_TABS__", TAB_ADVANCED_JS)
"""Services dock with Run Configuration and MCP SSE transport session views."""

SERVICES_DOCK_JS = r"""
  const servicesPane=document.createElement('section');
  servicesPane.className='pynix-services-pane';
  servicesPane.hidden=true;
  servicesPane.innerHTML=`
   <header class="pynix-services-header">
    <strong>Services</strong><span class="pynix-services-fill"></span>
    <button data-sv="refresh" title="Refresh Services">⟳</button>
    <button data-sv="options" title="Options">⋮</button>
    <div data-sv="optionsMenu" class="pynix-services-options-menu" role="menu" hidden></div>
    <button data-sv="hide" title="Hide Services">−</button></header>
   <div class="pynix-services-content">
    <div class="pynix-services-sidebar"><nav class="pynix-services-toolbar" data-sv="toolbar">
     <button data-sv="add" title="Add Service">＋</button>
     <button data-sv="group" title="Group by Type">◉</button>
     <button data-sv="newMcp" title="Add MCP SSE Connection" aria-label="Add MCP SSE Connection">⊞</button>
     <button data-sv="expand" title="Expand All" aria-label="Expand All">⌄</button>
     <button data-sv="collapse" title="Collapse All" aria-label="Collapse All">⌃</button>
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
  // JetBrains-like line icons: keep vectors independent of system Unicode glyphs.
  // The native iconless theme explicitly opts this toolbar into SVG rendering.
  const svIcon=paths=>'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.45" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+paths+'</svg>';
  const svIcons={
   add:'<path d="M10 3v14M3 10h14"/>',
   group:'<path d="M1.6 10c2.15-3.9 5.2-5.85 8.4-5.85S16.25 6.1 18.4 10c-2.15 3.9-5.2 5.85-8.4 5.85S3.75 13.9 1.6 10z"/><circle cx="10" cy="10" r="2.8"/><path d="m16.7 16.5 1.5 1.5" stroke-width="1.25"/>',
   newMcp:'<path d="M13.3 4.5H5.1c-1.35 0-2.1.75-2.1 2.1v8.3c0 1.35.75 2.1 2.1 2.1h8.3c1.35 0 2.1-.75 2.1-2.1v-3.4"/><path d="M15.7 1.8v8M11.7 5.8h8"/>',
   expand:'<path d="m6 8 4-4 4 4M6 16l4-4 4 4"/>',
   collapse:'<path d="m6 4 4 4 4-4M6 12l4 4 4-4"/>',
   refresh:'<circle cx="10" cy="10" r="7.1"/><path d="M10 1.7v5M10 13.3v5M1.7 10h5M13.3 10h5"/>',
   options:'<circle cx="10" cy="4" r="1.15" fill="currentColor" stroke="none"/><circle cx="10" cy="10" r="1.15" fill="currentColor" stroke="none"/><circle cx="10" cy="16" r="1.15" fill="currentColor" stroke="none"/>',
   hide:'<path d="M3 10h14"/>',
   run:'<path d="m6 3.8 9 6.2-9 6.2z"/>',
   mcp:'<path d="M7.5 12.5 14.4 5.6a3 3 0 0 0-4.25-4.25L3.5 8a5 5 0 0 0 7.1 7.1l6-6a3.35 3.35 0 0 0-4.75-4.75L5.4 10.8"/>'
  };
  for(const key of ['add','group','newMcp','expand','collapse','refresh','options','hide'])
   sv(key).innerHTML=svIcon(svIcons[key]);
  sv('add').setAttribute('aria-label','Add Service');
  sv('group').setAttribute('aria-label','Group by Type');
  sv('refresh').setAttribute('aria-label','Refresh Services');
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
  const svSend=(action,extra={})=>{
   const bridge=window.webkit?.messageHandlers?.pynixServices;
   if(!bridge){sv('empty').textContent='Services requires native PYNIX IDE.';return false;}
   bridge.postMessage({action,...extra});return true;
  };
  const svRefresh=()=>svSend('list');
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
    svAction(actions,'Run',()=>{
     const select=document.querySelector('.pynix-run-mode');
     if(!select)return;
     select.value=item.id.slice(4);
     select.dispatchEvent(new Event('change',{bubbles:true}));
     document.querySelector('.pynix-run-action')?.click();
    },run.state==='running');
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
     button.setAttribute('aria-selected',String(item.id===svSelected));
     const icon=document.createElement('span');icon.className='pynix-services-item-icon';
     icon.innerHTML=svIcon(item.type==='run'?svIcons.run:svIcons.mcp);
     const name=document.createElement('span');name.textContent=item.name;
     const state=document.createElement('span');state.className='pynix-services-status';
     state.textContent=['connected','running'].includes(item.state)?'●':
      item.state==='connecting'?'◌':item.state==='error'?'!':'';
     state.title=item.state||'';
     button.append(icon,name,state);
     button.addEventListener('click',()=>{svSelected=item.id;svDraw();});
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
  const optionsMenu=sv('optionsMenu');
  const optionsButton=(text,callback)=>{
   const button=document.createElement('button');button.type='button';
   button.setAttribute('role','menuitem');button.textContent=text;
   button.addEventListener('click',()=>{
    optionsMenu.hidden=true;callback();updateOptions();
   });
   optionsMenu.appendChild(button);return button;
  };
  const groupOption=optionsButton('Group Services by Type',()=>{
   svGrouped=!svGrouped;svDraw();
  });
  const treeOption=optionsButton('Show Services Tree',()=>{
   servicesPane.classList.toggle('hide-tree');
  });
  const updateOptions=()=>{
   groupOption.textContent=(svGrouped?'✓ ':'  ')+'Group Services by Type';
   treeOption.textContent=(!servicesPane.classList.contains('hide-tree')?'✓ ':'  ')+
    'Show Services Tree';
  };
  sv('options').addEventListener('click',()=>{
   menu.hidden=true;updateOptions();
   optionsMenu.hidden=!optionsMenu.hidden;
  });
  sv('group').addEventListener('click',()=>{svGrouped=!svGrouped;svDraw();});
  sv('expand').addEventListener('click',()=>{svGrouped=true;svCollapsed.clear();svDraw();});
  sv('collapse').addEventListener('click',()=>{
   svGrouped=true;svCollapsed.add('Run Configurations');svCollapsed.add('MCP SSE');svDraw();
  });
  sv('refresh').addEventListener('click',svRefresh);
  sv('hide').addEventListener('click',()=>setToolWindowVisible(false));
  sv('sessionTab').addEventListener('click',()=>{svTab='session';svDetail();});
  sv('callsTab').addEventListener('click',()=>{svTab='calls';svDetail();});
  document.addEventListener('pointerdown',event=>{
   if(!sv('toolbar').contains(event.target)&&!sv('options').contains(event.target))
    menu.hidden=true;
   if(!optionsMenu.contains(event.target)&&!sv('options').contains(event.target))
    optionsMenu.hidden=true;
  });
  window.pynixServicesResult=result=>{
   if(result?.error){
    sv('empty').textContent='Services error: '+String(result.error);
    sv('empty').hidden=false;return;
   }
   if(Array.isArray(result?.services)){svProfiles=result.services;svDraw();}
  };
  window.pynixServicesRunEvent=(packet,request)=>{
   const state=packet?.state;
   const key=request?.source?'file':request?.mode;
   if(!['file','run','check'].includes(key))return;
   const previous=svRunStates.get(key)||{state:'idle',since:0};
   if(state==='running')svRunStates.set(key,{state:'running',since:Date.now()});
   if(['finished','error','idle'].includes(state))
    svRunStates.set(key,{state,since:previous.since});
   if(!servicesPane.hidden&&state!=='output'){svDraw();}
  };
  const servicesOnShow=()=>{svDraw();svRefresh();};
  window.setInterval(()=>{
   if(!servicesPane.hidden){svRefresh();svDetail();}
  },2500);
"""
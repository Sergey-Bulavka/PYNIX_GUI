# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Native PYNIX IDE Git tool window: real Log, branches, worktrees, commit diff.

The same resizable host is reused only for layout. No mock history, no hidden
mutating Git operations, and no Git content is rendered as HTML.
"""
from __future__ import annotations

GIT_WINDOW_STYLE = r"""
<style id="pynix-git-window-style">
.workspace-mode .integrated-terminal.pynix-git-active .pynix-terminal-dock-bar,
.workspace-mode .integrated-terminal.pynix-git-active .pynix-debug-panel-bar{display:none!important}
.workspace-mode .integrated-terminal.pynix-git-active .terminal-console{
 padding:0!important;overflow:hidden!important;display:flex!important;
 flex-direction:column!important;background:#1e1f22!important;min-width:0;min-height:0}
.pynix-git-window{display:flex;flex-direction:column;flex:1;min-height:0;min-width:0;
 color:#c4c6cb;font:12px -apple-system,BlinkMacSystemFont,sans-serif}
.pynix-git-head{height:36px;min-height:36px;display:flex;align-items:center;gap:7px;
 border-bottom:1px solid #34373b;padding:0 9px 0 12px;background:#24262a}
.pynix-git-head strong{margin-right:12px;font-size:13px}
.pynix-git-head button,.pynix-git-action,.pynix-git-filter{
 background:transparent;border:0;border-radius:5px;color:#bfc2c8;
 font:inherit;cursor:pointer}
.pynix-git-head button{padding:7px 10px}
.pynix-git-head button:hover,.pynix-git-action:hover,.pynix-git-filter:hover{background:#363a40}
.pynix-git-head button[aria-selected="true"]{background:#31486f;color:#e4edff;
 outline:1px solid #46649a}
.pynix-git-head button:disabled,.pynix-git-action:disabled{opacity:.42;cursor:default}
.pynix-git-head .pynix-git-spacer{flex:1}
.pynix-git-head .pynix-git-small{font-size:18px;padding:3px 8px}
.pynix-git-content{display:flex;min-height:0;min-width:0;flex:1}
.pynix-git-branch-pane{width:30%;min-width:150px;max-width:50%;
 border-right:1px solid #35373c;display:flex;flex-direction:column;resize:horizontal;
 overflow:auto;flex-shrink:0;background:#1e2023}
.pynix-git-toolbar{min-height:42px;display:flex;align-items:center;gap:7px;
 padding:4px 7px;border-bottom:1px solid #323439;min-width:0}
.pynix-git-input{background:#202225;border:1px solid #454950;border-radius:4px;
 color:#d9dade;min-width:0;padding:7px 9px;font:12px -apple-system,BlinkMacSystemFont,sans-serif;
 outline:none}
.pynix-git-input:focus{border-color:#5579bb}
.pynix-git-branch-search{flex:1;width:90px}
.pynix-git-branch-tree{flex:1;min-height:0;overflow:auto;padding:6px 6px 12px}
.pynix-git-tree-row{border:0;color:#bdc0c5;background:transparent;text-align:left;
 width:100%;padding:5px 6px;border-radius:4px;display:flex;align-items:center;gap:8px;
 cursor:pointer;font:inherit;white-space:nowrap}
.pynix-git-tree-row:hover{background:#30343a}
.pynix-git-tree-row[aria-selected="true"]{background:#31476e;color:#f0f3fa}
.pynix-git-tree-caption{font-weight:600;font-size:12px;color:#dee0e4}
.pynix-git-tree-mark{width:16px;text-align:center;color:#a4b8db}
.pynix-git-tree-children{padding-left:16px}
.pynix-git-commit-pane{flex:1;min-width:200px;display:flex;flex-direction:column;overflow:hidden}
.pynix-git-commit-toolbar{display:flex;align-items:center;gap:6px;
 border-bottom:1px solid #34373b;padding:5px 8px;min-height:42px;flex-shrink:0}
.pynix-git-query{width:150px;flex:1;max-width:250px}
.pynix-git-filter{padding:6px 5px;white-space:nowrap}
.pynix-git-filter[aria-pressed="true"]{background:#344866;color:#e6eefc}
.pynix-git-action{min-width:24px;min-height:24px;padding:4px 6px}
.pynix-git-commit-list{flex:1;min-height:0;overflow:auto}
.pynix-git-commit-row{display:flex;align-items:center;min-height:29px;gap:7px;
 width:100%;font:inherit;text-align:left;padding:0 10px 0 5px;background:transparent;
 color:#cfd1d5;border:0;cursor:pointer;white-space:nowrap}
.pynix-git-commit-row:hover{background:#30343b}
.pynix-git-commit-row[aria-selected="true"]{background:#303d57}
.pynix-git-graph{width:78px;flex:0 0 78px;display:flex;align-items:center;height:28px}
.pynix-git-graph svg{width:78px;height:28px;display:block}
.workspace-mode.pynix-iconless .pynix-git-graph svg{display:block!important;
 visibility:visible!important;opacity:1!important}
.pynix-git-subject{flex:1;overflow:hidden;text-overflow:ellipsis}
.pynix-git-badges{font-size:10px;color:#9ac1ea;max-width:135px;
 overflow:hidden;text-overflow:ellipsis}
.pynix-git-author{width:98px;flex:0 0 98px;overflow:hidden;text-overflow:ellipsis}
.pynix-git-date{width:118px;flex:0 0 118px;text-align:right;color:#a4a8af;font-variant-numeric:tabular-nums}
.pynix-git-right{width:24%;min-width:180px;max-width:47%;flex-shrink:0;resize:horizontal;
 display:flex;flex-direction:column;border-left:1px solid #383a3e;overflow:auto}
.pynix-git-files{flex:1;min-height:0;overflow:auto}
.pynix-git-right-title{border-bottom:1px solid #34373b;padding:8px 10px;font-weight:600;min-height:34px;box-sizing:border-box}
.pynix-git-file{display:flex;gap:8px;align-items:center;width:100%;font:inherit;
 border:0;text-align:left;color:#c5cad2;background:transparent;cursor:pointer;
 padding:6px 10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pynix-git-file:hover{background:#30363e}
.pynix-git-file[aria-selected="true"]{background:#34435b}
.pynix-git-file-status{color:#81b68c;font-weight:bold;width:12px}
.pynix-git-file-status[data-type="D"]{color:#cf7979}
.pynix-git-file-status[data-type="M"]{color:#8facdc}
.pynix-git-details{flex:1;min-height:150px;border-top:1px solid #34373b;overflow:auto}
.pynix-git-details-content{padding:9px 12px;white-space:pre-wrap;word-break:break-word;line-height:1.5}
.pynix-git-diff{font:11px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;
 white-space:pre;overflow:auto;margin:0;padding:8px}
.pynix-git-empty{color:#8c9097;font-size:13px;flex:1;display:flex;align-items:center;
 justify-content:center;text-align:center;padding:18px}
.pynix-git-status{font-size:11px;color:#8d949d;white-space:nowrap;
 text-overflow:ellipsis;overflow:hidden;padding:4px 10px;border-top:1px solid #34373b}
.pynix-git-worktrees{flex:1;min-height:0;overflow:auto;padding:12px 20px}
.pynix-git-worktree{border-bottom:1px solid #3b3d42;display:flex;gap:14px;
 align-items:center;padding:12px 6px}
.pynix-git-worktree-path{color:#a1b9e2;word-break:break-all}
.pynix-git-worktree-meta{font-size:11px;color:#9ba1ad}
.pynix-git-popover{position:fixed;z-index:11000;background:#2d3035;
 border:1px solid #50545c;border-radius:6px;padding:9px;min-width:180px;
 box-shadow:0 8px 22px #0008}
.pynix-git-popover[hidden]{display:none}
.pynix-git-popover input{width:calc(100% - 20px)}
.pynix-git-popover button{width:100%;padding:6px 8px;background:transparent;
 color:#d6dbe5;border:0;text-align:left;cursor:pointer;border-radius:4px}
.pynix-git-popover button:hover{background:#3a5178}
@media(max-width:1050px){
 .pynix-git-branch-pane{width:25%;min-width:135px}
 .pynix-git-right{width:27%;min-width:160px}
 .pynix-git-author{width:68px;flex-basis:68px}
 .pynix-git-date{width:78px;flex-basis:78px}
 .pynix-git-commit-toolbar{flex-wrap:wrap}
}
</style>
"""

GIT_WINDOW_SCRIPT = r"""
<script id="pynix-git-window-controller">
(() => {
 'use strict';
 const host=document.querySelector('.workspace-mode .integrated-terminal');
 const panel=host?.querySelector('.terminal-console');
 if(!host||!panel||window.pynixGitWindow)return;
 let log=null,chosen=null,details=null,selectedFile='',loading=false,error='',requestId=0;
 let activeTab='Log',showWorktrees=true,logSerial=1;
 const logTabs=['Log'];
 const filters={branch:'',text:'',user:'',since:'',until:'',path:''};
 const savedTabFilters=new Map([['Log',{...filters}]]);
 const lastRequests={};
 const root=document.createElement('section');root.className='pynix-git-window';
 root.setAttribute('aria-label','Git');
 const head=document.createElement('div');head.className='pynix-git-head';
 const title=document.createElement('strong');title.textContent='Git';head.appendChild(title);
 const main=document.createElement('div');main.className='pynix-git-content';
 const status=document.createElement('div');status.className='pynix-git-status';
 root.append(head,main,status);
 const branchPane=document.createElement('div');branchPane.className='pynix-git-branch-pane';
 const branchesSearch=document.createElement('input');branchesSearch.className='pynix-git-input pynix-git-branch-search';
 branchesSearch.type='search';branchesSearch.placeholder='Branch or tag';branchesSearch.setAttribute('aria-label','Branch or tag');
 const branchToolbar=document.createElement('div');branchToolbar.className='pynix-git-toolbar';
 branchToolbar.appendChild(branchesSearch);branchPane.appendChild(branchToolbar);
 const branchTree=document.createElement('div');branchTree.className='pynix-git-branch-tree';
 branchPane.appendChild(branchTree);
 const commitPane=document.createElement('div');commitPane.className='pynix-git-commit-pane';
 const commitToolbar=document.createElement('div');commitToolbar.className='pynix-git-commit-toolbar';
 const query=document.createElement('input');query.className='pynix-git-input pynix-git-query';
 query.type='search';query.placeholder='Text or hash';query.setAttribute('aria-label','Text or hash');
 commitToolbar.appendChild(query);
 const list=document.createElement('div');list.className='pynix-git-commit-list';list.setAttribute('role','listbox');
 list.setAttribute('aria-label','Git commits');
 commitPane.append(commitToolbar,list);
 const right=document.createElement('div');right.className='pynix-git-right';
 const filesTitle=document.createElement('div');filesTitle.className='pynix-git-right-title';
 filesTitle.textContent='Changed files';
 const files=document.createElement('div');files.className='pynix-git-files';
 const detailsPane=document.createElement('div');detailsPane.className='pynix-git-details';
 const detailsTitle=document.createElement('div');detailsTitle.className='pynix-git-right-title';
 detailsTitle.textContent='Commit details';
 const detailsText=document.createElement('div');detailsText.className='pynix-git-details-content';
 detailsPane.append(detailsTitle,detailsText);right.append(filesTitle,files,detailsPane);
 main.append(branchPane,commitPane,right);
 const worktreesPane=document.createElement('div');worktreesPane.className='pynix-git-worktrees';
 const popover=document.createElement('div');popover.className='pynix-git-popover';
 popover.hidden=true;document.body.appendChild(popover);
 const active=()=>{const state=window.pynixTerminalDock?.state?.();
  return state?.visible&&state.scope==='other'&&state.tool==='GIT'};
 const button=(label,cb,cls='pynix-git-action')=>{
  const b=document.createElement('button');b.type='button';b.className=cls;
  b.textContent=label;b.addEventListener('click',cb);return b;
 };
 const clearPopover=()=>{popover.hidden=true;popover.replaceChildren();};
 const positionPopover=anchor=>{
  const r=anchor.getBoundingClientRect();
  popover.style.left=Math.max(5,Math.min(innerWidth-235,r.left))+'px';
  popover.style.top=Math.max(5,Math.min(innerHeight-225,r.bottom+4))+'px';
  popover.hidden=false;
 };
 document.addEventListener('pointerdown',e=>{
  if(!popover.hidden&&!popover.contains(e.target)&&!e.target.closest('.pynix-git-filter,.pynix-git-small'))clearPopover();
 });
 window.addEventListener('resize',clearPopover);
 const post=(action,payload={})=>{
  const bridge=window.webkit?.messageHandlers?.pynixGitLog;
  if(!bridge){error='Git Log requires the native PYNIX IDE on macOS.';render();return;}
  const id=++requestId;lastRequests[action]=id;
  bridge.postMessage({action,requestId:id,...payload});
 };
 const refresh=()=>{loading=true;error='';render();post('log',{filters:{...filters}});};
 const filterButton=(label,field)=>{
  const b=button(label+' ⌄',()=>openFilter(field,b),'pynix-git-filter');commitToolbar.appendChild(b);
  return b;
 };
 const branchFilter=filterButton('Branch','branch');
 const authorFilter=filterButton('User','user');
 const dateFilter=filterButton('Date','date');
 const pathFilter=filterButton('Paths','path');
 const reloadButton=button('↻',refresh);reloadButton.title='Refresh Git Log';
 commitToolbar.appendChild(reloadButton);
 let searchTimer=0;
 query.addEventListener('input',()=>{
  filters.text=query.value;
  clearTimeout(searchTimer);
  searchTimer=setTimeout(refresh,330);
 });
 branchesSearch.addEventListener('input',()=>renderBranches());
 const openFilter=(field,anchor)=>{
  if(!popover.hidden){clearPopover();return;}
  clearPopover();
  const addInput=(name,placeholder,value)=>{
   const input=document.createElement('input');input.type='text';
   input.className='pynix-git-input';input.placeholder=placeholder;input.value=value;
   input.setAttribute('aria-label',name);popover.appendChild(input);return input;
  };
  if(field==='date'){
   const from=addInput('Since date YYYY-MM-DD','Since YYYY-MM-DD',filters.since);
   const to=addInput('Until date YYYY-MM-DD','Until YYYY-MM-DD',filters.until);
   const apply=button('Apply date filter',()=>{
    filters.since=from.value.trim();filters.until=to.value.trim();
    clearPopover();refresh();
   });popover.appendChild(apply);
   popover.appendChild(button('Clear date filter',()=>{
    filters.since='';filters.until='';clearPopover();refresh();
   }));
  }else{
   const input=addInput(field,field==='branch'?'Full local / remote ref':field,filters[field]||'');
   const apply=()=>{
    filters[field]=input.value.trim();clearPopover();refresh();
   };
   input.addEventListener('keydown',e=>{if(e.key==='Enter')apply();});
   popover.appendChild(button('Apply filter',apply));
   popover.appendChild(button('Clear filter',()=>{
    filters[field]='';clearPopover();refresh();
   }));
  }
  positionPopover(anchor);
  popover.querySelector('input')?.focus();
 };
 const fmtDate=value=>{
  if(!value)return '';
  const d=new Date(value);
  return Number.isNaN(d.getTime())?value:d.toLocaleString(undefined,
   {day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
 };
 const selectTab=name=>{
  if(activeTab!=='Worktrees')savedTabFilters.set(activeTab,{...filters});
  const changed=name!==activeTab;
  activeTab=name;
  if(name!=='Worktrees'){
   Object.assign(filters,savedTabFilters.get(name)||{});
   query.value=filters.text;
   if(changed){log=null;chosen=null;details=null;selectedFile='';}
  }
  render();
  if(changed||(!log&&!loading))refresh();
 };
 const renderHeader=()=>{
  head.replaceChildren(title);
  const addTab=name=>{
   const tab=button(name,()=>selectTab(name));tab.setAttribute('role','tab');
   tab.setAttribute('aria-selected',String(activeTab===name));
   head.appendChild(tab);
  };
  for(const name of logTabs)addTab(name);
  if(showWorktrees){
   addTab('Worktrees');
   const close=button('×',()=>{showWorktrees=false;if(activeTab==='Worktrees')activeTab='Log';render();},
    'pynix-git-small');
   close.title='Close Worktrees tab';head.appendChild(close);
  }
  const plus=button('+',()=>{
   logSerial+=1;const name='Log '+logSerial;logTabs.push(name);
   savedTabFilters.set(name,{...filters});selectTab(name);
  },'pynix-git-small');
  plus.title='New Git Log tab';head.appendChild(plus);
  const menu=button('⌄',()=>{clearPopover();
   const item=(name,cb)=>popover.appendChild(button(name,()=>{clearPopover();cb();}));
   item('New Log tab',()=>plus.click());
   item('Show Worktrees',()=>{showWorktrees=true;selectTab('Worktrees');});
   item('Refresh Git Log',refresh);
   positionPopover(menu);
  },'pynix-git-small');
  menu.title='Git tabs menu';head.appendChild(menu);
  const spacer=document.createElement('span');spacer.className='pynix-git-spacer';head.appendChild(spacer);
  const options=button('⋮',()=>{clearPopover();
   popover.appendChild(button('Refresh',()=>{clearPopover();refresh();}));
   popover.appendChild(button('Clear all filters',()=>{
    for(const key of Object.keys(filters))filters[key]='';query.value='';
    clearPopover();refresh();
   }));
   positionPopover(options);
  },'pynix-git-small');head.appendChild(options);
  const hide=button('−',()=>window.pynixTerminalDock?.hide?.(),'pynix-git-small');
  hide.title='Hide Git tool window';head.appendChild(hide);
 };
 const makeEmpty=(target,message)=>{
  target.replaceChildren();
  const el=document.createElement('div');el.className='pynix-git-empty';
  el.textContent=message;target.appendChild(el);
 };
 const treeRow=(parent,name,marker,click,selected=false,caption=false)=>{
  const row=button('',click,'pynix-git-tree-row');
  const icon=document.createElement('span');icon.className='pynix-git-tree-mark';
  icon.textContent=marker;
  const text=document.createElement('span');text.textContent=name;
  if(caption)text.className='pynix-git-tree-caption';
  row.append(icon,text);row.setAttribute('aria-selected',String(selected));
  parent.appendChild(row);return row;
 };
 let closedGroups=new Set();
 const renderBranches=()=>{
  branchTree.replaceChildren();
  if(!log?.available){makeEmpty(branchTree,loading?'Reading Git refs…':'No Git repository at project root');return;}
  const filter=branchesSearch.value.trim().toLowerCase();
  treeRow(branchTree,'HEAD (Current Branch)','⌁',()=>{
   filters.branch='';refresh();
  },!filters.branch);
  const sections=[['Local','local'],['Remote','remote'],['Tags','tag']];
  for(const [title,kind] of sections){
   const refs=log.refs.filter(x=>x.kind===kind&&(!filter||x.name.toLowerCase().includes(filter)));
   const collapsed=closedGroups.has(kind)&&!filter;
   const headRow=treeRow(branchTree,title+(refs.length?' ('+refs.length+')':''),collapsed?'▸':'▾',()=>{
    if(closedGroups.has(kind))closedGroups.delete(kind);else closedGroups.add(kind);
    renderBranches();
   },false,true);headRow.setAttribute('aria-expanded',String(!collapsed));
   if(collapsed)continue;
   const children=document.createElement('div');children.className='pynix-git-tree-children';
   // Preserve the real ref names, but show slash-separated branch namespaces
   // as JetBrains Local > feature > branch, instead of one long flat list.
   const refTree={refs:[],dirs:new Map()};
   for(const ref of refs){
    const parts=ref.name.split('/');
    let node=refTree;
    for(const segment of parts.slice(0,-1)){
     if(!node.dirs.has(segment))node.dirs.set(segment,{refs:[],dirs:new Map()});
     node=node.dirs.get(segment);
    }
    node.refs.push({...ref,shortName:parts.at(-1)});
   }
   const emit=(node,parent,prefix)=>{
    for(const ref of node.refs.sort((a,b)=>a.name.localeCompare(b.name))){
     const marker=ref.kind==='tag'?'◇':ref.name===log.branch?'◆':'◇';
     const row=treeRow(parent,ref.shortName,marker,()=>{
      filters.branch=ref.full;refresh();
     },filters.branch===ref.full);
     row.title=ref.full+' '+ref.sha.slice(0,8);
    }
    for(const [segment,child] of [...node.dirs.entries()].sort((a,b)=>a[0].localeCompare(b[0]))){
     const groupKey=kind+'/'+prefix+segment;
     const hidden=closedGroups.has(groupKey)&&!filter;
     const folder=treeRow(parent,segment,hidden?'▸':'▾',()=>{
      if(closedGroups.has(groupKey))closedGroups.delete(groupKey);
      else closedGroups.add(groupKey);
      renderBranches();
     },false,true);
     folder.setAttribute('aria-expanded',String(!hidden));
     if(!hidden){
      const nested=document.createElement('div');nested.className='pynix-git-tree-children';
      emit(child,nested,prefix+segment+'/');
      parent.appendChild(nested);
     }
    }
   };
   emit(refTree,children,'');
   branchTree.appendChild(children);
  }
 };
 // True parent-based lane drawing for the ordered local Git DAG.
 // Unlike a decorative vertical stripe, merges/forks connect actual SHAs.
 const graphLayouts=commits=>{
  let lanes=[];
  const layouts=new Map();
  for(const commit of commits){
   let column=lanes.indexOf(commit.sha);
   if(column<0){column=0;lanes.splice(0,0,commit.sha);}
   const before=lanes.slice();
   const after=lanes.slice();
   const parents=commit.parents||[];
   if(parents.length){
    if(after.includes(parents[0])&&after.indexOf(parents[0])!==column)
     after.splice(column,1);
    else after[column]=parents[0];
    for(const parent of parents.slice(1)){
     if(!after.includes(parent))after.splice(Math.min(column+1,after.length),0,parent);
    }
   }else after.splice(column,1);
   const links=[];
   for(let i=0;i<before.length;i++){
    if(i===column)continue;
    const j=after.indexOf(before[i]);
    if(j>=0)links.push([i,j,false]);
   }
   for(const parent of parents){
    const j=after.indexOf(parent);
    if(j>=0)links.push([column,j,true]);
   }
   layouts.set(commit.sha,{column,links});
   lanes=after;
  }
  return layouts;
 };
 const renderGraph=(commit,layout)=>{
  const graph=document.createElement('span');graph.className='pynix-git-graph';
  const ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 78 28');
  svg.setAttribute('aria-hidden','true');
  const x=n=>Math.min(72,9+Math.max(0,n)*13);
  const palette=['#8872d2','#4b99bf','#d08a61','#6cab92','#c16fac'];
  const line=(x1,y1,x2,y2,color)=>{
   const el=document.createElementNS(ns,'line');
   for(const [k,v] of [['x1',x1],['y1',y1],['x2',x2],['y2',y2]])
    el.setAttribute(k,String(v));
   el.setAttribute('stroke',color);el.setAttribute('stroke-width','2');
   svg.appendChild(el);
  };
  const col=layout?.column||0;
  line(x(col),0,x(col),14,palette[col%palette.length]);
  for(const [from,to,isParent] of layout?.links||[]){
   const color=palette[from%palette.length];
   if(isParent)line(x(from),14,x(to),28,color);
   else line(x(from),0,x(to),28,color);
  }
  const dot=document.createElementNS(ns,'circle');
  dot.setAttribute('cx',String(x(col)));dot.setAttribute('cy','14');
  dot.setAttribute('r','4');dot.setAttribute('fill','#23262c');
  dot.setAttribute('stroke',palette[col%palette.length]);dot.setAttribute('stroke-width','2');
  svg.appendChild(dot);graph.appendChild(svg);
  graph.title=commit.parents.length>1?'Merge · '+commit.parents.length+' parents':
   'Commit '+commit.sha.slice(0,8);
  return graph;
 };
 const visibleCommits=()=>{
  const source=log?.commits||[];
  // Hash searches are not message-grep; apply a client-side hash filter.
  const text=filters.text.trim().toLowerCase();
  if(!/^[0-9a-f]{5,64}$/.test(text))return source;
  return source.filter(c=>c.sha.toLowerCase().includes(text)||
   c.subject.toLowerCase().includes(text));
 };
 const renderCommits=()=>{
  list.replaceChildren();
  if(loading){makeEmpty(list,'Loading Git history…');return;}
  if(error){makeEmpty(list,error);return;}
  if(!log){makeEmpty(list,'Open Git to load repository history');return;}
  const commits=visibleCommits();
  if(!commits.length){makeEmpty(list,'No commits match the current filters');return;}
  const layouts=graphLayouts(commits);
  for(const commit of commits){
   const row=button('',()=>choose(commit),'pynix-git-commit-row');
   row.setAttribute('role','option');row.dataset.sha=commit.sha;
   row.setAttribute('aria-selected',String(chosen?.sha===commit.sha));
   row.appendChild(renderGraph(commit,layouts.get(commit.sha)));
   const subject=document.createElement('span');subject.className='pynix-git-subject';
   subject.textContent=commit.subject;subject.title=commit.subject;
   row.appendChild(subject);
   if(commit.refs){
    const refs=document.createElement('span');refs.className='pynix-git-badges';
    refs.textContent=commit.refs;refs.title=commit.refs;row.appendChild(refs);
   }
   const author=document.createElement('span');author.className='pynix-git-author';
   author.textContent=commit.author;author.title=commit.author;
   const date=document.createElement('span');date.className='pynix-git-date';
   date.textContent=fmtDate(commit.date);
   row.append(author,date);
   row.addEventListener('dblclick',()=>choose(commit));
   row.addEventListener('keydown',e=>{
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){
     const rows=[...list.querySelectorAll('.pynix-git-commit-row')];
     const next=rows[rows.indexOf(row)+(e.key==='ArrowDown'?1:-1)];
     if(next){e.preventDefault();next.click();next.focus();}
    }
    if(e.key==='Enter'){e.preventDefault();choose(commit);}
   });
   list.appendChild(row);
  }
 };
 const choose=commit=>{
  chosen=commit;details=null;selectedFile='';
  // Keep selected row mounted so ArrowDown/ArrowUp keyboard focus survives.
  for(const row of list.querySelectorAll('.pynix-git-commit-row'))
   row.setAttribute('aria-selected',String(row.dataset.sha===commit.sha));
  renderDetail();post('commit',{sha:commit.sha});
 };
 const renderDetail=()=>{
  files.replaceChildren();
  detailsText.replaceChildren();detailsTitle.textContent='Commit details';
  if(!chosen){makeEmpty(files,'Select commit to view changes');
   makeEmpty(detailsText,'Commit details');return;}
  if(!details||details.sha!==chosen.sha){
   makeEmpty(files,'Loading changed files…');return;
  }
  const title=document.createElement('div');title.textContent=details.message;
  const meta=document.createElement('div');meta.textContent=
   details.author+' <'+details.email+'>\n'+fmtDate(details.date)+'\n'+details.sha;
  detailsText.append(title,meta);
  const changed=Array.isArray(details.files)?details.files:[];
  filesTitle.textContent='Changed files ('+changed.length+')';
  if(!changed.length){makeEmpty(files,'No changed files');return;}
  for(const file of changed){
   const row=button('',()=>chooseFile(file),'pynix-git-file');
   row.setAttribute('aria-selected',String(selectedFile===file.path));
   const marker=document.createElement('span');marker.className='pynix-git-file-status';
   marker.textContent=file.status.slice(0,1);marker.dataset.type=file.status.slice(0,1);
   const name=document.createElement('span');name.textContent=file.path;
   row.append(marker,name);row.title=file.path;
   row.addEventListener('dblclick',()=>chooseFile(file));
   files.appendChild(row);
  }
 };
 const chooseFile=file=>{
  if(!chosen||!details)return;
  selectedFile=file.path;
  for(const row of files.querySelectorAll('.pynix-git-file')){
   row.setAttribute('aria-selected',String(row.title===selectedFile));
  }
  detailsText.textContent='Loading diff for '+file.path+'…';
  post('diff',{sha:chosen.sha,path:file.path});
 };
 const receive=packet=>{
  if(!packet||packet.requestId!==lastRequests[packet.action])return;
  if(packet.action==='log'){
   loading=false;error=String(packet.error||'');
   if(!error){log=packet.data||null;
    if(chosen&&!log?.commits.some(c=>c.sha===chosen.sha)){chosen=null;details=null;}
   }
   render();
  }else if(packet.action==='commit'){
   if(packet.error){detailsText.textContent=String(packet.error);return;}
   if(chosen?.sha===packet.data?.sha){details=packet.data;renderDetail();}
  }else if(packet.action==='diff'){
   if(packet.error){detailsText.textContent=String(packet.error);return;}
   if(chosen?.sha===packet.data?.sha&&selectedFile===packet.data.path){
    detailsTitle.textContent='Diff · '+packet.data.path;
    detailsText.replaceChildren();
    const pre=document.createElement('pre');pre.className='pynix-git-diff';
    pre.textContent=packet.data.error||packet.data.diff||'No textual changes';
    detailsText.appendChild(pre);
   }
  }
 };
 const renderWorktrees=()=>{
  main.replaceChildren(worktreesPane);worktreesPane.replaceChildren();
  const h=document.createElement('h3');h.textContent='Git Worktrees';
  worktreesPane.appendChild(h);
  if(error){const p=document.createElement('p');p.textContent=error;worktreesPane.appendChild(p);return;}
  if(!log){const p=document.createElement('p');p.textContent='Loading worktrees…';worktreesPane.appendChild(p);return;}
  for(const worktree of log.worktrees||[]){
   const row=document.createElement('div');row.className='pynix-git-worktree';
   const left=document.createElement('div');
   const name=document.createElement('div');name.className='pynix-git-worktree-path';
   name.textContent=worktree.path;
   const meta=document.createElement('div');meta.className='pynix-git-worktree-meta';
   meta.textContent=(worktree.branch||'(detached HEAD)')+' · '+String(worktree.sha||'').slice(0,8)+
    (worktree.locked?' · Locked':'')+(worktree.prunable?' · Prunable':'');
   left.append(name,meta);row.appendChild(left);worktreesPane.appendChild(row);
  }
  if(!log.worktrees?.length){
   const p=document.createElement('p');p.textContent='No worktrees found.';worktreesPane.appendChild(p);
  }
  const note=document.createElement('p');note.className='pynix-git-worktree-meta';
  note.textContent='Worktree list is live and read-only. Creation, removal and branch checkout require an explicit safe Git operation and are not enabled yet.';
  worktreesPane.appendChild(note);
 };
 function render(){
  if(!active())return;
  if(!panel.contains(root))panel.replaceChildren(root);
  host.classList.add('pynix-git-active');
  renderHeader();
  if(activeTab==='Worktrees'){renderWorktrees();}
  else{
   main.replaceChildren(branchPane,commitPane,right);
   for(const [field,b] of [['branch',branchFilter],['user',authorFilter],['path',pathFilter]]){
    b.setAttribute('aria-pressed',String(!!filters[field]));
   }
   dateFilter.setAttribute('aria-pressed',String(!!filters.since||!!filters.until));
   renderBranches();renderCommits();renderDetail();
  }
  status.textContent=loading?'Reading Git repository…':error||(
   log?((log.branch||'')+' · '+(log.commits?.length||0)+
    ' commits'+(log.truncated?' (first '+log.commits.length+'; use filters to search older history)':'')+
    ' · read-only'):'Git history not loaded');
 }
 window.pynixGitWindow={
  refresh,receive,toggle:()=>window.pynixTerminalDock?.toggleGit?.(),
  open:()=>window.pynixTerminalDock?.showGit?.(),
  state:()=>({activeTab,loaded:!!log,loading,selected:chosen?.sha||'',filters:{...filters}})
 };
 window.pynixGitLogResult=receive;
 window.addEventListener('pynix:terminal-change',event=>{
  const value=event.detail||{};
  const visible=value.visible&&value.scope==='other'&&value.tool==='GIT';
  host.classList.toggle('pynix-git-active',visible);
  if(visible){render();if(!log&&!loading)refresh();}
  else clearPopover();
 });
})();
</script>
"""


def apply_git_window(html_source: str) -> str:
    if "</body>" not in html_source:
        raise ValueError("Missing HTML body")
    if 'id="pynix-git-window-controller"' in html_source:
        return html_source
    return html_source.replace("</body>", GIT_WINDOW_STYLE + GIT_WINDOW_SCRIPT + "</body>", 1)

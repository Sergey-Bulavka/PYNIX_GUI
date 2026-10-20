# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""JetBrains-style Problems tool window bound to real PYNIX compiler diagnostics.

The compiler tooling V1 analyzes the saved project; this view never pretends
to provide unsaved-buffer inspections, quick fixes or AI reviews.
"""

PROBLEMS_CSS = r"""
<style id="pynix-problems-style">
.workspace-mode .integrated-terminal.pynix-problems-active .pynix-terminal-dock-bar,
.workspace-mode .integrated-terminal.pynix-problems-active .pynix-debug-panel-bar{
 display:none!important
}
.workspace-mode .integrated-terminal.pynix-problems-active .terminal-console{
 padding:0!important;overflow:hidden!important;display:flex!important;
 min-width:0;min-height:0;background:#1c1d1f!important
}
.pynix-problems-window{display:flex;flex-direction:column;flex:1;min-height:0;min-width:0;color:#bbc0c8;font:13px -apple-system,BlinkMacSystemFont,sans-serif}
.pynix-problems-header{display:flex;align-items:center;gap:7px;min-height:36px;padding:0 8px 0 12px;border-bottom:1px solid #33363a;background:#242629;flex-shrink:0}
.pynix-problems-heading{font-size:13px;font-weight:650;color:#cdd0d5;margin-right:12px;white-space:nowrap}
.pynix-problems-tab{font:inherit;color:#babec4;background:transparent;border:1px solid transparent;padding:5px 10px;border-radius:5px;cursor:pointer;white-space:nowrap}
.pynix-problems-tab:hover{background:#393c41}
.pynix-problems-tab[aria-selected="true"]{background:#2c446e;color:#e2ebff;border-color:#3b5c96}
.pynix-problems-spacer{flex:1}
.pynix-problems-header-action,.pynix-problems-rail-button{border:0;background:transparent;color:#b3b7bc;border-radius:5px;font:inherit;cursor:pointer;display:grid;place-items:center}
.pynix-problems-header-action{width:27px;height:27px;font-size:18px}
.pynix-problems-header-action:hover,.pynix-problems-rail-button:hover{background:#3b3e42;color:#f3f3f3}
.pynix-problems-main{display:flex;flex:1;min-width:0;min-height:0}
.pynix-problems-rail{flex:0 0 36px;display:flex;flex-direction:column;gap:4px;padding:8px 4px;align-items:center}
.pynix-problems-rail-button{width:29px;height:29px;font-size:16px}
.pynix-problems-rail-button[aria-pressed="true"]{background:#354b71;color:#ddeaff}
.pynix-problems-rail-button:disabled{opacity:.38;cursor:not-allowed}
.pynix-problems-body{display:flex;flex:1;min-width:0;min-height:0;flex-direction:column}
.pynix-problems-status{font-size:11px;color:#899099;padding:5px 12px;border-bottom:1px solid #292b2f;flex:0 0 auto}
.pynix-problems-results{overflow:auto;flex:1;min-height:0;padding:5px 0}
.pynix-problems-empty{height:100%;display:flex;align-items:center;justify-content:center;text-align:center;color:#81858d;font-size:13px;padding:20px}
.pynix-problems-row{width:100%;border:0;background:transparent;color:#ced1d5;display:flex;align-items:baseline;gap:10px;text-align:left;font:inherit;cursor:pointer;padding:6px 12px}
.pynix-problems-row:hover{background:#2b2e33}
.pynix-problems-row[aria-selected="true"]{background:#33415b}
.pynix-problems-severity{font-size:12px;color:#e98a7c;flex:0 0 14px}
.pynix-problems-severity[data-level="warning"]{color:#d7af68}
.pynix-problems-location{color:#8f9eb7;font-variant-numeric:tabular-nums;min-width:48px}
.pynix-problems-message{flex:1;overflow-wrap:anywhere}
.pynix-problems-code{color:#898c93;font-size:11px}
.pynix-problems-group{display:flex;align-items:center;gap:8px;color:#bec4cb;background:transparent;border:0;width:100%;font:inherit;font-weight:600;text-align:left;padding:7px 12px;cursor:pointer}
.pynix-problems-group:hover{background:#2d3035}
.pynix-problems-group .pynix-count{margin-left:auto;font-size:11px;color:#8e959f}
.pynix-problems-preview{flex:0 1 42%;min-width:0;border-top:1px solid #383b40;overflow:auto;background:#191b1e;padding:10px 12px}
.pynix-problems-preview pre{margin:7px 0 0;white-space:pre-wrap;word-break:break-word;color:#c8ced5;font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
.pynix-problems-preview-note{font-size:11px;color:#9da5b1}
.pynix-problems-menu{position:absolute;z-index:6000;background:#303238;border:1px solid #4b4e56;box-shadow:0 7px 22px #0009;border-radius:6px;min-width:210px;padding:5px}
.pynix-problems-menu[hidden]{display:none}
.pynix-problems-menu button{display:block;width:100%;padding:7px 10px;color:#dde0e5;background:transparent;border:0;text-align:left;border-radius:4px;font:12px -apple-system,sans-serif;cursor:pointer}
.pynix-problems-menu button:hover{background:#405780}
.pynix-problems-menu button:disabled{opacity:.5;cursor:default}
.pynix-problems-menu button[aria-checked="true"]::before{content:"✓ ";color:#a9c1f8}
</style>
"""

PROBLEMS_JS = r"""
<script id="pynix-problems-controller">
(() => {
 'use strict';
 const host=document.querySelector('.workspace-mode .integrated-terminal');
 const panel=host?.querySelector('.terminal-console');
 if(!host||!panel||window.pynixProblems)return;
 const root=document.createElement('section');
 root.className='pynix-problems-window';
 root.setAttribute('aria-label','Problems');
 const header=document.createElement('div');
 header.className='pynix-problems-header';
 const heading=document.createElement('span');heading.className='pynix-problems-heading';heading.textContent='Problems';
 const tabButtons=[];
 const tabs=['File','Project Errors','AI Self-Review'];
 let selectedTab='File',selected=null,previewVisible=false;
 let records=[],error='',loaded=false,loading=false,showWarnings=true,showErrors=true;
 let sortBySeverity=false,collapsed=new Set(),currentRows=[];
 const toolButton=(label,symbol,callback,cls='pynix-problems-header-action')=>{
  const b=document.createElement('button');b.type='button';b.className=cls;
  b.textContent=symbol;b.title=label;b.setAttribute('aria-label',label);
  b.addEventListener('click',callback);return b;
 };
 const hideMenu=()=>{menu.hidden=true;};
 const getSource=()=>window.pynixGetActiveSource?.()||null;
 const isActive=()=>window.pynixTerminalDock?.state()?.tool==='PROBLEMS' &&
   window.pynixTerminalDock?.state()?.scope==='other' &&
   !host.classList.contains('pynix-tool-window-collapsed');
 const selectTab=name=>{selectedTab=name;selected=null;hideMenu();render();};
 const headingTabs=()=>{
  for(const name of tabs){
   const button=document.createElement('button');button.type='button';
   button.className='pynix-problems-tab';button.textContent=name;button.setAttribute('role','tab');
   button.addEventListener('click',()=>selectTab(name));
   tabButtons.push(button);header.appendChild(button);
  }
 };
 header.appendChild(heading);headingTabs();
 const spacer=document.createElement('div');spacer.className='pynix-problems-spacer';header.appendChild(spacer);
 const refresh=toolButton('Refresh saved-project diagnostics','↻',()=>requestDiagnostics(true));
 const options=toolButton('View Options','⋮',()=>toggleMenu(options));
 const hide=toolButton('Hide Problems','−',()=>window.pynixTerminalDock?.hide?.());
 header.append(refresh,options,hide);
 const main=document.createElement('div');main.className='pynix-problems-main';
 const rail=document.createElement('div');rail.className='pynix-problems-rail';rail.setAttribute('role','toolbar');
 const viewOptions=toolButton('View Options','◉',()=>toggleMenu(viewOptions),'pynix-problems-rail-button');
 const fixes=toolButton('Quick fixes unavailable: compiler tooling V1 does not supply fix actions','♢',()=>{},'pynix-problems-rail-button');
 fixes.disabled=true;
 const preview=toolButton('Open Editor Preview','▤',()=>{
  previewVisible=!previewVisible;render();
 },'pynix-problems-rail-button');
 rail.append(viewOptions,fixes,preview);
 const body=document.createElement('div');body.className='pynix-problems-body';
 const status=document.createElement('div');status.className='pynix-problems-status';
 const results=document.createElement('div');results.className='pynix-problems-results';
 results.setAttribute('role','listbox');results.setAttribute('aria-label','Problems list');
 const previewPane=document.createElement('div');previewPane.className='pynix-problems-preview';
 body.append(status,results,previewPane);main.append(rail,body);root.append(header,main);
 const menu=document.createElement('div');menu.className='pynix-problems-menu';
 menu.hidden=true;menu.setAttribute('role','menu');document.body.appendChild(menu);
 const menuAction=(title,onClick,checked=null,disabled=false)=>{
  const b=document.createElement('button');b.type='button';b.textContent=title;
  b.setAttribute('role',checked===null?'menuitem':'menuitemcheckbox');
  if(checked!==null)b.setAttribute('aria-checked',String(checked));
  b.disabled=disabled;b.addEventListener('click',()=>{hideMenu();onClick();});menu.appendChild(b);
 };
 const toggleMenu=target=>{
  if(!menu.hidden){hideMenu();return;}
  menu.replaceChildren();
  menuAction('Show errors',()=>{showErrors=!showErrors;render();},showErrors);
  menuAction('Show warnings',()=>{showWarnings=!showWarnings;render();},showWarnings);
  menuAction('Sort by severity',()=>{sortBySeverity=!sortBySeverity;render();},sortBySeverity);
  menuAction('Sort by file position',()=>{sortBySeverity=false;render();});
  menuAction('Refresh diagnostics',()=>requestDiagnostics(true));
  menuAction('Copy selected description',copySelected,null,!selected);
  menuAction('Jump to Source  F4',jumpSelected,null,!selected);
  menuAction('Show Quick Fixes (unavailable)',()=>{},null,true);
  const bounds=target.getBoundingClientRect();
  menu.style.left=Math.max(4,Math.min(innerWidth-225,bounds.left))+'px';
  menu.style.top=Math.min(innerHeight-215,bounds.bottom+4)+'px';
  menu.hidden=false;
 };
 document.addEventListener('pointerdown',e=>{
  if(!menu.hidden&&!menu.contains(e.target)&&e.target!==options&&e.target!==viewOptions)hideMenu();
 });
 window.addEventListener('resize',hideMenu);
 const severity=item=>{
  const value=String(item.severity||'').toLowerCase();
  if(value==='warning'||value==='weak_warning'||(!value&&/^W/i.test(item.code||'')))return 'warning';
  return 'error';
 };
 const normalize=raw=>{
  if(!raw||typeof raw!=='object')return null;
  const source=String(raw.source||'');
  if(!source||source.startsWith('/')||source.includes('..')||source.includes('\\'))return null;
  const line=Math.max(1,Number(raw.line)||1);
  const column=Math.max(1,Number(raw.column)||1);
  return {source,line,column,code:String(raw.code||''),message:String(raw.message||''),
   severity:severity(raw)};
 };
 const problemsForTab=()=>{
  const source=getSource();
  let list=records.filter(item=>selectedTab!=='File'||item.source===source);
  list=list.filter(item=>item.severity==='warning'?showWarnings:showErrors);
  if(sortBySeverity)list=list.slice().sort((a,b)=>
   (a.severity==='error'?0:1)-(b.severity==='error'?0:1)||
   a.source.localeCompare(b.source)||a.line-b.line||a.column-b.column);
  return list;
 };
 const problemKey=p=>p.source+':'+p.line+':'+p.column+':'+p.code+':'+p.message;
 const jump=item=>{
  if(!item)return;
  document.dispatchEvent(new CustomEvent('pynix:navigate',{
   detail:{source:item.source,line:item.line,column:item.column}
  }));
 };
 function jumpSelected(){jump(selected);}
 function copySelected(){
  if(!selected)return;
  const content=selected.source+':'+selected.line+':'+selected.column+' '+selected.message;
  if(navigator.clipboard?.writeText)navigator.clipboard.writeText(content).catch(()=>{});
  else{
   const input=document.createElement('textarea');input.value=content;
   document.body.appendChild(input);input.select();document.execCommand('copy');input.remove();
  }
 }
 const addRow=item=>{
  const row=document.createElement('button');row.type='button';
  row.className='pynix-problems-row';row.setAttribute('role','option');
  row.setAttribute('aria-selected',String(selected!==null&&problemKey(selected)===problemKey(item)));
  const level=document.createElement('span');level.className='pynix-problems-severity';
  level.dataset.level=item.severity;level.textContent=item.severity==='warning'?'▲':'●';
  const place=document.createElement('span');place.className='pynix-problems-location';
  place.textContent=item.line+':'+item.column;
  const message=document.createElement('span');message.className='pynix-problems-message';message.textContent=item.message;
  const code=document.createElement('span');code.className='pynix-problems-code';code.textContent=item.code;
  row.append(level,place,message,code);
  row.title=item.source+':'+item.line+':'+item.column+' — '+item.message;
  row.addEventListener('click',()=>{selected=item;render();});
  row.addEventListener('dblclick',()=>jump(item));
  row.addEventListener('keydown',e=>{
   if(e.key==='F4'||e.key==='Enter'){e.preventDefault();jump(item);}
   if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='c'){e.preventDefault();copySelected();}
   if(e.key==='ArrowDown'||e.key==='ArrowUp'){
    const items=[...results.querySelectorAll('.pynix-problems-row')];
    const index=items.indexOf(row),next=items[index+(e.key==='ArrowDown'?1:-1)];
    if(next){e.preventDefault();next.focus();next.click();}
   }
  });
  results.appendChild(row);
  return row;
 };
 const renderPreview=()=>{
  preview.setAttribute('aria-pressed',String(previewVisible));
  previewPane.hidden=!previewVisible;
  if(!previewVisible)return;
  previewPane.replaceChildren();
  const description=document.createElement('div');description.className='pynix-problems-preview-note';
  if(!selected){description.textContent='Select a problem to preview its source.';previewPane.append(description);return;}
  const source=window.pynixGetProblemPreview?.(selected.source);
  description.textContent=selected.source+':'+selected.line+
   ' · Read-only preview (edit in main editor)'+(source?.dirty?' · Unsaved changes':'');
  previewPane.appendChild(description);
  const pre=document.createElement('pre');
  if(typeof source?.text!=='string'){
   pre.textContent='Source preview not loaded. Double-click the problem to open the file.';
  }else{
   const lines=source.text.split('\n');
   const start=Math.max(0,selected.line-4),end=Math.min(lines.length,selected.line+3);
   pre.textContent=lines.slice(start,end).map((text,i)=>
    String(start+i+1).padStart(4,' ')+(start+i+1===selected.line?' > ':'   ')+text).join('\n');
  }
  previewPane.append(pre);
 };
 const empty=message=>{
  const el=document.createElement('div');el.className='pynix-problems-empty';el.textContent=message;results.appendChild(el);
 };
 function render(){
  tabButtons.forEach((button,i)=>button.setAttribute('aria-selected',String(tabs[i]===selectedTab)));
  viewOptions.setAttribute('aria-pressed',String(!showErrors||!showWarnings||sortBySeverity));
  preview.setAttribute('aria-pressed',String(previewVisible));
  if(!isActive())return;
  if(!panel.contains(root))panel.replaceChildren(root);
  host.classList.add('pynix-problems-active');
  results.replaceChildren();
  const source=getSource(),list=selectedTab==='AI Self-Review'?[]:problemsForTab();
  currentRows=list;
  status.textContent=loading?'Checking saved project…':
   error?'Compiler diagnostics unavailable · '+error:
   !loaded?'Saved-project diagnostics have not run yet':
   (list.length+' shown / '+records.length+' project problems · saved source only');
  if(selectedTab==='AI Self-Review'){
   empty('AI Self-Review is not connected. No AI analysis results are available.');
  }else if(loading){
   empty('Analyzing saved project…');
  }else if(error){
   empty('Unable to analyze the project: '+error);
  }else if(!loaded){
   empty('Open Problems or refresh to analyze the saved project.');
  }else if(selectedTab==='File'&&!source){
   empty('No file open');
  }else if(!list.length){
   empty(selectedTab==='File'?'No problems in '+source:'No project problems'+
    ((!showWarnings||!showErrors)?' with the current filters':''));
  }else if(selectedTab==='Project Errors'){
   const groups=new Map();
   for(const item of list){
    if(!groups.has(item.source))groups.set(item.source,[]);
    groups.get(item.source).push(item);
   }
   for(const [name,items] of groups){
    const group=document.createElement('button');group.type='button';
    group.className='pynix-problems-group';
    group.textContent=(collapsed.has(name)?'▸ ':'▾ ')+name;
    const count=document.createElement('span');count.className='pynix-count';count.textContent=String(items.length);
    group.appendChild(count);group.setAttribute('aria-expanded',String(!collapsed.has(name)));
    group.addEventListener('click',()=>{if(collapsed.has(name))collapsed.delete(name);else collapsed.add(name);render();});
    results.appendChild(group);
    if(!collapsed.has(name))items.forEach(addRow);
   }
  }else list.forEach(addRow);
  renderPreview();
 }
 function requestDiagnostics(force=false){
  if(loading)return;
  if(loaded&&!force)return;
  const bridge=window.webkit?.messageHandlers?.pynixDiagnostics;
  if(!bridge){
   error='Compiler diagnostics require the native PYNIX IDE on macOS.';
   loaded=true;render();return;
  }
  loading=true;error='';render();
  bridge.postMessage({scope:'project'});
 }
 const receiveDiagnostics=payload=>{
  loading=false;loaded=true;
  error=String(payload?.error||'');
  records=(Array.isArray(payload?.problems)?payload.problems:[]).slice(0,200)
   .map(normalize).filter(Boolean);
  if(selected&&!records.some(p=>problemKey(p)===problemKey(selected)))selected=null;
  render();
 };
 // Replace the legacy "print diagnostics into Terminal" handler: every
 // result now belongs to Problems even if Terminal/Run is currently active.
 window.pynixLiveDiagnosticsResult=receiveDiagnostics;
 window.pynixProblems={
  refresh:()=>requestDiagnostics(true),receiveDiagnostics,
  open:()=>window.pynixTerminalDock?.showProblems?.(),
  toggle:()=>window.pynixTerminalDock?.toggleProblems?.(),
  state:()=>({tab:selectedTab,loaded,loading,count:records.length,source:getSource()})
 };
 window.addEventListener('pynix:terminal-change',event=>{
  const detail=event.detail||{};
  const active=detail.scope==='other'&&detail.tool==='PROBLEMS'&&detail.visible;
  host.classList.toggle('pynix-problems-active',active);
  if(active){render();requestDiagnostics();}
  else hideMenu();
 });
 document.addEventListener('pynix:file-opened',()=>{if(isActive())render();});
 document.addEventListener('pynix:file-saved',()=>{if(isActive())requestDiagnostics(true);});
 host.addEventListener('keydown',event=>{
  if(!isActive()||!(event.altKey&&!event.metaKey&&!event.ctrlKey))return;
  if(event.key==='ArrowRight'||event.key==='ArrowLeft'){
   event.preventDefault();
   const index=tabs.indexOf(selectedTab);
   selectTab(tabs[(index+(event.key==='ArrowRight'?1:tabs.length-1))%tabs.length]);
  }
 });
})();
</script>
"""


def apply_problems_window(html_source: str) -> str:
    """Install a single Problems pane after workspace and dock initialization."""
    if "</body>" not in html_source:
        raise ValueError("Missing HTML body")
    if 'id="pynix-problems-controller"' in html_source:
        return html_source
    return html_source.replace("</body>", PROBLEMS_CSS + PROBLEMS_JS + "</body>", 1)

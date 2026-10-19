# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Native V4 Search Everywhere: routes to real workspace/editor controls.

The workspace provides the file/symbol catalog; this module only owns the
search dialog and keyboard/navigation presentation, not a second file index.
"""

SEARCH_SCRIPT = r"""<script id="pynix-search-everywhere-script">
(() => {
 if(window.pynixSearchEverywhereInstalled)return;
 window.pynixSearchEverywhereInstalled=true;
 let backdrop=null,input=null,results=null,catalog=[],visible=[],chosen=0;
 const toolWindows=[
  ['Project',0],['Search',1],['Version Control',2],
 ];
 const actions=[
  ['Run Current File','.pynix-pycharm-center>.pynix-run-action'],
  ['Debug Current File','.pynix-pycharm-center>.pynix-debug-primary'],
  ['Save Source','.pynix-save-action'],
  ['More Actions','.pynix-pycharm-center>.pynix-tools-menu>summary'],
 ];
 const close=()=>{
  if(backdrop)backdrop.hidden=true;
 };
 const activate=entry=>{
  if(!entry)return;
  close();
  if(entry.settings){
   window.pynixOpenSettingsWindow?.('Editor');
  }else if(entry.source){
   window.pynixOpenSourceFromSearch?.(entry.source,entry.line||1);
  }else if(entry.action){
   document.querySelector(entry.action)?.click();
  }else if(Number.isInteger(entry.rail)){
   document.querySelectorAll('.workspace-mode .rail>.rail-item')[entry.rail]?.click();
  }
 };
 const select=()=>{
  results.querySelectorAll('[role="option"]').forEach((node,i)=>
   node.setAttribute('aria-selected',String(i===chosen)));
  input.setAttribute('aria-activedescendant',
   visible.length?'pynix-everywhere-option-'+chosen:'');
  if(visible.length)results.children[chosen]?.scrollIntoView({block:'nearest'});
 };
 const render=()=>{
  results.replaceChildren();
  const query=input.value.trim().toLocaleLowerCase();
  visible=catalog.filter(item=>
   !query||[item.label,item.category,item.source||''].join(' ')
    .toLocaleLowerCase().includes(query)
  ).slice(0,80);
  chosen=Math.max(0,Math.min(chosen,visible.length-1));
  if(!visible.length){
   const empty=document.createElement('div');
   empty.className='pynix-search-everywhere-empty';
   empty.textContent='No results among indexed files and available commands';
   results.appendChild(empty);return;
  }
  visible.forEach((entry,index)=>{
   const button=document.createElement('button');
   button.type='button';button.className='pynix-search-everywhere-result';
   button.id='pynix-everywhere-option-'+index;button.setAttribute('role','option');
   button.setAttribute('aria-selected',String(index===chosen));
   const category=document.createElement('span');
   category.className='pynix-search-everywhere-kind';category.textContent=entry.category;
   const name=document.createElement('span');
   name.className='pynix-search-everywhere-name';name.textContent=entry.label;
   button.append(category,name);
   if(entry.source&&entry.category!=='Files'){
    const source=document.createElement('span');
    source.className='pynix-search-everywhere-path';
    source.textContent=entry.source+(entry.line?':'+entry.line:'');
    button.appendChild(source);
   }
   button.addEventListener('pointermove',()=>{
    if(chosen===index)return;
    chosen=index;select();
   });
   button.addEventListener('click',()=>activate(entry));
   results.appendChild(button);
  });
  select();
 };
 const ensure=()=>{
  if(backdrop)return;
  backdrop=document.createElement('div');
  backdrop.className='pynix-search-everywhere-backdrop';backdrop.hidden=true;
  const dialog=document.createElement('section');
  dialog.className='pynix-search-everywhere-dialog';
  dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');
  dialog.setAttribute('aria-label','Search Everywhere');
  const heading=document.createElement('div');
  heading.className='pynix-search-everywhere-heading';
  heading.textContent='Search Everywhere';
  input=document.createElement('input');input.type='search';
  input.className='pynix-search-everywhere-input';
  input.setAttribute('role','combobox');input.setAttribute('aria-label','Search Everywhere');
  input.setAttribute('aria-autocomplete','list');
  input.setAttribute('aria-controls','pynix-everywhere-results');
  input.placeholder='Files, classes, symbols, tool windows, actions, settings';
  results=document.createElement('div');
  results.id='pynix-everywhere-results';
  results.className='pynix-search-everywhere-results';
  results.setAttribute('role','listbox');
  dialog.append(heading,input,results);backdrop.appendChild(dialog);
  document.body.appendChild(backdrop);
  backdrop.addEventListener('pointerdown',event=>{
   if(event.target===backdrop)close();
  });
  input.addEventListener('input',()=>{chosen=0;render();});
  input.addEventListener('keydown',event=>{
   if(event.key==='Escape'){event.preventDefault();close();return;}
   if(event.key==='ArrowDown'||event.key==='ArrowUp'){
    event.preventDefault();
    if(visible.length){
     chosen=(chosen+(event.key==='ArrowDown'?1:-1)+visible.length)%visible.length;
     select();
    }
   }
   if(event.key==='Enter'){event.preventDefault();activate(visible[chosen]);}
  });
 };
 const open=()=>{
  ensure();
  catalog=[];
  const sources=window.pynixSearchEverywhereCatalog?.();
  if(Array.isArray(sources))
   catalog.push(...sources.filter(item=>item&&
    typeof item.label==='string'&&typeof item.source==='string'));
  for(const [name,rail] of toolWindows){
   if(document.querySelectorAll('.workspace-mode .rail>.rail-item')[rail])
    catalog.push({
     category:name==='Settings'?'Settings':'Tool Windows',
     label:name,rail
    });
  }
  if(typeof window.pynixOpenSettingsWindow==='function')
   catalog.push({category:'Settings',label:'Settings',settings:true});
  for(const [name,action] of actions){
   if(document.querySelector(action))
    catalog.push({category:'Actions',label:name,action});
  }
  backdrop.hidden=false;chosen=0;input.value='';render();input.focus();
 };
 window.pynixOpenSearchEverywhere=open;
 let lastShift=0;
 document.addEventListener('keyup',event=>{
  if(event.key!=='Shift'||event.repeat||event.ctrlKey||event.metaKey||event.altKey)return;
  const now=performance.now();
  if(lastShift>0&&now-lastShift<=450){lastShift=0;open();}
  else lastShift=now;
 },true);
 document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&backdrop&&!backdrop.hidden){
   event.preventDefault();event.stopPropagation();close();
  }
 },true);
})();
</script>"""


def apply_search_everywhere(document: str) -> str:
    """Install the V4 palette without replacing existing search or run handlers."""
    if "</body>" not in document or 'id="pynix-search-everywhere-script"' in document:
        return document
    return document.replace("</body>", SEARCH_SCRIPT + "</body>", 1)

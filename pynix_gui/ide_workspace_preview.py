"""Read-only bridge from a real local project into the V4 visual workspace.

Uses a bounded snapshot, not subprocesses or arbitrary filesystem access.
"""
from __future__ import annotations

import html
import json

from .ide_workspace_session import WorkspaceSession
from .ide_syntax_highlight import highlight_document
from .ide_file_icons import file_icon_type


def workspace_bootstrap(session: WorkspaceSession, *, max_files: int = 120,
                        max_bytes: int = 100_000) -> str:
    records = []
    folders = session.list_directories()
    loaded = 0
    for name in session.list_files(limit=10000):
        if not name.lower().endswith((".pnx", ".py", ".md", ".json", ".toml", ".txt")):
            continue
        try:
            path = session.resolve_file(name)
            if path.stat().st_size > max_bytes:
                records.append({"name": name, "text": "", "tokens": None,
                                "icon": file_icon_type(name), "unloaded": True})
                continue
            if loaded >= max_files:
                records.append({"name": name, "text": "", "tokens": None,
                                "icon": file_icon_type(name), "unloaded": True})
                continue
            doc = session.open(name)
            loaded += 1
        except (OSError, ValueError):
            continue
        records.append({"name": name, "text": doc.text,
                        "tokens": highlight_document(doc.text) if name.endswith(".pnx") else None,
                        "icon": file_icon_type(name)})
    session.documents.clear()
    session.active = None
    folder_payload = json.dumps(folders, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    payload = json.dumps(records, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    # This script is appended after the gallery's own scripts, so the initial
    # design preview retains its independent, self-contained state.
    return """<script>
(() => {
 const files = PAYLOAD;
 const PROJECT_NAME = PROJECT_NAME_PAYLOAD;
 const folders = FOLDER_PAYLOAD;
 const workspace = document.body.classList.contains('workspace-mode');
 if (!workspace || !files.length) return;
 const tree = document.querySelector('.tree');
 const tabs = document.querySelector('.editor-tabs');
 const code = document.querySelector('.editor .code');
 if (!tree || !tabs || !code) return;
 const original = tree.innerHTML;
 const byName = new Map(files.map(file => [file.name, file]));
 const openTabs = [];
 let current = null;
 let selectedPath = null;
 // Native editor uses a textarea for real caret, selection, IME and Undo/Redo.
 const editorInput=document.createElement('textarea');
 editorInput.className='pynix-source-input';
 editorInput.spellcheck=false;
 editorInput.wrap='off';
 editorInput.setAttribute('aria-label','PYNIX source editor');
 editorInput.hidden=true;
 const editLayer=document.createElement('div');
 editLayer.className='pynix-edit-layer';
 const coloredSource=document.createElement('pre');
 coloredSource.className='pynix-edit-highlight';
 coloredSource.setAttribute('aria-hidden','true');
 const gutter=document.createElement('pre');
 gutter.className='pynix-edit-gutter';
 gutter.setAttribute('aria-hidden','true');
 const activeLine=document.createElement('div');
 activeLine.className='pynix-active-line';
 const customCaret=document.createElement('div');
 customCaret.className='pynix-custom-caret';
 customCaret.setAttribute('aria-hidden','true');
 editLayer.append(gutter,activeLine,coloredSource,editorInput,customCaret);
 const cursorStatus=document.createElement('span');
 cursorStatus.className='pynix-cursor-status';
 document.querySelector('.bottom')?.appendChild(cursorStatus);
 function updateCursor(){
   if(!current)return;
   const before=editorInput.value.slice(0,editorInput.selectionStart);
   const line=before.split('\\n').length;
   const column=before.length-before.lastIndexOf('\\n');
   cursorStatus.textContent='Ln '+line+', Col '+column;
   const metrics=getComputedStyle(editorInput);
   const lineHeight=parseFloat(metrics.lineHeight);
   const topPadding=parseFloat(metrics.paddingTop);
   activeLine.style.height=lineHeight+'px';
   activeLine.style.transform='translateY('+(topPadding+(line-1)*lineHeight-editorInput.scrollTop)+'px)';
   const colIndex=before.length-before.lastIndexOf('\\n')-1;
   const measure=document.createElement('span');
   measure.style.cssText='position:absolute;visibility:hidden;white-space:pre';
   measure.style.fontFamily=metrics.fontFamily;
   measure.style.fontSize=metrics.fontSize;
   measure.style.fontWeight=metrics.fontWeight;
   measure.style.fontStyle=metrics.fontStyle;
   measure.style.letterSpacing=metrics.letterSpacing;
   measure.textContent='0000000000';
   editorInput.parentElement.appendChild(measure);
   const advance=measure.getBoundingClientRect().width/10;
   measure.remove();
   const left=parseFloat(metrics.paddingLeft)+colIndex*advance-editorInput.scrollLeft;
   const top=topPadding+(line-1)*lineHeight-editorInput.scrollTop;
   customCaret.style.height=lineHeight+'px';
   customCaret.style.transform='translate('+left+'px,'+top+'px)';
   customCaret.classList.remove('pynix-caret-blink');
   void customCaret.offsetWidth;
   customCaret.classList.add('pynix-caret-blink');
   customCaret.hidden=editorInput.selectionStart!==editorInput.selectionEnd||document.activeElement!==editorInput;

   const file=byName.get(current);
   if(file){file.cursorStart=editorInput.selectionStart;file.cursorEnd=editorInput.selectionEnd;file.scrollTop=editorInput.scrollTop;file.scrollLeft=editorInput.scrollLeft;}
 }
 editorInput.addEventListener('click',updateCursor);
 editorInput.addEventListener('focus',updateCursor);
 editorInput.addEventListener('blur',()=>{customCaret.hidden=true;});
 editorInput.addEventListener('keyup',updateCursor);
 editorInput.addEventListener('select',updateCursor);
 code.parentElement.appendChild(editLayer);
 function escapeCode(v){return v.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
 function recolorSource(){
   const value=editorInput.value;
   // The lexer consumes one token at a time. Strings/comments are atomic:
   // numbers inside // comments, # comments or quoted strings stay in that color.
   const token=/(?:\\/\\/[^\\n]*|#[^\\n]*|"(?:\\\\.|[^"\\\\])*"|'(?:\\\\.|[^'\\\\])*'|\\b[A-Za-z_][A-Za-z_0-9]*\\b|\\b\\d+(?:\\.\\d+)?\\b)/g;
   const words=new Set(['function','module','import','from','as','let','var','const','if','else','elif','while','for','in','return','break','continue','and','or','not','class','interface','type','enum','match','case','try','catch','finally','raise','public','private','async','await']);
   const types=new Set(['Int','Float','Bool','String','Void','Any','List','Map']);
   let html='',last=0,match;
   while((match=token.exec(value))){
     html+=escapeCode(value.slice(last,match.index));
     const t=match[0];
     let kind='plain';
     if(t.startsWith('//')||t.startsWith('#'))kind='comment';
     else if(t[0]==='"'||t[0]==="'")kind='string';
     else if(/^\\d/.test(t))kind='number';
     else if(words.has(t))kind='keyword';
     else if(types.has(t))kind='type';
     else if(['print','input','len','range','str','int','float'].includes(t))kind='builtin';
     else if(/^[A-Za-z_]/.test(t)&&/^\\s*\\(/.test(value.slice(token.lastIndex)))kind='call';
     else if(['true','false','none','null'].includes(t))kind='constant';
     html+='<span class="pynix-edit-'+kind+'">'+escapeCode(t)+'</span>';
     last=token.lastIndex;
   }
   coloredSource.innerHTML=html+escapeCode(value.slice(last))+'\\n';
   decorateFindMatches();
   const count=value.split('\\n').length;
   gutter.textContent=Array.from({length:count},(_,i)=>String(i+1)).join('\\n');
   coloredSource.scrollTop=editorInput.scrollTop;
   coloredSource.scrollLeft=editorInput.scrollLeft;
   gutter.scrollTop=editorInput.scrollTop;
 }
 editorInput.addEventListener('scroll',()=>{coloredSource.scrollTop=editorInput.scrollTop;coloredSource.scrollLeft=editorInput.scrollLeft;gutter.scrollTop=editorInput.scrollTop;updateCursor();});
 const editButton=document.createElement('button');
 editButton.type='button';
 editButton.textContent='Edit';
 editButton.className='nav-action pynix-edit-toggle';
 document.querySelector('.workspace-toolbar')?.appendChild(editButton);
 const saveButton=document.createElement('button');
 saveButton.type='button';saveButton.textContent='Save';
 saveButton.className='nav-action pynix-save-action';
 document.querySelector('.workspace-toolbar')?.appendChild(saveButton);
 const searchBar=document.createElement('div');
 searchBar.className='pynix-find-bar';
 searchBar.hidden=true;
 const findInput=document.createElement('input');
 findInput.type='search';
 findInput.placeholder='Find in file';
 findInput.setAttribute('aria-label','Find in current file');
 const findCount=document.createElement('span');
 findCount.className='pynix-find-count';
 const findPrevious=document.createElement('button');
 findPrevious.type='button';findPrevious.textContent='↑';findPrevious.title='Previous match (Shift+Enter)';
 const findNext=document.createElement('button');
 findNext.type='button';findNext.textContent='↓';findNext.title='Next match (Enter)';
 const findClose=document.createElement('button');
 findClose.type='button';findClose.textContent='×';findClose.title='Close search (Esc)';
 searchBar.append(findInput,findCount,findPrevious,findNext,findClose);
 document.querySelector('.workspace-toolbar')?.appendChild(searchBar);
 let findIndex=-1;
 function findMatches(){
   const needle=findInput.value.toLocaleLowerCase();
   const text=editorInput.value.toLocaleLowerCase();
   const positions=[];
   if(!needle)return positions;
   let offset=0;
   while((offset=text.indexOf(needle,offset))>=0){
     positions.push(offset);
     offset+=needle.length;
     if(positions.length>=10000)break;
   }
   return positions;
 }
 function decorateFindMatches(){
   if(searchBar.hidden||!findInput.value)return;
   const matches=findMatches();
   if(!matches.length)return;
   const selected=matches[findIndex];
   const length=findInput.value.length;
   const walker=document.createTreeWalker(coloredSource,NodeFilter.SHOW_TEXT);
   const nodes=[];
   let node,offset=0;
   while((node=walker.nextNode())){
     nodes.push({node,start:offset,end:offset+node.textContent.length});
     offset+=node.textContent.length;
   }
   for(const entry of nodes){
     const overlaps=[];
     for(let i=0;i<matches.length;i++){
       const start=matches[i],end=start+length;
       if(end<=entry.start)continue;
       if(start>=entry.end)break;
       overlaps.push({start:Math.max(0,start-entry.start),end:Math.min(entry.end-entry.start,end-entry.start),active:start===selected});
     }
     if(!overlaps.length)continue;
     const fragment=document.createDocumentFragment();
     const original=entry.node.textContent;
     let pos=0;
     for(const item of overlaps){
       if(item.start>pos)fragment.appendChild(document.createTextNode(original.slice(pos,item.start)));
       const mark=document.createElement('span');
       mark.className=item.active?'pynix-find-current':'pynix-find-match';
       mark.textContent=original.slice(item.start,item.end);
       fragment.appendChild(mark);
       pos=item.end;
     }
     if(pos<original.length)fragment.appendChild(document.createTextNode(original.slice(pos)));
     entry.node.replaceWith(fragment);
   }
 }
 function navigateFind(step=1,reset=false){
   const matches=findMatches();
   if(!matches.length){
     findCount.textContent=findInput.value?'0 matches':'';
     findIndex=-1;
     recolorSource();
     return;
   }
   if(reset){
     const caret=editorInput.selectionStart;
     findIndex=matches.findIndex(position=>position>=caret);
     if(findIndex<0)findIndex=0;
   }else{
     findIndex=(findIndex+step+matches.length)%matches.length;
   }
   const at=matches[findIndex];
   // Keep keyboard focus in the search field; only mark the match in the editor.
   editorInput.setSelectionRange(at,at+findInput.value.length);
   const before=editorInput.value.slice(0,at);
   const line=before.split('\\n').length-1;
   const height=parseFloat(getComputedStyle(editorInput).lineHeight);
   editorInput.scrollTop=Math.max(0,line*height-editorInput.clientHeight/2);
   findCount.textContent=(findIndex+1)+' / '+matches.length;
   recolorSource();
   // Do not call updateCursor here: it updates the visual editor caret.
 }
 function openFind(){
   if(!current||byName.get(current)?.unloaded)return;
   searchBar.hidden=false;
   const selected=editorInput.value.slice(editorInput.selectionStart,editorInput.selectionEnd);
   if(selected&&!selected.includes('\\n'))findInput.value=selected;
   findInput.focus();findInput.select();
   navigateFind(1,true);
 }
 function closeFind(){
   replaceBar.hidden=true;
   searchBar.hidden=true;
   recolorSource();
   editorInput.focus();
 }
 findInput.addEventListener('input',()=>navigateFind(1,true));
 findInput.addEventListener('keydown',e=>{
   if(e.key==='Escape'){e.preventDefault();closeFind();}
   if(e.key==='Enter'){e.preventDefault();navigateFind(e.shiftKey?-1:1);}
 });
 findNext.addEventListener('click',()=>{navigateFind(1);findInput.focus();});
 findPrevious.addEventListener('click',()=>{navigateFind(-1);findInput.focus();});
 findClose.addEventListener('click',closeFind);
 document.addEventListener('keydown',e=>{
   if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='f'){
     if(document.activeElement===editorInput||document.activeElement===findInput){
       e.preventDefault();openFind();
     }
   }
   if(e.key==='Escape'&&!searchBar.hidden&&document.activeElement===editorInput){
     e.preventDefault();closeFind();
   }
 });
 const replaceBar=document.createElement('div');
 replaceBar.className='pynix-find-bar pynix-replace-bar';
 replaceBar.hidden=true;
 const replaceInput=document.createElement('input');
 replaceInput.placeholder='Replace with';
 replaceInput.setAttribute('aria-label','Replacement text');
 const replaceOne=document.createElement('button');
 replaceOne.type='button';replaceOne.textContent='Replace';
 const replaceAll=document.createElement('button');
 replaceAll.type='button';replaceAll.textContent='All';
 replaceBar.append(replaceInput,replaceOne,replaceAll);
 document.querySelector('.workspace-toolbar')?.appendChild(replaceBar);
 function openReplace(){
   openFind();
   replaceBar.hidden=false;
   findInput.focus();
 }
 function replaceCurrent(){
   const matches=findMatches();
   if(!matches.length)return;
   const pos=matches[Math.max(0,findIndex)];
   pushUndo(byName.get(current));
   editorInput.setRangeText(replaceInput.value,pos,pos+findInput.value.length,'end');
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
   navigateFind(1,true);
   findInput.focus();
 }
 function replaceEvery(){
   const matches=findMatches();
   if(!matches.length)return;
   pushUndo(byName.get(current));
   let text=editorInput.value;
   for(let i=matches.length-1;i>=0;i--){
     const pos=matches[i];
     text=text.slice(0,pos)+replaceInput.value+text.slice(pos+findInput.value.length);
   }
   editorInput.value=text;
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
   navigateFind(1,true);
   findInput.focus();
 }
 replaceOne.addEventListener('click',replaceCurrent);
 replaceAll.addEventListener('click',replaceEvery);
 const goBar=document.createElement('div');
 goBar.className='pynix-find-bar pynix-go-bar';goBar.hidden=true;
 const goInput=document.createElement('input');
 goInput.type='number';goInput.min='1';goInput.placeholder='Go to line';
 const goButton=document.createElement('button');
 goButton.type='button';goButton.textContent='Go';
 goBar.append(goInput,goButton);
 document.querySelector('.workspace-toolbar')?.appendChild(goBar);
 function goToLine(line){
   const lines=editorInput.value.split('\\n');
   const number=Math.max(1,Math.min(lines.length,Number(line)||1));
   const offset=lines.slice(0,number-1).reduce((n,item)=>n+item.length+1,0);
   editorInput.focus();editorInput.setSelectionRange(offset,offset);
   const height=parseFloat(getComputedStyle(editorInput).lineHeight);
   editorInput.scrollTop=Math.max(0,(number-1)*height-editorInput.clientHeight/2);
   updateCursor();
 }
 goButton.addEventListener('click',()=>{goToLine(goInput.value);goBar.hidden=true;});
 goInput.addEventListener('keydown',e=>{
   if(e.key==='Enter'){e.preventDefault();goToLine(goInput.value);goBar.hidden=true;}
   if(e.key==='Escape'){e.preventDefault();goBar.hidden=true;editorInput.focus();}
 });
 document.addEventListener('keydown',e=>{
   if(!(e.metaKey||e.ctrlKey)||e.altKey&&e.key.toLowerCase()!=='f')return;
   const key=e.key.toLowerCase();
   if(key==='f'&&e.altKey&&!e.shiftKey){e.preventDefault();openReplace();}
   else if(key==='l'&&!e.shiftKey){e.preventDefault();goBar.hidden=false;goInput.focus();goInput.select();}
 });
 const projectFindBar=document.createElement('div');
 projectFindBar.className='pynix-find-bar pynix-project-find-bar';
 projectFindBar.hidden=true;
 const projectFindInput=document.createElement('input');
 projectFindInput.type='search';projectFindInput.placeholder='Search entire project';
 const projectFindButton=document.createElement('button');
 projectFindButton.type='button';projectFindButton.textContent='Search';
 const projectFindClose=document.createElement('button');
 projectFindClose.type='button';projectFindClose.textContent='×';
 projectFindBar.append(projectFindInput,projectFindButton,projectFindClose);
 document.querySelector('.workspace-toolbar')?.appendChild(projectFindBar);
 const projectResults=document.createElement('div');
 projectResults.className='pynix-project-results';
 projectResults.hidden=true;
 document.body.appendChild(projectResults);
 function positionProjectResults(){
   const rect=projectFindBar.getBoundingClientRect();
   projectResults.style.top=Math.round(rect.bottom+7)+'px';
   projectResults.style.left=Math.round(Math.max(8,rect.right-Math.min(570,window.innerWidth-16)))+'px';
   projectResults.style.width=Math.round(Math.min(570,window.innerWidth-16))+'px';
   projectResults.style.maxHeight=Math.max(100,window.innerHeight-rect.bottom-20)+'px';
 }
 function closeProjectFind(){
   projectFindBar.hidden=true;
   projectResults.hidden=true;
   editorInput.focus();
 }
 window.addEventListener('resize',()=>{if(!projectResults.hidden)positionProjectResults();});
 document.addEventListener('keydown',e=>{
   if(e.key==='Escape'&&(!projectFindBar.hidden||!projectResults.hidden)){
     e.preventDefault();e.stopImmediatePropagation();closeProjectFind();
   }
 },true);
 function runProjectFind(){
   const query=projectFindInput.value.trim();
   if(!query)return;
   positionProjectResults();
   projectResults.hidden=false;
   projectResults.textContent='Searching project…';
   const bridge=window.webkit?.messageHandlers?.pynixProjectSearch;
   if(bridge)bridge.postMessage({query});
   else projectResults.textContent='Project search requires the macOS native IDE';
 }
 projectFindButton.addEventListener('click',runProjectFind);
 projectFindInput.addEventListener('keydown',e=>{
   if(e.key==='Enter'){e.preventDefault();runProjectFind();}
   if(e.key==='Escape'){e.preventDefault();closeProjectFind();}
 });
 projectFindClose.addEventListener('click',closeProjectFind);
 document.addEventListener('keydown',e=>{
   if((e.metaKey||e.ctrlKey)&&e.shiftKey&&e.key.toLowerCase()==='f'){
     e.preventDefault();projectFindBar.hidden=false;projectFindInput.focus();projectFindInput.select();
     positionProjectResults();
   }
 });
 window.pynixProjectSearchResult=payload=>{
   if(projectFindBar.hidden)return;
   positionProjectResults();
   projectResults.replaceChildren();
   if(payload.error){projectResults.textContent=payload.error;return;}
   const head=document.createElement('div');
   head.className='pynix-project-result-head';
   head.textContent=(payload.matches||[]).length+' results'+(payload.truncated?' (first 300)':'');
   projectResults.appendChild(head);
   for(const item of payload.matches||[]){
     const entry=document.createElement('button');
     entry.type='button';entry.className='pynix-project-result';
     entry.textContent=item.source+':'+item.line+'  '+item.preview;
     entry.addEventListener('click',()=>{
       projectResults.hidden=true;projectFindBar.hidden=true;
       document.dispatchEvent(new CustomEvent('pynix:navigate',{detail:{source:item.source,line:item.line,column:item.column}}));
     });
     projectResults.appendChild(entry);
   }
 };
 const diagnosticsStatus=document.createElement('span');
 diagnosticsStatus.className='pynix-diagnostics-status';
 document.querySelector('.bottom')?.appendChild(diagnosticsStatus);
 let editing=true;
 let restoringEditor=false;
 let editorRestoreEpoch=0;
 function persistBuffer(){
   if(restoringEditor||!editing||!current)return;
   const file=byName.get(current);
   if(!file || file.unloaded)return;
   file.text=editorInput.value;
   file.dirty=file.text!==file.savedText;
   file.cursorStart=editorInput.selectionStart;
   file.cursorEnd=editorInput.selectionEnd;
   file.scrollTop=editorInput.scrollTop;
   file.scrollLeft=editorInput.scrollLeft;
 }
 editorInput.addEventListener('keyup',()=>persistBuffer());
 editorInput.addEventListener('mouseup',()=>persistBuffer());
 editorInput.addEventListener('select',()=>persistBuffer());
 editorInput.addEventListener('scroll',()=>persistBuffer());
 function updateEditingView(){
   const file=current?byName.get(current):null;
   const available=!!file&&!file.unloaded;
   editLayer.hidden=!editing||!available;
   editorInput.hidden=!editing||!available;
   code.hidden=editing&&available;
   editButton.textContent=editing?'Preview':'Edit';
   saveButton.disabled=!available||!file.dirty;
   if(editing&&available){
     // WebKit dispatches selection/scroll events while replacing textarea.value
     // and after setSelectionRange; those events must not overwrite tab state.
     const source=current;
     const epoch=++editorRestoreEpoch;
     const start=file.cursorStart??0;
     const end=file.cursorEnd??start;
     const top=file.scrollTop??0;
     const left=file.scrollLeft??0;
     restoringEditor=true;
     editorInput.value=file.text;
     recolorSource();
     editorInput.focus();
     editorInput.setSelectionRange(start,end);
     editorInput.scrollTop=top;
     editorInput.scrollLeft=left;
     recolorSource();
     updateCursor();
     requestAnimationFrame(()=>{
       if(epoch!==editorRestoreEpoch||current!==source)return;
       editorInput.setSelectionRange(start,end);
       editorInput.scrollTop=top;
       editorInput.scrollLeft=left;
       requestAnimationFrame(()=>{
         if(epoch===editorRestoreEpoch&&current===source)restoringEditor=false;
       });
     });
   }else{
     ++editorRestoreEpoch;
     restoringEditor=false;
   }
 }
 // Explicit history is needed because setRangeText and document switches do not
 // reliably participate in WebKit's native textarea undo manager.
 const undoLimit=200;
 let applyingHistory=false;
 function historyState(){
   return {text:editorInput.value,start:editorInput.selectionStart,end:editorInput.selectionEnd};
 }
 function pushUndo(file){
   if(!file||applyingHistory)return;
   const state=historyState();
   const undo=file.undoStack||(file.undoStack=[]);
   if(undo.length&&undo[undo.length-1].text===state.text)return;
   undo.push(state);
   if(undo.length>undoLimit)undo.shift();
   file.redoStack=[];
 }
 function restoreHistory(direction){
   const file=current?byName.get(current):null;
   if(!file)return;
   const from=direction==='undo'?'undoStack':'redoStack';
   const to=direction==='undo'?'redoStack':'undoStack';
   const stack=file[from]||[];
   if(!stack.length)return;
   const state=stack.pop();
   (file[to]||(file[to]=[])).push(historyState());
   applyingHistory=true;
   editorInput.value=state.text;
   editorInput.setSelectionRange(state.start,state.end);
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
   applyingHistory=false;
 }
 editorInput.addEventListener('beforeinput',e=>{
   if(e.isComposing||applyingHistory)return;
   if(e.inputType==='historyUndo'||e.inputType==='historyRedo'){
     e.preventDefault();
     restoreHistory(e.inputType==='historyUndo'?'undo':'redo');
     return;
   }
   if(e.inputType?.startsWith('insert')||e.inputType?.startsWith('delete'))
     pushUndo(byName.get(current));
 });
 function replaceSelection(text, start, end){
   pushUndo(byName.get(current));
   editorInput.focus();
   editorInput.setRangeText(text,start,end,'end');
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
   updateCursor();
 }
 function indentSelectedLines(outdent){
   pushUndo(byName.get(current));
   const value=editorInput.value;
   const start=editorInput.selectionStart,end=editorInput.selectionEnd;
   const lineStart=value.lastIndexOf('\\n',Math.max(0,start-1))+1;
   const effectiveEnd=end>lineStart&&value[end-1]==='\\n'?end-1:end;
   const lineEndIndex=value.indexOf('\\n',effectiveEnd);
   const lineEnd=lineEndIndex<0?value.length:lineEndIndex;
   const block=value.slice(lineStart,lineEnd);
   const pieces=block.split('\\n');
   let firstRemoved=0,totalDelta=0;
   const adjusted=pieces.map((line,i)=>{
     if(outdent){
       const removed=line.startsWith('\\t')?1:(line.match(/^ {1,4}/)?.[0].length||0);
       if(i===0)firstRemoved=removed;
       totalDelta-=removed;
       return line.slice(removed);
     }
     totalDelta+=4;
     return '    '+line;
   }).join('\\n');
   editorInput.setRangeText(adjusted,lineStart,lineEnd,'preserve');
   editorInput.setSelectionRange(Math.max(lineStart,start+(outdent?-firstRemoved:4)),Math.max(lineStart,end+totalDelta));
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
   updateCursor();
 }
 editorInput.addEventListener('keydown',e=>{
   if((e.metaKey||e.ctrlKey)&&!e.altKey&&e.key.toLowerCase()==='z'){
     e.preventDefault();
     restoreHistory(e.shiftKey?'redo':'undo');
     return;
   }
   if(e.key==='Tab'){
     e.preventDefault();
     const start=editorInput.selectionStart,end=editorInput.selectionEnd;
     if(e.shiftKey||editorInput.value.slice(start,end).includes('\\n')){
       indentSelectedLines(e.shiftKey);
     }else{
       replaceSelection('    ',start,end);
     }
   } else if(e.key==='Enter'&&!e.isComposing){
     e.preventDefault();
     const start=editorInput.selectionStart,end=editorInput.selectionEnd;
     const prefix=editorInput.value.slice(editorInput.value.lastIndexOf('\\n',start-1)+1,start);
     const indent=prefix.match(/^[ \\t]*/)?.[0]||'';
     replaceSelection('\\n'+indent,start,end);
   }
 });
 const coreSyncTimers=new Map();
 const coreRevisions=new Map();
 const coreConfirmedRevisions=new Map();
 window.pynixCoreBufferResult=reply=>{
   const source=reply?.source;
   const revision=reply?.revision;
   if(typeof source!=='string'||!Number.isInteger(revision))return;
   if(!byName.has(source))return;
   if(revision<(coreRevisions.get(source)||0))return;
   const status=document.querySelector('.pynix-core-bridge-indicator');
   if(!status)return;
   if(reply.ok){
     coreConfirmedRevisions.set(source,revision);
     const file=byName.get(source);
     if(file){file.coreRevision=revision;file.coreDirty=reply.dirty===true;}
     status.textContent='IDE Core: synced (revision '+revision+')';
   }else{
     status.textContent='IDE Core: sync error — '+String(reply.error||'Unknown error');
   }
 };
 function scheduleCoreBufferSync(){
   if(!current||!current.endsWith('.pnx'))return;
   const source=current;
   const content=editorInput.value;
   const bridge=window.webkit?.messageHandlers?.pynixCoreBuffer;
   if(!bridge)return;
   if(coreSyncTimers.has(source))clearTimeout(coreSyncTimers.get(source));
   const revision=(coreRevisions.get(source)||0)+1;
   coreRevisions.set(source,revision);
   coreSyncTimers.set(source,setTimeout(()=>{
     coreSyncTimers.delete(source);
     bridge.postMessage({source,text:content,revision});
   },400));
 }
 editorInput.addEventListener('input',()=>{
   persistBuffer();
   scheduleCoreBufferSync();
   recolorSource();
   updateCursor();
   const file=byName.get(current);
   if(file?.dirty)diagnosticsStatus.textContent='Diagnostics require save';
   saveButton.disabled=!file?.dirty;
   renderTabs();
 });
 editButton.addEventListener('click',()=>{persistBuffer();editing=!editing;updateEditingView();if(!editing&&current)renderCode(byName.get(current))});
 function prepareNativeSave(source,content){
   // A save is a synchronization barrier: cancel obsolete deferred editor sends
   // and allocate a newer revision for the exact bytes being saved.
   cancelCoreBufferSync(source);
   let revision=null;
   if(source.endsWith('.pnx')){
     revision=(coreRevisions.get(source)||0)+1;
     coreRevisions.set(source,revision);
   }
   return {source,text:content,revision};
 }
 function saveSource(){
   persistBuffer();
   const file=current?byName.get(current):null;
   if(!file||file.unloaded||!file.dirty)return;
   const bridge=window.webkit?.messageHandlers?.pynixFileSave;
   if(!bridge){window.alert('Native file saving is unavailable');return;}
   bridge.postMessage(prepareNativeSave(current,file.text));
 }
 saveButton.addEventListener('click',saveSource);
 // Native menu forwards to the same handlers used by toolbar and keyboard.
 window.pynixMenuCommand=command=>{
   const nav=label=>[...document.querySelectorAll('.workspace-toolbar .nav-action')]
     .find(button=>button.textContent.trim()===label)?.click();
   switch(command){
     case 'file.save': saveSource(); break;
     case 'edit.find': openFind(); break;
     case 'edit.replace': openReplace(); break;
     case 'edit.findProject':
       projectFindBar.hidden=false;
       projectFindInput.focus();projectFindInput.select();
       positionProjectResults();
       break;
     case 'edit.goToLine':
       goBar.hidden=false;goInput.focus();goInput.select();
       break;
     case 'navigate.definition': nav('Definition'); break;
     case 'navigate.references': nav('References'); break;
     case 'navigate.type': nav('Type'); break;
   }
 };

 editorInput.addEventListener('keydown',e=>{
   if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='s'){e.preventDefault();saveSource()}
 });
 window.pynixSaveResult=payload=>{
   const file=payload?.source?byName.get(payload.source):null;
   if(!file)return;
   if(payload.error){pendingCloseAfterSave=null;window.alert('Save failed: '+payload.error);return;}
   if(payload.saved){
     file.savedText=typeof payload.savedText==='string'?payload.savedText:file.text;
     file.dirty=file.text!==file.savedText;
     renderTabs();
     if(pendingCloseAfterSave===payload.source){
       pendingCloseAfterSave=null;
       if(!file.dirty){closeTabNow(payload.source);return;}
     }
     if(current===payload.source){
       updateEditingView();
       const diagnostics=payload.diagnostics||[];
       const local=diagnostics.filter(item=>item.source===payload.source||item.source?.endsWith('/'+payload.source));
       diagnosticsStatus.textContent=payload.diagnostic_error||('Problems: '+local.length);
       const panel=document.querySelector('.terminal-console');
       if(panel){
         panel.replaceChildren();
         for(const item of local){
           const entry=document.createElement('div');
           entry.className='navigation-result';
           entry.textContent=(item.line||1)+':'+(item.column||1)+' '+(item.code||'')+' '+item.message;
           panel.appendChild(entry);
         }
       }
     }
   }
 };

 const expanded = new Set(['']);
 const icon = {
  "folder": "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' > <path d='M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z' /> </svg> ",
  "folder-open": "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' > <path d='m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2' /> </svg> ",
  "file": "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' > <path d='M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z' /> <path d='M14 2v5a1 1 0 0 0 1 1h5' /> </svg> ",
  "file-code": "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' > <path d='M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z' /> <path d='M14 2v5a1 1 0 0 0 1 1h5' /> <path d='M10 12.5 8 15l2 2.5' /> <path d='m14 12.5 2 2.5-2 2.5' /> </svg> "
};
 function fileIconMarkup(type) {
   // Common SVG glyphs stay consistent with our approved Lucide family.
   if(type==='python') return `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 128 128'><linearGradient id='python-original-a' gradientUnits='userSpaceOnUse' x1='70.252' y1='1237.476' x2='170.659' y2='1151.089' gradientTransform='matrix(.563 0 0 -.568 -29.215 707.817)'><stop offset='0' stop-color='#5A9FD4'/><stop offset='1' stop-color='#306998'/></linearGradient><linearGradient id='python-original-b' gradientUnits='userSpaceOnUse' x1='209.474' y1='1098.811' x2='173.62' y2='1149.537' gradientTransform='matrix(.563 0 0 -.568 -29.215 707.817)'><stop offset='0' stop-color='#FFD43B'/><stop offset='1' stop-color='#FFE873'/></linearGradient><path fill='url(#python-original-a)' d='M63.391 1.988c-4.222.02-8.252.379-11.8 1.007-10.45 1.846-12.346 5.71-12.346 12.837v9.411h24.693v3.137H29.977c-7.176 0-13.46 4.313-15.426 12.521-2.268 9.405-2.368 15.275 0 25.096 1.755 7.311 5.947 12.519 13.124 12.519h8.491V67.234c0-8.151 7.051-15.34 15.426-15.34h24.665c6.866 0 12.346-5.654 12.346-12.548V15.833c0-6.693-5.646-11.72-12.346-12.837-4.244-.706-8.645-1.027-12.866-1.008zM50.037 9.557c2.55 0 4.634 2.117 4.634 4.721 0 2.593-2.083 4.69-4.634 4.69-2.56 0-4.633-2.097-4.633-4.69-.001-2.604 2.073-4.721 4.633-4.721z' transform='translate(0 10.26)'/><path fill='url(#python-original-b)' d='M91.682 28.38v10.966c0 8.5-7.208 15.655-15.426 15.655H51.591c-6.756 0-12.346 5.783-12.346 12.549v23.515c0 6.691 5.818 10.628 12.346 12.547 7.816 2.297 15.312 2.713 24.665 0 6.216-1.801 12.346-5.423 12.346-12.547v-9.412H63.938v-3.138h37.012c7.176 0 9.852-5.005 12.348-12.519 2.578-7.735 2.467-15.174 0-25.096-1.774-7.145-5.161-12.521-12.348-12.521h-9.268zM77.809 87.927c2.561 0 4.634 2.097 4.634 4.692 0 2.602-2.074 4.719-4.634 4.719-2.55 0-4.633-2.117-4.633-4.719 0-2.595 2.083-4.692 4.633-4.692z' transform='translate(0 10.26)'/><radialGradient id='python-original-c' cx='1825.678' cy='444.45' r='26.743' gradientTransform='matrix(0 -.24 -1.055 0 532.979 557.576)' gradientUnits='userSpaceOnUse'><stop offset='0' stop-color='#B8B8B8' stop-opacity='.498'/><stop offset='1' stop-color='#7F7F7F' stop-opacity='0'/></radialGradient><path opacity='.444' fill='url(#python-original-c)' d='M97.309 119.597c0 3.543-14.816 6.416-33.091 6.416-18.276 0-33.092-2.873-33.092-6.416 0-3.544 14.815-6.417 33.092-6.417 18.275 0 33.091 2.872 33.091 6.417z'/></svg>`;
   if(type==='markdown') return '<span class="file-mark file-mark-md">M↓</span>';
   if(type==='pynix') return '<span class="file-mark file-mark-pnx">PN</span>';
   if(type==='json') return '<span class="file-mark file-mark-json">{ }</span>';
   if(type==='settings') return '<span class="file-mark file-mark-settings">⚙</span>';
   if(type==='image') return '<span class="file-mark file-mark-image">▧</span>';
   if(type==='terminal') return '<span class="file-mark file-mark-terminal">›_</span>';
   return type==='code'?icon['file-code']:icon.file;
 }
 function buildTree() {
   const root = {children: new Map(), path:'', folder:true};
   for(const path of [...folders, ...files.map(file=>file.name)]) {
     let node = root;
     const pieces = path.split('/');
     pieces.forEach((part, i) => {
       const key = pieces.slice(0,i+1).join('/');
       if(!node.children.has(part))
         node.children.set(part, {name:part,path:key,folder:i<pieces.length-1 || folders.includes(key),children:new Map()});
       node=node.children.get(part);
     });
   }
   return root;
 }
 const root=buildTree();
 function renderTree() {
   // Preserve the source-control panel while it is selected.
   const rails=[...document.querySelectorAll('.rail-item')];
   if(rails[2]?.classList.contains('active'))return;
   tree.replaceChildren();
   const heading=document.createElement('div');
   heading.className='tree-title';
   heading.textContent='EXPLORER · '+files.length+' FILES';
   tree.appendChild(heading);
   function appendRow(entry, depth, isRoot=false) {
     const isOpen=expanded.has(entry.path);
     const line=document.createElement('div');
     line.className='entry project-entry'+(isRoot?' project-root':'');
     line.style.paddingLeft=(7+Math.min(depth,12)*13)+'px';
     if(entry.path===selectedPath)line.classList.add('workspace-selected');
     line.setAttribute('role','button');
     line.tabIndex=0;
     line.setAttribute('aria-label',(entry.folder?'Toggle ':'Open ')+entry.path);
     const chevron=document.createElement('span');
     chevron.className='project-chevron';
     if(entry.folder) {
       chevron.innerHTML='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></svg>';
       if(!isOpen)chevron.classList.add('collapsed');
     }
     line.appendChild(chevron);
     const glyph=document.createElement('span');
     const extension=entry.name.split('.').pop().toLowerCase();
     const fileType=byName.get(entry.path)?.icon || 'file';
     glyph.className='project-glyph '+(entry.folder?'folder-icon':('file-'+fileType));
     glyph.innerHTML=entry.folder?(isOpen?icon['folder-open']:icon.folder):fileIconMarkup(fileType);
     line.appendChild(glyph);
     const label=document.createElement('span');
     label.className='project-label';
     label.textContent=entry.name;
     line.appendChild(label);
     const activate=()=>{
       if(entry.folder){
         if(expanded.has(entry.path))expanded.delete(entry.path);
         else expanded.add(entry.path);
         renderTree();
       } else show(entry.path);
     };
     if(entry.folder){
       // Folder disclosure remains a single-click action.
       line.addEventListener('click',e=>{
         if(e.button!==0)return;
         activate();
       });
     } else {
       // A single click selects a file; only a double click opens its tab.
       line.addEventListener('click',e=>{
         if(e.button!==0)return;
         selectedPath=entry.path;
         renderTree();
       });
       line.addEventListener('dblclick',e=>{
         if(e.button!==0)return;
         selectedPath=entry.path;
         show(entry.path);
       });
     }
     line.addEventListener('keydown',e=>{
       if(e.key==='Enter'){e.preventDefault();activate()}
       if(e.key===' '){e.preventDefault();if(entry.folder)activate();else {selectedPath=entry.path;renderTree()}}
     });
     tree.appendChild(line);
   }
   appendRow({name:PROJECT_NAME,path:'',folder:true},0,true);
   function visit(node,depth) {
     const children=[...node.children.values()].sort((a,b)=>
       Number(b.folder)-Number(a.folder)||a.name.localeCompare(b.name));
     for(const entry of children){
       appendRow(entry,depth);
       if(entry.folder&&expanded.has(entry.path))visit(entry,depth+1);
     }
   }
   if(expanded.has(''))visit(root,1);
 }
 function renderCode(file) {
   code.replaceChildren();
   file.text.split('\\n').forEach((line, i) => {
     const row = document.createElement('div');
     row.className='source-line';
     row.dataset.line=String(i+1);
     const gutter = document.createElement('span');
     gutter.className = 'ln';
     gutter.textContent = String(i + 1);
     row.appendChild(gutter);
     const content = document.createElement('span');
     content.className='source-text';
     content.tabIndex=0;
     if(file.tokens && file.tokens[i]) {
       for(const token of file.tokens[i]){
         const span=document.createElement('span');
         span.className='pnx-token pnx-'+token.kind;
         span.textContent=token.text;
         content.appendChild(span);
       }
     } else content.textContent=line;
     row.appendChild(content);
     code.appendChild(row);
   });
 }
 let pendingCloseAfterSave=null;
 function cancelCoreBufferSync(name){
   if(coreSyncTimers.has(name)){
     clearTimeout(coreSyncTimers.get(name));
     coreSyncTimers.delete(name);
   }
 }
 function closeTabNow(name){
   cancelCoreBufferSync(name);
   const index=openTabs.indexOf(name);
   if(index<0)return;
   openTabs.splice(index,1);
   const file=byName.get(name);
   if(file){file.unloaded=true;file.text='';file.tokens=null;file.savedText=undefined;file.dirty=false;}
   if(current===name){
     current=null;
     const next=openTabs[Math.min(index,openTabs.length-1)];
     if(next){show(next);return;}
     code.replaceChildren();editing=true;updateEditingView();
   }
   renderTabs();renderTree();
 }
 function requestCloseTab(name){
   persistBuffer();
   const file=byName.get(name);
   if(!file?.dirty){closeTabNow(name);return;}
   if(document.querySelector('.pynix-unsaved-overlay'))return;
   const overlay=document.createElement('div');
   overlay.className='pynix-unsaved-overlay';
   const dialog=document.createElement('div');
   dialog.className='pynix-unsaved-dialog';
   dialog.setAttribute('role','dialog');
   dialog.setAttribute('aria-modal','true');
   dialog.setAttribute('aria-label','Unsaved changes');
   const prompt=document.createElement('p');
   prompt.textContent='Save changes to '+name+' before closing?';
   const actions=document.createElement('div');
   actions.className='pynix-unsaved-actions';
   const dismiss=()=>overlay.remove();
   const button=(text,handler)=>{
     const item=document.createElement('button');
     item.type='button';item.textContent=text;
     item.addEventListener('click',handler);actions.appendChild(item);return item;
   };
   const cancel=button('Cancel',dismiss);
   button('Don’t Save',()=>{
     dismiss();
     cancelCoreBufferSync(name);
     const bridge=window.webkit?.messageHandlers?.pynixCoreDiscard;
     if(bridge&&name.endsWith('.pnx'))bridge.postMessage({source:name});
     closeTabNow(name);
   });
   button('Save',()=>{
     if(current!==name){dismiss();show(name);}
     const selected=byName.get(name);
     if(!selected?.dirty){closeTabNow(name);return;}
     const bridge=window.webkit?.messageHandlers?.pynixFileSave;
     if(!bridge){window.alert('Native file saving is unavailable');return;}
     pendingCloseAfterSave=name;
     dismiss();bridge.postMessage(prepareNativeSave(name,selected.text));
   });
   dialog.append(prompt,actions);overlay.appendChild(dialog);
   document.body.appendChild(overlay);cancel.focus();
   overlay.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();dismiss();}});
 }
 function renderTabs(){
   tabs.replaceChildren();
   for(const fileName of openTabs){
     const file=byName.get(fileName);
     const wrap=document.createElement('div');
     wrap.className='pynix-editor-tab'+(fileName===current?' active':'');
     const label=document.createElement('button');
     label.type='button';
     label.textContent=fileName.split('/').pop()+(file?.dirty?' *':'');
     label.addEventListener('click',()=>show(fileName));
     const close=document.createElement('button');
     close.type='button';
     close.innerHTML='<svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
     close.className='pynix-editor-tab-close';
     close.setAttribute('aria-label','Close '+fileName);
     close.addEventListener('click',()=>requestCloseTab(fileName));
     wrap.append(label,close);
     tabs.appendChild(wrap);
   }
 }
 function show(name) {
   if (!byName.has(name)) return;
   persistBuffer();
   if(current && current!==name && byName.get(current)?.dirty && current.endsWith('.pnx')){
     // Flush the previous tab's pending buffer before opening another Core source.
     const source=current;
     if(coreSyncTimers.has(source)){
       clearTimeout(coreSyncTimers.get(source));
       coreSyncTimers.delete(source);
       const bridge=window.webkit?.messageHandlers?.pynixCoreBuffer;
       const revision=coreRevisions.get(source);
       if(bridge&&revision)bridge.postMessage({source,text:byName.get(source).text,revision});
     }
   }
   if (!openTabs.includes(name)) openTabs.push(name);
   current = name;
   selectedPath = name;
   const segments=name.split('/');
   for(let i=1;i<segments.length;i++)expanded.add(segments.slice(0,i).join('/'));
   renderTabs();
   searchBar.hidden=true;
   findIndex=-1;
   const file=byName.get(name);
   if(file.savedText===undefined && !file.unloaded)file.savedText=file.text;
   editing=true;
   if(file.unloaded){
     code.replaceChildren();
     const info=document.createElement('div');
     info.className='source-unloaded';
     info.textContent='Loading '+name+'...';
     code.appendChild(info);
     const bridge=window.webkit?.messageHandlers?.pynixFileOpen;
     if(bridge)bridge.postMessage({source:name});
     else info.textContent='File contents unavailable outside the native IDE.';
   } else renderCode(file);
   updateEditingView();
   document.dispatchEvent(new CustomEvent('pynix:file-opened',{detail:{source:name}}));
   renderTree();
 }
 let pendingNavigation=null;
 function selectNavigationLocation(target){
   if(current!==target.source)return;
   const lines=editorInput.value.split('\\n');
   const line=Math.max(1,Math.min(lines.length,Number(target.line)||1));
   const col=Math.max(1,Number(target.column)||1);
   const offset=lines.slice(0,line-1).reduce((total,item)=>total+item.length+1,0)
       +Math.min(lines[line-1].length,col-1);
   editorInput.focus();
   editorInput.setSelectionRange(offset,offset);
   const rowHeight=parseFloat(getComputedStyle(editorInput).lineHeight);
   editorInput.scrollTop=Math.max(0,(line-1)*rowHeight-editorInput.clientHeight/2);
   updateCursor();
 }
 window.pynixReceiveFile=function(payload){
   if(!payload || !byName.has(payload.source))return;
   const file=byName.get(payload.source);
   if(payload.error){
     if(current===payload.source){
       code.replaceChildren();
       const message=document.createElement('div');
       message.className='source-unloaded';
       message.textContent=payload.error;
       code.appendChild(message);
     }
     return;
   }
   file.text=payload.text;
   file.savedText=payload.text;
   file.dirty=false;
   file.tokens=payload.tokens||null;
   file.unloaded=false;
   if(current===payload.source){
     renderCode(file);updateEditingView();
     if(pendingNavigation?.source===payload.source){
       selectNavigationLocation(pendingNavigation);
       pendingNavigation=null;
     }
   }
 };
 document.addEventListener('pynix:navigate',event=>{
   const target=event.detail||{};
   if(!byName.has(target.source))return;
   pendingNavigation=target;
   show(target.source);
   if(!byName.get(target.source).unloaded){
     selectNavigationLocation(target);
     pendingNavigation=null;
   }
 });
 const explorerControl=document.querySelectorAll('.rail-item')[0];
 explorerControl?.addEventListener('click',()=>renderTree());
 explorerControl?.addEventListener('keydown',e=>{
   if(e.key==='Enter'||e.key===' ')queueMicrotask(()=>renderTree());
 });
 const sourceControl = document.querySelectorAll('.rail-item')[2];
 sourceControl?.addEventListener('click', () => {
   // Source Control remains the visual-only demonstration mode.
 });
 show(files[0].name);
})();
</script>""".replace("PROJECT_NAME_PAYLOAD", json.dumps(session.root.name, ensure_ascii=False)).replace("FOLDER_PAYLOAD", folder_payload).replace("PAYLOAD", payload)


def attach_workspace(html_source: str, session: WorkspaceSession) -> str:
    if "</body>" not in html_source:
        raise ValueError("Missing HTML body")
    # The project caption is data, not HTML; escape before inserting.
    escaped_name = html.escape(session.root.name)
    html_source = html_source.replace("PYNIX</b> / Icon System",
                                      "PYNIX</b> / " + escaped_name, 1)
    html_source = html_source.replace("⑂ feature/icon-system-v4",
                                      "Project · read-only", 1)
    html_source = html_source.replace("▾ main.pnx", "▾ Project files", 1)
    html_source = html_source.replace("⑂ main · 1 modified", "Project · read-only", 1)
    return html_source.replace("</body>", workspace_bootstrap(session) + "</body>", 1)


def attach_git_snapshot(html_source: str, snapshot) -> str:
    """Replace the mock Source Control with the actual read-only Git snapshot."""
    payload = json.dumps({
        "available": snapshot.available,
        "branch": snapshot.branch,
        "changes": [{"status": item.status, "path": item.path} for item in snapshot.changes],
        "history": list(snapshot.history),
    }, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    script = """<script>
(() => {
 const data = GIT_PAYLOAD;
 if (!document.body.classList.contains('workspace-mode')) return;
 const rail = document.querySelectorAll('.rail-item')[2];
 const tree = document.querySelector('.tree');
 if (!rail || !tree) return;
 const setText = (parent, cls, value) => {
   const el = document.createElement('div');
   el.className = cls; el.textContent = value; parent.appendChild(el);
 };
 function render() {
   if (!rail.classList.contains('active')) return;
   tree.replaceChildren();
   setText(tree,'tree-title','SOURCE CONTROL');
   if(!data.available){
     setText(tree,'git-hint','No Git repository at this project root');
     return;
   }
   setText(tree,'git-branch-title','Branch · '+data.branch);
   setText(tree,'git-section-label','CHANGES ('+data.changes.length+')');
   if(!data.changes.length) setText(tree,'git-change','Working tree clean');
   for(const change of data.changes)
     setText(tree,'git-change',change.status+'  '+change.path);
   setText(tree,'git-section-label','HISTORY');
   for(const entry of data.history) setText(tree,'git-change',entry);
   setText(tree,'git-hint','Read-only Git status · no Git command will run');
 }
 rail.addEventListener('click',()=>queueMicrotask(render));
 rail.addEventListener('keydown',e=>{
   if(e.key==='Enter'||e.key===' ')queueMicrotask(render);
 });
})();
</script>""".replace("GIT_PAYLOAD", payload)
    if "</body>" not in html_source:
        raise ValueError("Missing HTML body")
    return html_source.replace("</body>", script + "</body>", 1)


def attach_diagnostics(html_source: str, snapshot) -> str:
    """Present compiler-provided problems; never execute code from diagnostics."""
    payload = json.dumps({
        "error": snapshot.error,
        "problems": [{"source": p.source, "line": p.line, "column": p.column,
                      "code": p.code, "message": p.message}
                     for p in snapshot.problems],
    }, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    script = """<script>
(() => {
 const data = PROBLEMS_PAYLOAD;
 if(!document.body.classList.contains('workspace-mode'))return;
 const tabs = document.querySelector('.terminal-tabs');
 const consoleArea = document.querySelector('.terminal-console');
 if(!tabs || !consoleArea)return;
 const problemsTab = [...tabs.children].find(el=>el.textContent.trim()==='PROBLEMS');
 const terminalTab = [...tabs.children].find(el=>el.textContent.trim()==='TERMINAL');
 if(!problemsTab || !terminalTab)return;
 const original = consoleArea.innerHTML;
 const displayProblems = () => {
   for(const child of tabs.children)child.classList.remove('active-tool-tab');
   problemsTab.classList.add('active-tool-tab');
   consoleArea.replaceChildren();
   const message = text => {
     const row=document.createElement('div');
     row.className='diagnostic-row';row.textContent=text;
     consoleArea.appendChild(row);
   };
   if(data.error)message(data.error);
   else if(!data.problems.length)message('No compiler diagnostics');
   for(const problem of data.problems)
     message(problem.source+':'+problem.line+':'+problem.column+'  '+
             problem.code+'  '+problem.message);
 };
 problemsTab.addEventListener('click', displayProblems);
 terminalTab.addEventListener('click', () => {
   for(const child of tabs.children)child.classList.remove('active-tool-tab');
   consoleArea.innerHTML=original;
 });
})();
</script>""".replace("PROBLEMS_PAYLOAD", payload)
    if "</body>" not in html_source:
        raise ValueError("Missing HTML body")
    return html_source.replace("</body>", script+"</body>", 1)


def attach_navigation(html_source: str, result: dict, command: str) -> str:
    """Attach explicitly queried language navigation to a read-only output pane."""
    payload = json.dumps({"command": command, "result": result},
                         ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    script = """<script>
(() => {
 const payload = NAV_PAYLOAD;
 if(!document.body.classList.contains('workspace-mode')) return;
 const tabs = document.querySelector('.terminal-tabs');
 const panel = document.querySelector('.terminal-console');
 const output = [...tabs.children].find(el=>el.textContent.trim()==='OUTPUT');
 if(!output || !panel)return;
 output.addEventListener('click', () => {
   panel.replaceChildren();
   const print=(value)=>{
     const row=document.createElement('div');
     row.className='navigation-result';
     row.textContent=value;
     panel.appendChild(row);
   };
   const result=payload.result;
   if(result.error){print(result.error);return;}
   print('PYNIX tooling · '+payload.command);
   if(payload.command==='definition'){
     const d=result.definition;
     print(d?((d.qualifiedName||d.name||'')+' · '+d.source+':'+(d.start?.line||1)):'No definition at this position');
   } else if(payload.command==='references'){
     print('References: '+(result.references||[]).length);
     for(const ref of (result.references||[]).slice(0,200))
       print(ref.source+':'+(ref.start?.line||1)+':'+(ref.start?.column||1));
   } else if(payload.command==='type-at'){
     const e=result.expression;
     print(e?JSON.stringify(e):'No expression at this position');
   }
 });
})();
</script>""".replace("NAV_PAYLOAD", payload)
    if "</body>" not in html_source:
        raise ValueError("Missing HTML body")
    return html_source.replace("</body>", script+"</body>", 1)

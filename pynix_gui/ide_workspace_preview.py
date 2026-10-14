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
 window.pynixIndexedSources=files.map(file=>file.name);
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
 const inlineHint=document.createElement('span');
 inlineHint.className='pynix-inline-completion';
 inlineHint.hidden=true;
 inlineHint.setAttribute('aria-hidden','true');
 editLayer.append(gutter,activeLine,coloredSource,editorInput,customCaret,inlineHint);
 const cursorStatus=document.createElement('span');
 cursorStatus.className='pynix-cursor-status';
 document.querySelector('.bottom')?.appendChild(cursorStatus);
 function updateCursor(){
   if(!current)return;
   const before=editorInput.value.slice(0,editorInput.selectionStart);
   const line=before.split('\\n').length;
   const column=before.length-before.lastIndexOf('\\n');
   const extraCount=byName.get(current)?.extraSelections?.length||0;
   cursorStatus.textContent='Ln '+line+', Col '+column+(extraCount?' · '+(extraCount+1)+' cursors':'');
   const metrics=getComputedStyle(editorInput);
   const lineHeight=parseFloat(metrics.lineHeight);
   const topPadding=parseFloat(metrics.paddingTop);
   activeLine.hidden=restoringEditor||document.activeElement!==editorInput;
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
   inlineHint.style.transform=customCaret.style.transform;
   customCaret.hidden=restoringEditor||editorInput.selectionStart!==editorInput.selectionEnd||document.activeElement!==editorInput;

   const file=byName.get(current);
   if(file){file.cursorStart=editorInput.selectionStart;file.cursorEnd=editorInput.selectionEnd;file.scrollTop=editorInput.scrollTop;file.scrollLeft=editorInput.scrollLeft;}
 }
 editorInput.addEventListener('pointerdown',event=>{
   const file=current?byName.get(current):null;
   if(!file)return;
   if(!event.altKey){file.extraSelections=[];return;}
   // Monospaced, unwrapped text permits deterministic Option+Click caret offsets.
   event.preventDefault();
   const rect=editorInput.getBoundingClientRect();
   const style=getComputedStyle(editorInput);
   const height=parseFloat(style.lineHeight)||21;
   const top=parseFloat(style.paddingTop)||0;
   const left=parseFloat(style.paddingLeft)||0;
   const canvas=document.createElement('canvas');
   const ctx=canvas.getContext('2d');
   ctx.font=style.fontSize+' '+style.fontFamily;
   const advance=ctx.measureText('0000000000').width/10||8;
   const row=Math.max(0,Math.floor((event.clientY-rect.top-top+editorInput.scrollTop)/height));
   const column=Math.max(0,Math.round((event.clientX-rect.left-left+editorInput.scrollLeft)/advance));
   const lines=editorInput.value.split('\\n');
   const line=Math.min(row,lines.length-1);
   const position=lines.slice(0,line).reduce((sum,value)=>sum+value.length+1,0)
     +Math.min(column,lines[line].length);
   const previous={start:editorInput.selectionStart,end:editorInput.selectionEnd};
   if(position===previous.start&&previous.start===previous.end)return;
   const extras=file.extraSelections||(file.extraSelections=[]);
   if(!extras.some(item=>item.start===previous.start&&item.end===previous.end))
     extras.push(previous);
   editorInput.focus();
   editorInput.setSelectionRange(position,position);
   recolorSource();updateCursor();
 });
 editorInput.addEventListener('click',()=>{updateCursor();recolorSource();});
 editorInput.addEventListener('focus',()=>{updateCursor();recolorSource();});
 editorInput.addEventListener('blur',()=>{customCaret.hidden=true;});
 editorInput.addEventListener('keyup',()=>{updateCursor();recolorSource();});
 editorInput.addEventListener('select',()=>{updateCursor();recolorSource();});
 code.parentElement.appendChild(editLayer);
 function escapeCode(v){return v.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
 function matchingBracketPositions(value,caret){
   const pairs={'(':')','[':']','{':'}',')':'(',']':'[','}':'{'};
   const candidate=pairs[value[caret]]?caret:
     (caret>0&&pairs[value[caret-1]]?caret-1:caret);
   const symbol=value[candidate];
   if(!pairs[symbol])return new Set();
   // Ignore structural punctuation occurring inside quoted literals/comments.
   const masked=new Uint8Array(value.length);
   const ignored=/(?:\\/\\/[^\\n]*|#[^\\n]*|"(?:\\\\.|[^"\\\\])*"|'(?:\\\\.|[^'\\\\])*')/g;
   let token;
   while((token=ignored.exec(value))){
     for(let j=token.index;j<ignored.lastIndex;j++)masked[j]=1;
   }
   if(masked[candidate])return new Set();
   const open='([{'.includes(symbol);
   const direction=open?1:-1;
   const match=pairs[symbol];
   let depth=0;
   for(let pos=candidate;pos>=0&&pos<value.length;pos+=direction){
     if(masked[pos])continue;
     if(value[pos]===symbol)depth++;
     else if(value[pos]===match&&--depth===0)return new Set([candidate,pos]);
   }
   return new Set([candidate]);
 }
 function recolorSource(){
   const value=editorInput.value;
   // The lexer consumes one token at a time. Strings/comments are atomic:
   // numbers inside // comments, # comments or quoted strings stay in that color.
   const token=/(?:\\/\\/[^\\n]*|#[^\\n]*|"(?:\\\\.|[^"\\\\])*"|'(?:\\\\.|[^'\\\\])*'|[(){}\\[\\]]|\\b[A-Za-z_][A-Za-z_0-9]*\\b|\\b\\d+(?:\\.\\d+)?\\b)/g;
   const words=new Set(['function','module','import','from','as','let','var','const','if','else','elif','while','for','in','return','break','continue','and','or','not','class','interface','type','enum','match','case','try','catch','finally','raise','public','private','async','await']);
   const types=new Set(['Int','Float','Bool','String','Void','Any','List','Map']);
   const matching=matchingBracketPositions(value,editorInput.selectionStart);
   const secondary=byName.get(current)?.extraSelections||[];
   function decorateSegment(segment,at){
     const end=at+segment.length;
     const stops=new Set([at,end]);
     for(const range of secondary){
       if(range.start>=at&&range.start<=end)stops.add(range.start);
       if(range.end>=at&&range.end<=end)stops.add(range.end);
     }
     const edges=[...stops].sort((a,b)=>a-b);
     let result='';
     for(let i=0;i<edges.length;i++){
       const left=edges[i];
       if(secondary.some(range=>range.start===left&&range.end===left))
         result+='<span class="pynix-secondary-caret"></span>';
       if(i+1>=edges.length)break;
       const right=edges[i+1];
       const selected=secondary.some(range=>range.start<=left&&range.end>=right&&range.end>range.start);
       const text=escapeCode(value.slice(left,right));
       result+=selected?'<span class="pynix-secondary-selection">'+text+'</span>':text;
     }
     return result;
   }
   let html='',last=0,match;
   while((match=token.exec(value))){
     html+=decorateSegment(value.slice(last,match.index),last);
     const t=match[0];
     let kind='plain';
     if(t.startsWith('//')||t.startsWith('#'))kind='comment';
     else if(t[0]==='"'||t[0]==="'")kind='string';
     else if(/^\\d/.test(t))kind='number';
     else if(matching.has(match.index))kind='bracket-match';
     else if(words.has(t))kind='keyword';
     else if(types.has(t))kind='type';
     else if(['print','input','len','range','str','int','float'].includes(t))kind='builtin';
     else if(/^[A-Za-z_]/.test(t)&&/^\\s*\\(/.test(value.slice(token.lastIndex)))kind='call';
     else if(['true','false','none','null'].includes(t))kind='constant';
     html+='<span class="pynix-edit-'+kind+'">'+decorateSegment(t,match.index)+'</span>';
     last=token.lastIndex;
   }
   coloredSource.innerHTML=html+decorateSegment(value.slice(last),last)+'\\n';
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
 const foldButton=document.createElement('button');
 foldButton.type='button';foldButton.className='nav-action pynix-fold-action';
 foldButton.textContent='Fold';
 const unfoldButton=document.createElement('button');
 unfoldButton.type='button';unfoldButton.className='nav-action pynix-unfold-action';
 unfoldButton.textContent='Unfold';
 document.querySelector('.workspace-toolbar')?.append(foldButton,unfoldButton);
 foldButton.addEventListener('click',()=>{
   persistBuffer();
   const file=current?byName.get(current):null;
   if(!file||file.unloaded)return;
   const line=editorInput.value.slice(0,editorInput.selectionStart).split('\\n').length-1;
   const ranges=foldableLines(file.text);
   const candidates=[...ranges].filter(([start,end])=>start<=line&&end>=line);
   const header=candidates.length?candidates[candidates.length-1][0]:null;
   if(header===null)return;
   (file.foldedLines||(file.foldedLines=new Set())).add(header);
   editing=false;updateEditingView();renderCode(file);
 });
 unfoldButton.addEventListener('click',()=>{
   const file=current?byName.get(current):null;
   if(!file)return;
   file.foldedLines=new Set();
   renderCode(file);
 });
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
 const runButton=document.createElement('button');
 runButton.type='button';runButton.className='nav-action pynix-run-action';
 runButton.textContent='Run';
 const stopButton=document.createElement('button');
 stopButton.type='button';stopButton.className='nav-action pynix-stop-action';
 stopButton.textContent='Stop';stopButton.disabled=true;
 document.querySelector('.workspace-toolbar')?.append(runButton,stopButton);
 let isProjectRunning=false;
 function runProjectAction(action){
   if(action==='run'){
     persistBuffer();
     if([...byName.values()].some(file=>file.dirty)){
       window.alert('Save all changes before running the PYNIX project.');return;
     }
   }
   const bridge=window.webkit?.messageHandlers?.pynixProjectRun;
   if(!bridge){window.alert('Run/Stop requires native PYNIX IDE');return;}
   bridge.postMessage({action});
 }
 runButton.addEventListener('click',()=>runProjectAction('run'));
 stopButton.addEventListener('click',()=>runProjectAction('stop'));
 window.pynixProjectRunResult=packet=>{
   const state=packet?.state||'error';
   if(state==='running')isProjectRunning=true;
   if(state==='finished'||state==='error'||state==='idle')isProjectRunning=false;
   runButton.disabled=isProjectRunning;
   stopButton.disabled=!isProjectRunning;
   const tabs=document.querySelector('.terminal-tabs');
   const consolePanel=document.querySelector('.terminal-console');
   const consoleTab=[...tabs?.children||[]].find(item=>item.textContent.trim()==='TERMINAL');
   consoleTab?.click();
   if(!consolePanel)return;
   if(state==='running')consolePanel.textContent='Running PYNIX project…';
   else if(state==='stopping')consolePanel.textContent+='\\nStopping…';
   else if(state==='finished')
     consolePanel.textContent=(packet.output||'')+
       '\\nProcess exited: '+packet.exitCode+(packet.timedOut?' (timeout)':'')+
       (packet.truncated?' (output truncated)':'');
   else if(state==='error')consolePanel.textContent='Run failed: '+String(packet.error||'unknown error');
 };
 const diagnosticsButton=document.createElement('button');
 diagnosticsButton.type='button';
 diagnosticsButton.className='nav-action pynix-diagnostics-action';
 diagnosticsButton.textContent='Problems';
 diagnosticsButton.title='Run saved-project compiler diagnostics';
 document.querySelector('.workspace-toolbar')?.appendChild(diagnosticsButton);
 diagnosticsButton.addEventListener('click',()=>{
   const bridge=window.webkit?.messageHandlers?.pynixDiagnostics;
   const status=document.querySelector('.pynix-diagnostics-status');
   if(status)status.textContent='Checking saved project…';
   if(bridge)bridge.postMessage({});
   else if(status)status.textContent='Compiler diagnostics require native IDE';
 });
 window.pynixLiveDiagnosticsResult=payload=>{
   const status=document.querySelector('.pynix-diagnostics-status');
   const tabs=document.querySelector('.terminal-tabs');
   const panel=document.querySelector('.terminal-console');
   const problems=Array.isArray(payload?.problems)?payload.problems:[];
   if(status)status.textContent=payload?.error?'Diagnostics: '+payload.error:
      'Problems: '+problems.length+' (saved project)';
   if(!tabs||!panel)return;
   const problemsTab=[...tabs.children].find(item=>item.textContent.trim()==='PROBLEMS');
   problemsTab?.click();
   panel.replaceChildren();
   if(payload?.error){panel.textContent=String(payload.error);return;}
   if(!problems.length){panel.textContent='No compiler problems in saved project';return;}
   for(const item of problems.slice(0,200)){
     const row=document.createElement('button');
     row.type='button';row.className='navigation-result nav-location';
     row.textContent=(item.source||'')+':'+(item.line||1)+':'+(item.column||1)+
       ' '+(item.code||'')+' '+(item.message||'');
     row.addEventListener('click',()=>document.dispatchEvent(
       new CustomEvent('pynix:navigate',{detail:{source:item.source,line:item.line||1}})));
     panel.appendChild(row);
   }
 };
 const diagnosticsStatus=document.createElement('span');
 diagnosticsStatus.className='pynix-diagnostics-status';
 document.querySelector('.bottom')?.appendChild(diagnosticsStatus);
 let editing=true;
 let restoringEditor=false;
 let editorRestoreEpoch=0;
 window.pynixHasUnsavedSource=source=>{
   const file=byName.get(source);
   if(!file)return false;
   if(source===current&&editing&&!editorInput.hidden)
     return editorInput.value!==file.savedText;
   return file.text!==file.savedText;
 };
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
         if(epoch===editorRestoreEpoch&&current===source){
           restoringEditor=false;updateCursor();
         }
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
 const completionButton=document.createElement('button');
 completionButton.type='button';
 completionButton.className='nav-action pynix-completion-action';
 completionButton.textContent='Complete';
 completionButton.title='Suggest keywords and identifiers in the current source (Ctrl+Space)';
 document.querySelector('.workspace-toolbar')?.appendChild(completionButton);
 completionButton.addEventListener('click',()=>{
   if(!current||!editing||editorInput.hidden)return;
   editorInput.focus();
   window.webkit?.messageHandlers?.pynixProjectSymbols?.postMessage({});
   offerCompletion();
 });
 const completionBox=document.createElement('div');
 completionBox.className='pynix-completion-popup';
 completionBox.hidden=true;
 completionBox.setAttribute('role','listbox');
 editLayer.appendChild(completionBox);
 let compilerSymbols=[];
 const compilerSymbolKinds=new Map();
 window.pynixProjectSymbolsResult=packet=>{
   if(Array.isArray(packet?.symbols)){
     compilerSymbolKinds.clear();
     compilerSymbols=packet.symbols.filter(item=>item&&typeof item.name==='string')
       .slice(0,1200).map(item=>{
         if(typeof item.kind==='string')compilerSymbolKinds.set(item.name,item.kind);
         return item.name;
       });
   }
   if(!completionBox.hidden)offerCompletion();
 };
 let completionChoices=[];
 let completionIndex=0;
 let completionRange=null;
 const completionKeywords=['function','import','module','let','const','if','else','elif','for','while',
   'return','break','continue','class','interface','type','enum','match','case',
   'try','catch','finally','true','false','none'];
 function closeCompletion(){
   completionBox.hidden=true;
   completionChoices=[];
   completionRange=null;
 }
 function completionPrefix(){
   if(!current||!editing||editorInput.hidden||
     editorInput.selectionStart!==editorInput.selectionEnd)return null;
   const end=editorInput.selectionStart;
   const before=editorInput.value.slice(0,end);
   const match=before.match(/[A-Za-z_][A-Za-z0-9_]*$/);
   return {start:match?end-match[0].length:end,end,prefix:match?match[0]:''};
 }
 function paintCompletion(){
   completionBox.replaceChildren();
   completionChoices.forEach((word,i)=>{
     const item=document.createElement('button');
     item.type='button';
     item.className='pynix-completion-option'+(i===completionIndex?' selected':'');
     const kind=compilerSymbolKinds.get(word)||
       (completionKeywords.includes(word)?'keyword':'local');
     item.textContent=word+'  ·  '+kind;
     item.title=kind==='local'?'Identifier in current source':'PYNIX '+kind;
     item.setAttribute('role','option');
     item.setAttribute('aria-selected',i===completionIndex?'true':'false');
     item.addEventListener('mousedown',event=>event.preventDefault());
     item.addEventListener('click',()=>applyCompletion(i));
     completionBox.appendChild(item);
   });
 }
 let inlineSuggestion=null;
 function refreshInlineCompletion(){
   inlineHint.hidden=true;inlineSuggestion=null;
   if(restoringEditor||document.activeElement!==editorInput||
      !completionBox.hidden||byName.get(current)?.extraSelections?.length)return;
   const range=completionPrefix();
   if(!range||range.prefix.length<2)return;
   const source=editorInput.value;
   const names=source.match(/\\b[A-Za-z_][A-Za-z0-9_]*\\b/g)||[];
   const candidate=[...new Set([...completionKeywords,...compilerSymbols,...names])]
     .find(word=>word!==range.prefix&&word.startsWith(range.prefix));
   if(!candidate)return;
   inlineSuggestion={...range,word:candidate};
   inlineHint.textContent=candidate.slice(range.prefix.length);
   inlineHint.hidden=false;
 }
 function acceptInlineCompletion(){
   const candidate=inlineSuggestion;
   if(!candidate||document.activeElement!==editorInput)return false;
   if(editorInput.selectionStart!==candidate.end||editorInput.selectionEnd!==candidate.end||
      editorInput.value.slice(candidate.start,candidate.end)!==candidate.prefix)return false;
   inlineHint.hidden=true;inlineSuggestion=null;
   replaceSelection(candidate.word,candidate.start,candidate.end);
   editorInput.setSelectionRange(candidate.start+candidate.word.length,candidate.start+candidate.word.length);
   updateCursor();
   return true;
 }
 function offerCompletion(){
   const range=completionPrefix();
   if(!range){closeCompletion();return;}
   const source=editorInput.value;
   const identifiers=source.match(/\\b[A-Za-z_][A-Za-z0-9_]*\\b/g)||[];
   const choices=[...new Set([...completionKeywords,...compilerSymbols,...identifiers])]
     .filter(word=>word.startsWith(range.prefix)&&word!==range.prefix)
     .sort((a,b)=>a.localeCompare(b)).slice(0,30);
   if(!choices.length){closeCompletion();return;}
   completionRange=range;
   completionChoices=choices;
   completionIndex=0;
   paintCompletion();
   completionBox.hidden=false;
 }
 function applyCompletion(index){
   const range=completionRange,word=completionChoices[index];
   if(!range||!word||!current)return;
   if(editorInput.selectionStart!==range.end||editorInput.selectionEnd!==range.end||
       editorInput.value.slice(range.start,range.end)!==range.prefix){
     closeCompletion();return;
   }
   closeCompletion();
   replaceSelection(word,range.start,range.end);
 }
  editorInput.addEventListener('keydown',event=>{
   if(event.key==='Tab'&&!event.shiftKey&&!event.altKey&&!event.ctrlKey&&!event.metaKey&&completionBox.hidden&&acceptInlineCompletion()){
     event.preventDefault();event.stopImmediatePropagation();
   }
 },true);
editorInput.addEventListener('keydown',event=>{
   if(event.ctrlKey&&!event.metaKey&&event.code==='Space'&&!event.altKey){
     event.preventDefault();
     window.webkit?.messageHandlers?.pynixProjectSymbols?.postMessage({});
     offerCompletion();return;
   }
   if(completionBox.hidden)return;
   if(event.key==='Escape'){event.preventDefault();closeCompletion();return;}
   if(event.key==='ArrowDown'||event.key==='ArrowUp'){
     event.preventDefault();
     completionIndex=(completionIndex+(event.key==='ArrowDown'?1:-1)+completionChoices.length)%completionChoices.length;
     paintCompletion();return;
   }
   if(event.key==='Tab'||event.key==='Enter'){
     event.preventDefault();applyCompletion(completionIndex);
   }
 },true);
 editorInput.addEventListener('input',()=>{
   if(!completionBox.hidden)offerCompletion();
   refreshInlineCompletion();
 });
 editorInput.addEventListener('click',refreshInlineCompletion);
 editorInput.addEventListener('keyup',refreshInlineCompletion);
 editorInput.addEventListener('select',refreshInlineCompletion);
 editorInput.addEventListener('blur',()=>{closeCompletion();inlineHint.hidden=true;inlineSuggestion=null;});
 const renameButton=document.createElement('button');
 renameButton.type='button';renameButton.className='nav-action pynix-rename-action';
 renameButton.textContent='Rename Local';
 document.querySelector('.workspace-toolbar')?.appendChild(renameButton);
 function selectedIdentifier(){
   const value=editorInput.value;
   let start=editorInput.selectionStart,end=editorInput.selectionEnd;
   if(start===end){
     while(start>0&&/[A-Za-z0-9_]/.test(value[start-1]))start--;
     while(end<value.length&&/[A-Za-z0-9_]/.test(value[end]))end++;
   }
   const word=value.slice(start,end);
   return /^[A-Za-z_][A-Za-z0-9_]*$/.test(word)?word:null;
 }
 function renameLocalIdentifier(){
   if(!current||!editing||editorInput.hidden)return;
   const old=selectedIdentifier();
   if(!old){window.alert('Select a PYNIX identifier to rename');return;}
   const replacement=window.prompt('Rename occurrences in CURRENT file (textual, not semantic):',old);
   if(replacement===null||replacement===old)return;
   if(!/^[A-Za-z_][A-Za-z0-9_]*$/.test(replacement)){
     window.alert('New name must be a valid identifier');return;
   }
   const lexer=/(?:\\/\\/[^\\n]*|#[^\\n]*|"(?:\\\\.|[^"\\\\])*"|'(?:\\\\.|[^'\\\\])*'|[A-Za-z_][A-Za-z_0-9]*)/g;
   const matches=[...editorInput.value.matchAll(lexer)]
     .filter(match=>match[0]===old).map(match=>match.index);
   if(!matches.length)return;
   if(!window.confirm('Replace '+matches.length+' code identifiers named '+old+
       ' in '+current+'? Scope shadowing is not analyzed. Undo is available.'))return;
   pushUndo(byName.get(current));
   let changed=editorInput.value;
   for(const index of [...matches].reverse())
     changed=changed.slice(0,index)+replacement+changed.slice(index+old.length);
   editorInput.value=changed;
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
 }
 renameButton.addEventListener('click',renameLocalIdentifier);
 editorInput.addEventListener('keydown',event=>{
   // F2 is reserved for compiler-backed Rename Symbol; Shift+F2 uses Rename Local.
 });
 const semanticRenameButton=document.createElement('button');
 semanticRenameButton.type='button';
 semanticRenameButton.className='nav-action pynix-semantic-rename';
 semanticRenameButton.textContent='Rename Symbol';
 semanticRenameButton.title='Compiler-verified cross-file rename (F2); review unsaved buffers before saving';
 document.querySelector('.workspace-toolbar')?.appendChild(semanticRenameButton);
 function requestSemanticRename(){
   if(!current||!current.endsWith('.pnx')||!editing||editorInput.hidden)return;
   persistBuffer();
   if([...byName.values()].some(file=>file.dirty)){
     window.alert('Save all modified files before semantic rename.');return;
   }
   if(coreRecovering){
     window.alert('Restore IDE Core before semantic rename.');return;
   }
   const symbol=selectedIdentifier();
   if(!symbol){window.alert('Place the caret on a PYNIX symbol');return;}
   const newName=window.prompt('Rename resolved symbol throughout the project:',symbol);
   if(newName===null||newName===symbol)return;
   if(!/^[A-Za-z_][A-Za-z_0-9]*$/.test(newName)){
     window.alert('New name must be a PYNIX identifier');return;
   }
   const bridge=window.webkit?.messageHandlers?.pynixSemanticRename;
   if(!bridge){window.alert('Compiler rename requires the native IDE');return;}
   const before=editorInput.value.slice(0,editorInput.selectionStart);
   const line=before.split('\\n').length;
   const column=before.length-before.lastIndexOf('\\n');
   bridge.postMessage({source:current,line,column,newName});
 }
 window.pynixSemanticRenamePlan=packet=>{
   if(packet?.error){window.alert('Rename unavailable: '+packet.error);return;}
   const changes=packet?.files;
   if(!Array.isArray(changes)||!changes.length||changes.length>100)return;
   persistBuffer();
   // Preflight every document BEFORE changing any editor buffers.
   if(changes.some(item=>{
     const file=byName.get(item?.source);
     return !file||typeof item.before!=='string'||typeof item.after!=='string'||
       (!file.unloaded&&(file.text!==item.before||file.savedText!==item.before))||
       (current===item.source&&!file.unloaded&&editorInput.value!==item.before);
   })){
     window.alert('Rename aborted: open all affected sources and save changes, then retry.');return;
   }
   const bridge=window.webkit?.messageHandlers?.pynixCoreBuffer;
   if(!bridge||coreRecovering){
     window.alert('Rename requires an available IDE Core buffer bridge.');return;
   }
   if(!window.confirm('Rename '+packet.symbol+' → '+packet.newName+' in '+
       changes.length+' file(s), '+packet.occurrences+' verified occurrences? '+
       'Changes remain UNSAVED. Review every tab and save manually.'))return;
   for(const item of changes){
     const file=byName.get(item.source);
     if(file.unloaded){
       // Compiler plan and native Core preflight verified these exact bytes.
       file.text=item.before;file.savedText=item.before;file.unloaded=false;
     }
     const undo=file.undoStack||(file.undoStack=[]);
     undo.push({text:item.before,start:file.cursorStart||0,end:file.cursorEnd||0,extraSelections:[]});
     if(undo.length>undoLimit)undo.shift();
     file.redoStack=[];
     file.text=item.after;
     file.dirty=true;
     file.extraSelections=[];
     if(!openTabs.includes(item.source))openTabs.push(item.source);
     cancelCoreBufferSync(item.source);
     const revision=Math.max(coreRevisions.get(item.source)||0,
       Number.isInteger(item.coreRevision)?item.coreRevision:0)+1;
     coreRevisions.set(item.source,revision);
     bridge.postMessage({source:item.source,text:item.after,revision});
   }
   renderTabs();
   if(current&&byName.has(current)){
     updateEditingView();
     recolorSource();
     updateCursor();
   }
   diagnosticsStatus.textContent='Rename pending: review and save '+changes.length+' affected file(s)';
 };
 semanticRenameButton.addEventListener('click',requestSemanticRename);
 editorInput.addEventListener('keydown',event=>{
   if(event.key==='F2'&&!event.altKey&&!event.metaKey&&!event.ctrlKey){
     event.preventDefault();
     if(event.shiftKey)renameLocalIdentifier();else requestSemanticRename();
   }
 });
 function historyState(){
   const file=current?byName.get(current):null;
   return {text:editorInput.value,start:editorInput.selectionStart,end:editorInput.selectionEnd,
     extraSelections:(file?.extraSelections||[]).map(item=>({...item}))};
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
   file.extraSelections=state.extraSelections||[];
   editorInput.setSelectionRange(state.start,state.end);
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
   applyingHistory=false;
 }
 function duplicateCurrentLine(){
   const value=editorInput.value,start=editorInput.selectionStart;
   const begin=value.lastIndexOf('\\n',Math.max(0,start-1))+1;
   let end=value.indexOf('\\n',start);
   if(end<0)end=value.length;
   const source=value.slice(begin,end);
   pushUndo(byName.get(current));
   editorInput.setRangeText('\\n'+source,end,end,'end');
   editorInput.setSelectionRange(end+1+(start-begin),end+1+(start-begin));
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
 }
 function moveCurrentLine(direction){
   const value=editorInput.value,start=editorInput.selectionStart;
   const begin=value.lastIndexOf('\\n',Math.max(0,start-1))+1;
   let end=value.indexOf('\\n',start);
   if(end<0)end=value.length;
   const line=value.slice(begin,end),offset=start-begin;
   if(direction<0){
     if(begin===0)return;
     const previousStart=value.lastIndexOf('\\n',Math.max(0,begin-2))+1;
     const previous=value.slice(previousStart,begin-1);
     pushUndo(byName.get(current));
     editorInput.setRangeText(line+'\\n'+previous,previousStart,end,'end');
     editorInput.setSelectionRange(previousStart+offset,previousStart+offset);
   }else{
     if(end>=value.length)return;
     let nextEnd=value.indexOf('\\n',end+1);
     if(nextEnd<0)nextEnd=value.length;
     const next=value.slice(end+1,nextEnd);
     pushUndo(byName.get(current));
     editorInput.setRangeText(next+'\\n'+line,begin,nextEnd,'end');
     const position=begin+next.length+1+offset;
     editorInput.setSelectionRange(position,position);
   }
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
 }
 function addVerticalCaret(direction){
   const file=current?byName.get(current):null;
   if(!file)return;
   const value=editorInput.value;
   const start=editorInput.selectionStart;
   const lineStart=value.lastIndexOf('\\n',Math.max(0,start-1))+1;
   const lineEndIndex=value.indexOf('\\n',start);
   const lineEnd=lineEndIndex<0?value.length:lineEndIndex;
   const column=start-lineStart;
   let targetStart,targetEnd;
   if(direction<0){
     if(lineStart===0)return;
     targetEnd=lineStart-1;
     targetStart=value.lastIndexOf('\\n',Math.max(0,targetEnd-1))+1;
   }else{
     if(lineEnd===value.length)return;
     targetStart=lineEnd+1;
     const nextEnd=value.indexOf('\\n',targetStart);
     targetEnd=nextEnd<0?value.length:nextEnd;
   }
   const target=Math.min(targetStart+column,targetEnd);
   const extras=file.extraSelections||(file.extraSelections=[]);
   if(extras.some(range=>range.start===target&&range.end===target))return;
   extras.push({start:editorInput.selectionStart,end:editorInput.selectionEnd});
   editorInput.setSelectionRange(target,target);
   recolorSource();updateCursor();
 }
 function addNextOccurrence(){
   const file=current?byName.get(current):null;
   if(!file)return;
   let start=editorInput.selectionStart,end=editorInput.selectionEnd;
   const value=editorInput.value;
   if(start===end){
     while(start>0&&/[A-Za-z0-9_]/.test(value[start-1]))start--;
     while(end<value.length&&/[A-Za-z0-9_]/.test(value[end]))end++;
     if(start===end)return;
     editorInput.setSelectionRange(start,end);
     return;
   }
   const word=value.slice(start,end);
   if(!word||word.includes('\\n'))return;
   const extras=file.extraSelections||(file.extraSelections=[]);
   const used=[...extras,{start,end}];
   let pos=value.indexOf(word,end),wrapped=false;
   while(pos!==-1){
     if(!used.some(item=>pos<item.end&&pos+word.length>item.start))break;
     pos=value.indexOf(word,pos+word.length);
   }
   if(pos<0){
     wrapped=true;
     pos=value.indexOf(word,0);
     while(pos!==-1&&used.some(item=>pos<item.end&&pos+word.length>item.start))
       pos=value.indexOf(word,pos+word.length);
   }
   if(pos<0)return;
   extras.push({start,end});
   editorInput.setSelectionRange(pos,pos+word.length);
   cursorStatus.textContent='Multiple selections: '+(extras.length+1);
 }
 function editMultipleSelections(inputType,data){
   const file=current?byName.get(current):null;
   const extras=file?.extraSelections||[];
   if(!extras.length)return false;
   const value=editorInput.value;
   const primary={start:editorInput.selectionStart,end:editorInput.selectionEnd};
   const ranges=[...extras,primary].sort((a,b)=>a.start-b.start);
   if(ranges.some((item,i)=>i>0&&item.start<ranges[i-1].end))return false;
   const edits=ranges.map(item=>{
     const from=inputType==='deleteContentBackward'&&item.start===item.end
       ?Math.max(0,item.start-1):item.start;
     const closing={'(' : ')','[' : ']','{' : '}', '"':'"', "'":"'"};
     const replacement=inputType==='deleteContentBackward'?'':
       inputType==='insertPair'?data+value.slice(item.start,item.end)+closing[data]:data;
     return {from,to:item.end,replacement,primary:item===primary,
       caretAdvance:inputType==='insertPair'?1+(item.end-item.start):replacement.length};
   });
   pushUndo(file);
   let text=value;
   for(const edit of [...edits].reverse())
     text=text.slice(0,edit.from)+edit.replacement+text.slice(edit.to);
   let delta=0,primaryAt=0;
   const next=[];
   for(let i=0;i<edits.length;i++){
     const edit=edits[i];
     const position=edit.from+delta+edit.caretAdvance;
     if(i===ranges.indexOf(primary))primaryAt=position;
     else next.push({start:position,end:position});
     delta+=edit.replacement.length-(edit.to-edit.from);
   }
   file.extraSelections=next;
   editorInput.value=text;
   editorInput.setSelectionRange(primaryAt,primaryAt);
   editorInput.dispatchEvent(new Event('input',{bubbles:true}));
   return true;
 }
 editorInput.addEventListener('beforeinput',e=>{
   if(e.isComposing||applyingHistory)return;
   if((e.inputType==='insertText'&&typeof e.data==='string')||e.inputType==='deleteContentBackward'){
     if(editMultipleSelections(e.inputType,e.data||'')){e.preventDefault();return;}
   }
   if(e.inputType==='historyUndo'||e.inputType==='historyRedo'){
     e.preventDefault();
     restoreHistory(e.inputType==='historyUndo'?'undo':'redo');
     return;
   }
   if(e.inputType?.startsWith('insert')||e.inputType?.startsWith('delete')){
     const file=byName.get(current);
     if(file?.extraSelections?.length)file.extraSelections=[];
     pushUndo(file);
   }
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
   if(e.metaKey&&e.altKey&&['ArrowUp','ArrowDown'].includes(e.key)){
     e.preventDefault();addVerticalCaret(e.key==='ArrowUp'?-1:1);return;
   }
   if(e.metaKey&&e.shiftKey&&!e.altKey&&e.key.toLowerCase()==='d'){
     e.preventDefault();duplicateCurrentLine();return;
   }
   if(e.altKey&&!e.metaKey&&!e.ctrlKey&&['ArrowUp','ArrowDown'].includes(e.key)){
     e.preventDefault();moveCurrentLine(e.key==='ArrowUp'?-1:1);return;
   }
   if((e.metaKey||e.ctrlKey)&&e.key==='/'){
     e.preventDefault();
     const start=editorInput.selectionStart,end=editorInput.selectionEnd;
     const value=editorInput.value;
     const begin=value.lastIndexOf('\\n',Math.max(0,start-1))+1;
     let finish=value.indexOf('\\n',end);
     if(finish<0)finish=value.length;
     const lines=value.slice(begin,finish).split('\\n');
     const uncomment=lines.every(line=>!line.trim()||line.trimStart().startsWith('//'));
     const changed=lines.map(line=>{
       if(!line.trim())return line;
       return uncomment?line.replace(/^(\\s*)\\/\\/ ?/,'$1'):line.replace(/^(\\s*)/,'$1// ');
     }).join('\\n');
     replaceSelection(changed,begin,finish);
     editorInput.setSelectionRange(begin,begin+changed.length);
     return;
   }
   if(e.metaKey&&!e.altKey&&e.key.toLowerCase()==='d'){
     e.preventDefault();addNextOccurrence();return;
   }
   if(e.key==='Escape'&&byName.get(current)?.extraSelections?.length){
     e.preventDefault();byName.get(current).extraSelections=[];updateCursor();return;
   }
   if((e.metaKey||e.ctrlKey)&&!e.altKey&&e.key.toLowerCase()==='z'){
     e.preventDefault();
     restoreHistory(e.shiftKey?'redo':'undo');
     return;
   }
   if(!e.metaKey&&!e.ctrlKey&&!e.altKey&&!e.isComposing){
     const pairs={'(' : ')','[' : ']','{' : '}', '"':'"', "'":"'"};
     const start=editorInput.selectionStart,end=editorInput.selectionEnd;
     if(Object.prototype.hasOwnProperty.call(pairs,e.key)){
       e.preventDefault();
       if(editMultipleSelections('insertPair',e.key))return;
       const selected=editorInput.value.slice(start,end);
       replaceSelection(e.key+selected+pairs[e.key],start,end);
       editorInput.setSelectionRange(start+1,start+1+selected.length);
       updateCursor();
       return;
     }
     if([')',']','}', '"', "'"].includes(e.key)&&start===end&&editorInput.value[start]===e.key){
       e.preventDefault();
       editorInput.setSelectionRange(start+1,start+1);
       updateCursor();
       return;
     }
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
     const tail=editorInput.value.slice(end);
     const next=tail[0]||'';
     const opens=prefix.trimEnd().endsWith('{');
     const pnxBlock=/^(?:function|if|elif|else|for|while|class|interface|match|case|try|catch|finally)\\b/.test(prefix.trim());
     if(opens&&next==='}'){
       replaceSelection('\\n'+indent+'    '+'\\n'+indent,start,end);
       editorInput.setSelectionRange(start+1+indent.length+4,start+1+indent.length+4);
     }else{
       const adjusted=/^[}\\]\\)]/.test(next)&&indent.length>=4?indent.slice(0,-4):indent;
       replaceSelection('\\n'+adjusted+((opens||pnxBlock)?'    ':''),start,end);
     }
   }
 });
 const coreSyncTimers=new Map();
 const coreRevisions=new Map();
 const coreConfirmedRevisions=new Map();
 window.pynixCoreBufferResult=reply=>{
   const source=reply?.source;
   const revision=reply?.revision;
   if(typeof source!=='string'||!Number.isInteger(revision))return;
   if(!byName.has(source)||!openTabs.includes(source))return;
   if(revision!==(coreRevisions.get(source)||0))return;
   const status=document.querySelector('.pynix-core-bridge-indicator');
   if(!status)return;
   if(reply.ok){
     coreConfirmedRevisions.set(source,revision);
     const file=byName.get(source);
     if(file){file.coreRevision=revision;file.coreDirty=reply.dirty===true;file.coreSyncError=null;}
     status.textContent='IDE Core: synced (revision '+revision+')';
   }else{
     const file=byName.get(source);
     if(file)file.coreSyncError=String(reply.error||'Unknown error');
     status.textContent='IDE Core: sync error — '+String(reply.error||'Unknown error');
   }
 };
 let coreRecovering=false;
 let coreRecoverySnapshot=null;
 function sendCoreRevision(source,content,revision){
   const bridge=window.webkit?.messageHandlers?.pynixCoreBuffer;
   if(bridge)bridge.postMessage({source,text:content,revision});
 }
 function recoverCoreBuffers(){
   const bridge=window.webkit?.messageHandlers?.pynixCoreRecover;
   if(!bridge||coreRecovering)return;
   if(pendingNativeSaves.size||pendingCoreClose.size){
     window.alert('Wait for pending Save or Close before restoring IDE Core');
     return;
   }
   persistBuffer();
   const buffers=[];
   for(const source of openTabs){
     const file=byName.get(source);
     if(!source.endsWith('.pnx')||!file||file.unloaded)continue;
     cancelCoreBufferSync(source);
     const revision=(coreRevisions.get(source)||0)+1;
     coreRevisions.set(source,revision);
     buffers.push({source,content:file.text,revision});
   }
   coreRecovering=true;
   coreRecoverySnapshot=buffers;
   const status=document.querySelector('.pynix-core-bridge-indicator');
   if(status)status.textContent='IDE Core: restoring '+buffers.length+' buffers...';
   bridge.postMessage({buffers});
 }
 window.pynixCoreRecoveryResult=reply=>{
   const replay=coreRecoverySnapshot||[];
   coreRecoverySnapshot=null;
   coreRecovering=false;
   const status=document.querySelector('.pynix-core-bridge-indicator');
   if(reply?.ok){
     // Mark only exactly replayed versions as confirmed. An edit during
     // recovery must always be sent again, even for an inactive tab.
     for(const item of replay){
       if(!openTabs.includes(item.source))continue;
       const file=byName.get(item.source);
       if(!file||file.unloaded)continue;
       if((coreRevisions.get(item.source)||0)===item.revision&&file.text===item.content){
         file.coreRevision=item.revision;
         file.coreDirty=file.dirty;
         file.coreSyncError=null;
         coreConfirmedRevisions.set(item.source,item.revision);
       }else{
         cancelCoreBufferSync(item.source);
         const revision=(coreRevisions.get(item.source)||0)+1;
         coreRevisions.set(item.source,revision);
         sendCoreRevision(item.source,file.text,revision);
       }
     }
     if(status)status.textContent='IDE Core: restored '+reply.restored+' buffers';
   }else{
     const error=String(reply?.error||'Unknown error');
     for(const item of replay){
       const file=byName.get(item.source);
       if(file&&!file.unloaded)file.coreSyncError=error;
     }
     if(status)status.textContent='IDE Core: recovery failed — '+error;
   }
 };
 // The native host injects this indicator after the workspace script.
 // Delegate from document so recovery works independently of insertion order.
 document.addEventListener('click',event=>{
   if(event.target?.closest?.('.pynix-core-bridge-indicator'))recoverCoreBuffers();
 });
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
   if(coreRecovering||pendingCoreClose.has(source))return null;
   if(pendingNativeSaves.has(source))return null;
   // A save is a synchronization barrier: cancel obsolete deferred editor sends
   // and allocate a newer revision for the exact bytes being saved.
   cancelCoreBufferSync(source);
   let revision=null;
   if(source.endsWith('.pnx')){
     revision=(coreRevisions.get(source)||0)+1;
     coreRevisions.set(source,revision);
   }
   pendingNativeSaves.set(source,{revision,text:content});
   return {source,text:content,revision};
 }
 function saveSource(){
   persistBuffer();
   const file=current?byName.get(current):null;
   if(!file||file.unloaded||!file.dirty)return;
   const bridge=window.webkit?.messageHandlers?.pynixFileSave;
   if(!bridge){window.alert('Native file saving is unavailable');return;}
   const request=prepareNativeSave(current,file.text);
   if(request)bridge.postMessage(request);
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
 const pendingNativeSaves=new Map();
 window.pynixSaveResult=payload=>{
   const source=payload?.source;
   const pending=pendingNativeSaves.get(source);
   if(!pending)return;
   if(payload.revision!==pending.revision)return;
   pendingNativeSaves.delete(source);
   const file=byName.get(source);
   if(!file||!openTabs.includes(source))return;
   if(payload.error){
     pendingCloseAfterSave=null;
     // Never discard a dirty buffer or silently close the tab on save failure.
     file.coreSyncError=String(payload.error);
     const indicator=document.querySelector('.pynix-core-bridge-indicator');
     if(indicator)indicator.textContent='IDE Core: save failed — '+String(payload.error);
     window.alert('Save failed: '+payload.error);
     return;
   }
   if(payload.saved){
     file.savedText=typeof payload.savedText==='string'?payload.savedText:pending.text;
     if(Number.isInteger(pending.revision)&&file.text===pending.text
         &&(coreRevisions.get(source)||0)===pending.revision){
       file.coreRevision=pending.revision;
       file.coreDirty=false;
       coreConfirmedRevisions.set(source,pending.revision);
     }
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
     // Explorer has one highlighted row: explicit selection wins over active tab.
     if(!entry.folder&&entry.path===(selectedPath??current))line.classList.add('workspace-selected');
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
 function foldableLines(text){
   const lines=text.split('\\n');
   const positions=new Map();
   for(let i=0;i<lines.length-1;i++){
     if(!lines[i].trim()||lines[i].trimStart().startsWith('//'))continue;
     const base=lines[i].match(/^[ \\t]*/)[0].replaceAll('\\t','    ').length;
     let end=i+1;
     while(end<lines.length){
       if(!lines[end].trim()){end++;continue;}
       const depth=lines[end].match(/^[ \\t]*/)[0].replaceAll('\\t','    ').length;
       if(depth<=base)break;
       end++;
     }
     if(end>i+1)positions.set(i,end-1);
   }
   return positions;
 }
 function renderCode(file) {
   code.replaceChildren();
   const foldable=foldableLines(file.text);
   const folded=file.foldedLines||(file.foldedLines=new Set());
   let hiddenThrough=-1;
   file.text.split('\\n').forEach((line, i) => {
     if(i<=hiddenThrough)return;
     if(folded.has(i)&&foldable.has(i))hiddenThrough=foldable.get(i);
     const row = document.createElement('div');
     row.className='source-line';
     row.dataset.line=String(i+1);
     const gutter = document.createElement('span');
     gutter.className = 'ln';
     gutter.textContent = String(i + 1);
     if(foldable.has(i)){
       gutter.classList.add('pynix-fold-control');
       gutter.title=folded.has(i)?'Expand block':'Collapse block';
       gutter.textContent=(folded.has(i)?'▸ ':'▾ ')+(i+1);
       gutter.addEventListener('click',()=>{
         if(folded.has(i))folded.delete(i);else folded.add(i);
         renderCode(file);
       });
     }
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
 const pendingCoreClose=new Map();
 function closeTabNow(name,discard=false){
   if(coreRecovering){window.alert('Wait for IDE Core recovery before closing a tab');return;}
   if(!openTabs.includes(name)||pendingCoreClose.has(name))return;
   cancelCoreBufferSync(name);
   const bridge=window.webkit?.messageHandlers?.pynixCoreClose;
   if(name.endsWith('.pnx')&&bridge){
     const file=byName.get(name);
     pendingCoreClose.set(name,{discard,revision:coreRevisions.get(name)||0,text:file?.text});
     bridge.postMessage({source:name,discard});
     return;
   }
   finishTabClose(name);
 }
 window.pynixCoreCloseResult=reply=>{
   const source=reply?.source;
   const pending=pendingCoreClose.get(source);
   if(!pending)return;
   pendingCoreClose.delete(source);
   const file=byName.get(source);
   // A user may have edited the document while Core was closing it.
   if((coreRevisions.get(source)||0)!==pending.revision||file?.text!==pending.text||file?.dirty&&!pending.discard){
     if(!reply?.closed)window.alert('IDE Core refused to close '+source+': '+String(reply?.error||'Document changed'));
     else if(file)file.coreSyncError='Document changed while Core was closing; recover Core before continuing';
     return;
   }
   if(reply?.closed){finishTabClose(source);return;}
   if(file)file.coreSyncError=String(reply?.error||'IDE Core refused to close document');
   window.alert('Close failed: '+String(reply?.error||'Unknown Core error'));
 };
 function finishTabClose(name){
   if(!openTabs.includes(name))return;
   const index=openTabs.indexOf(name);
   if(index<0)return;
   openTabs.splice(index,1);
   const file=byName.get(name);
   if(file){file.unloaded=true;file.text='';file.tokens=null;file.savedText=undefined;file.dirty=false;file.coreSyncError=null;}
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
     closeTabNow(name,true);
   });
   button('Save',()=>{
     if(current!==name){dismiss();show(name);}
     const selected=byName.get(name);
     if(!selected?.dirty){closeTabNow(name);return;}
     const bridge=window.webkit?.messageHandlers?.pynixFileSave;
     if(!bridge){window.alert('Native file saving is unavailable');return;}
     pendingCloseAfterSave=name;
     dismiss();
     const request=prepareNativeSave(name,selected.text);
     if(request)bridge.postMessage(request);
     else pendingCloseAfterSave=null;
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
   if(!payload || !byName.has(payload.source)||!openTabs.includes(payload.source))return;
   const file=byName.get(payload.source);
   if(!file.unloaded||file.dirty)return;
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
   file.savedText=typeof payload.savedText==='string'?payload.savedText:payload.text;
   file.dirty=payload.dirty===true;
   if(Number.isInteger(payload.revision)&&payload.revision>=0){
     coreRevisions.set(payload.source,Math.max(coreRevisions.get(payload.source)||0,payload.revision));
     coreConfirmedRevisions.set(payload.source,payload.revision);
     file.coreRevision=payload.revision;
     file.coreDirty=file.dirty;
   }
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
 const newSourceButton=document.createElement('button');
 newSourceButton.type='button';
 newSourceButton.className='nav-action pynix-new-source';
 newSourceButton.textContent='New .pnx';
 newSourceButton.title='Create a new PYNIX file inside the current project';
 document.querySelector('.workspace-toolbar')?.appendChild(newSourceButton);
 newSourceButton.addEventListener('click',()=>{
   const selected=selectedPath||current||'';
   const base=selected.includes('/')?selected.slice(0,selected.lastIndexOf('/')+1):'';
   const proposed=window.prompt('New PYNIX file (project-relative path):',base+'new_file.pnx');
   if(proposed===null)return;
   if(!/^[A-Za-z0-9_./-]+\\.pnx$/.test(proposed)){
     window.alert('Use a project-relative .pnx path without spaces');return;
   }
   const bridge=window.webkit?.messageHandlers?.pynixProjectCreate;
   if(!bridge){window.alert('File creation requires native macOS workspace');return;}
   bridge.postMessage({source:proposed});
 });
 window.pynixProjectCreateResult=result=>{
   if(!result?.ok){window.alert('Create file failed: '+String(result?.error||'unknown error'));return;}
   const name=result.source;
   if(byName.has(name))return;
   const file={name,text:result.text||'',savedText:result.text||'',tokens:null,icon:'pnx',dirty:false};
   files.push(file);
   files.sort((a,b)=>a.name.localeCompare(b.name));
   byName.set(name,file);
   window.pynixIndexedSources=files.map(entry=>entry.name);
   const parts=name.split('/');
   for(let i=1;i<parts.length;i++){
     const folder=parts.slice(0,i).join('/');
     if(!folders.includes(folder))folders.push(folder);
     expanded.add(folder);
   }
   show(name);
 };
 const renameFileButton=document.createElement('button');
 renameFileButton.type='button';renameFileButton.className='nav-action';
 renameFileButton.textContent='Rename File';
 const deleteFileButton=document.createElement('button');
 deleteFileButton.type='button';deleteFileButton.className='nav-action';
 deleteFileButton.textContent='Delete File';
 document.querySelector('.workspace-toolbar')?.append(renameFileButton,deleteFileButton);
 function requestProjectFileAction(action){
   persistBuffer();
   const source=selectedPath||current;
   if(!source||!byName.has(source)||!source.endsWith('.pnx'))return;
   if(openTabs.includes(source)){
     window.alert('Close the file tab before renaming or deleting it. Save any changes first.');
     return;
   }
   const file=byName.get(source);
   if(file?.dirty){
     window.alert('Save changes before modifying the project file.');return;
   }
   const bridge=window.webkit?.messageHandlers?.pynixProjectFileAction;
   if(!bridge){window.alert('Project file actions require native macOS workspace');return;}
   if(action==='rename'){
     const destination=window.prompt('Rename project file:',source);
     if(destination===null||destination===source)return;
     if(!/^[A-Za-z0-9_./-]+\\.pnx$/.test(destination)){
       window.alert('Use a safe project-relative .pnx filename');return;
     }
     bridge.postMessage({action,source,destination});
   } else {
     if(!window.confirm('Permanently delete '+source+'? This cannot be undone.'))return;
     bridge.postMessage({action,source});
   }
 }
 renameFileButton.addEventListener('click',()=>requestProjectFileAction('rename'));
 deleteFileButton.addEventListener('click',()=>requestProjectFileAction('delete'));
 window.pynixProjectFileActionResult=result=>{
   if(!result?.ok){window.alert('Project file operation failed: '+String(result?.error||'unknown error'));return;}
   const source=result.source;
   const file=byName.get(source);
   if(!file)return;
   byName.delete(source);
   const index=files.indexOf(file);
   if(index>=0)files.splice(index,1);
   if(result.action==='rename'){
     file.name=result.destination;
     byName.set(file.name,file);
     files.push(file);
     files.sort((a,b)=>a.name.localeCompare(b.name));
   }
   window.pynixIndexedSources=files.map(entry=>entry.name);
   selectedPath=result.action==='rename'?result.destination:null;
   renderTree();
 };
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

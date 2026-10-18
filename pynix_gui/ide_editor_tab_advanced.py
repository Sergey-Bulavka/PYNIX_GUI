"""Native V4 tab menu's bookmarks, preferences and code minimap.

Inserted inside the editor workspace scope; no parallel editor state.
"""

TAB_ADVANCED_JS = r"""
  // Safe, project-scoped session preferences. The in-memory copy still works
  // if WebKit's current document has no localStorage entitlement.
  const optionsKey='pynix.ide.tabs.v1:'+PROJECT_PATH;
  let savedOptions={};
  try{savedOptions=JSON.parse(localStorage.getItem(optionsKey)||'{}')||{};}catch(_){}
  const pref={
   compact:savedOptions.compact===true,
   icons:savedOptions.icons!==false,
   closeAlways:savedOptions.closeAlways===true,
   minimap:savedOptions.minimap===true
  };
  let bookmarked=Array.isArray(savedOptions.bookmarked)?
    savedOptions.bookmarked.filter(entry=>
      entry&&typeof entry.name==='string'&&Array.isArray(entry.files))
      .slice(0,20).map(entry=>({
       name:entry.name.slice(0,60),
       files:entry.files.filter(x=>typeof x==='string').slice(0,100)
      })):[];
  const saveOptions=()=>{
   try{localStorage.setItem(optionsKey,JSON.stringify({
    ...pref,bookmarked
   }));}catch(_){}
  };
  const applyOptions=()=>{
   tabs.dataset.pynixCompact=String(pref.compact);
   tabs.dataset.pynixIcons=String(pref.icons);
   tabs.dataset.pynixClose=String(pref.closeAlways);
   schedule();
  };
  const bookmarkOpenTabs=()=>{
   if(!openTabs.length)return;
   const suggestion='Open tabs '+(bookmarked.length+1);
   const answer=window.prompt('Bookmark these '+openTabs.length+' open tabs as:',suggestion);
   if(answer===null)return;
   const name=answer.trim().slice(0,60);
   if(!name)return;
   const at=bookmarked.findIndex(x=>x.name===name);
   if(at>=0)bookmarked.splice(at,1);
   bookmarked.unshift({name,files:[...openTabs]});
   if(bookmarked.length>20)bookmarked.pop();
   saveOptions();
  };
  const restoreBookmarks=entry=>{
   for(const name of entry.files){
    if(byName.has(name))show(name);
   }
  };
  const paintBookmarks=()=>{
   if(!bookmarked.length){
    row('No bookmarked tab groups',null,{disabled:true});return;
   }
   for(const entry of bookmarked){
    const item=row(entry.name+' ('+entry.files.length+')',
      ()=>restoreBookmarks(entry));
    const erase=document.createElement('button');
    erase.type='button';erase.className='pynix-tabs-menu-close';
    erase.setAttribute('aria-label','Delete bookmarked group '+entry.name);
    erase.textContent='×';
    erase.addEventListener('click',event=>{
     event.stopPropagation();
     bookmarked=bookmarked.filter(x=>x!==entry);
     saveOptions();paint();position();
    });
    item.appendChild(erase);
   }
  };
  const preferenceRow=(name,key)=>{
   row((pref[key]?'✓  ':'    ')+name,()=>{
    pref[key]=!pref[key];saveOptions();applyOptions();
   });
  };
  const paintPreferences=()=>{
   preferenceRow('Compact Tabs','compact');
   preferenceRow('Show File Icons','icons');
   preferenceRow('Always Show Close Buttons','closeAlways');
  };
  // A real, read-only and clickable minimap of the current source buffer.
  // Draw compressed line glyphs (not a second editor) and a viewport marker.
  const editorHost=code.parentElement;
  const mini=document.createElement('div');
  mini.className='pynix-editor-minimap';
  mini.setAttribute('role','region');
  mini.setAttribute('aria-label','Code minimap');
  const miniCanvas=document.createElement('canvas');
  miniCanvas.setAttribute('aria-label','Click to scroll code');
  miniCanvas.setAttribute('role','button');
  miniCanvas.tabIndex=0;
  mini.appendChild(miniCanvas);
  mini.hidden=!pref.minimap;
  editorHost.appendChild(mini);
  let minimapFrame=0;
  const scrollHost=()=>editing&&!editorInput.hidden?editorInput:
    code.querySelector('.pynix-editor-scroll');
  const drawMinimap=()=>{
   minimapFrame=0;
   mini.hidden=!pref.minimap;
   if(!pref.minimap||!current||!byName.has(current))return;
   const file=byName.get(current);
   if(!file||file.unloaded)return;
   const width=Math.max(1,mini.clientWidth);
   const height=Math.max(1,mini.clientHeight);
   const ratio=Math.min(2,window.devicePixelRatio||1);
   miniCanvas.width=Math.round(width*ratio);
   miniCanvas.height=Math.round(height*ratio);
   const ctx=miniCanvas.getContext('2d');if(!ctx)return;
   ctx.setTransform(ratio,0,0,ratio,0,0);
   ctx.clearRect(0,0,width,height);
   const lines=(editing&&!editorInput.hidden?editorInput.value:file.text).split('\n');
   const limit=Math.min(lines.length,5000),step=Math.max(1,Math.ceil(lines.length/limit));
   const rowHeight=Math.max(.8,Math.min(2.8,height/Math.max(1,Math.ceil(lines.length/step))));
   const n=Math.max(1,Math.ceil(lines.length/step));
   const scale=height/n;
   for(let i=0;i<n;i++){
    const line=lines[i*step]||'';
    if(!line.trim())continue;
    const indent=(line.match(/^\s*/)?.[0].length||0);
    const x=Math.min(width-8,3+indent*.65);
    const length=Math.min(width-6-x,Math.max(3,line.trim().length*.72));
    if(length<=0)continue;
    ctx.fillStyle=/^\s*(#|\/\/)/.test(line)?'#657563':
      /^\s*(class|def|function|import|from|return)\b/.test(line)?'#ae835f':'#868a92';
    ctx.fillRect(x,i*scale,Math.max(1,length),rowHeight);
   }
   const target=scrollHost();
   if(target){
    const total=Math.max(1,target.scrollHeight);
    const y=height*Math.min(1,target.scrollTop/total);
    const h=Math.min(height,Math.max(12,height*target.clientHeight/total));
    ctx.fillStyle='rgba(116,146,182,.23)';
    ctx.fillRect(0,y,width,h);
    ctx.strokeStyle='rgba(140,167,199,.60)';
    ctx.strokeRect(.5,y+.5,width-1,Math.max(1,h-1));
   }
  };
  const scheduleMinimap=()=>{
   if(!minimapFrame)minimapFrame=requestAnimationFrame(drawMinimap);
  };
  miniCanvas.addEventListener('click',event=>{
   const target=scrollHost();if(!target)return;
   const rect=miniCanvas.getBoundingClientRect();
   const position=Math.max(0,Math.min(1,(event.clientY-rect.top)/Math.max(1,rect.height)));
   const max=Math.max(0,target.scrollHeight-target.clientHeight);
   target.scrollTop=Math.round(position*max);
   target.dispatchEvent(new Event('scroll',{bubbles:true}));
  });
  miniCanvas.addEventListener('keydown',event=>{
   if(event.key!=='Enter'&&event.key!==' ')return;
   event.preventDefault();miniCanvas.click();
  });
  editorInput.addEventListener('input',scheduleMinimap);
  editorInput.addEventListener('scroll',scheduleMinimap,{passive:true});
  code.addEventListener('scroll',scheduleMinimap,true);
  document.addEventListener('pynix:file-opened',scheduleMinimap);
  new ResizeObserver(scheduleMinimap).observe(editorHost);
  const setMinimap=value=>{
   pref.minimap=Boolean(value);
   saveOptions();scheduleMinimap();
  };
  const toggleMinimap=()=>setMinimap(!pref.minimap);
  // Defer until the parent tab controller has installed its width scheduler.
  requestAnimationFrame(()=>{applyOptions();scheduleMinimap();});
"""
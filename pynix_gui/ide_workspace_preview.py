"""Read-only bridge from a real local project into the V4 visual workspace.

Uses a bounded snapshot, not subprocesses or arbitrary filesystem access.
"""
from __future__ import annotations

import html
import json

from .ide_workspace_session import WorkspaceSession


def workspace_bootstrap(session: WorkspaceSession, *, max_files: int = 120,
                        max_bytes: int = 100_000) -> str:
    records = []
    for name in session.list_files(limit=max_files):
        if not name.lower().endswith((".pnx", ".py", ".md", ".json", ".toml", ".txt")):
            continue
        try:
            path = session.resolve_file(name)
            if path.stat().st_size > max_bytes:
                continue
            doc = session.open(name)
        except (OSError, ValueError):
            continue
        records.append({"name": name, "text": doc.text})
    session.documents.clear()
    session.active = None
    payload = json.dumps(records, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    # This script is appended after the gallery's own scripts, so the initial
    # design preview retains its independent, self-contained state.
    return """<script>
(() => {
 const files = PAYLOAD;
 const PROJECT_NAME = PROJECT_NAME_PAYLOAD;
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
 const expanded = new Set(['']);
 const icon = {
   folder: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M3 5h6l2 3h10v11H3z"/></svg>',
   file: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M5 2h10l5 5v15H5zM15 2v5h5"/></svg>',
   code: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M5 2h10l5 5v15H5zM15 2v5h5M10 12l-2 3 2 3m5-6 2 3-2 3"/></svg>'
 };
 function buildTree() {
   const root = {children: new Map(), path:'', folder:true};
   for(const file of files) {
     let node = root;
     const pieces = file.name.split('/');
     pieces.forEach((part, i) => {
       const key = pieces.slice(0,i+1).join('/');
       if(!node.children.has(part))
         node.children.set(part, {name:part,path:key,folder:i<pieces.length-1,children:new Map()});
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
   const project=document.createElement('div');
   project.className='entry project-root';
   project.textContent='⌄  '+PROJECT_NAME;
   tree.appendChild(project);
   function visit(node,depth) {
     const children=[...node.children.values()].sort((a,b)=>
        Number(b.folder)-Number(a.folder)||a.name.localeCompare(b.name));
     for(const entry of children) {
       const line=document.createElement('div');
       line.className='entry project-entry';
       line.style.paddingLeft=(11+Math.min(depth,12)*14)+'px';
       const isOpen=expanded.has(entry.path);
       if(entry.path===current)line.classList.add('workspace-selected');
       line.setAttribute('role','button');
       line.tabIndex=0;
       line.setAttribute('aria-label',(entry.folder?'Toggle ':'Open ')+entry.path);
       const chevron=document.createElement('span');
       chevron.className='project-chevron';
       chevron.textContent=entry.folder?(isOpen?'⌄':'›'):'';
       line.appendChild(chevron);
       const glyph=document.createElement('span');
       const extension=entry.name.split('.').pop().toLowerCase();
       glyph.className='project-glyph '+(entry.folder?'folder-icon':('file-'+extension));
       glyph.innerHTML=entry.folder?icon.folder:(extension==='pnx'||extension==='py'?icon.code:icon.file);
       line.appendChild(glyph);
       const label=document.createElement('span');
       label.className='project-label';
       label.textContent=entry.name;
       line.appendChild(label);
       function activate(){
         if(entry.folder){
           if(expanded.has(entry.path))expanded.delete(entry.path);
           else expanded.add(entry.path);
           renderTree();
         } else show(entry.path);
       }
       line.addEventListener('click',activate);
       line.addEventListener('keydown',e=>{
         if(e.key==='Enter'||e.key===' '){e.preventDefault();activate()}
       });
       tree.appendChild(line);
       if(entry.folder&&isOpen)visit(entry,depth+1);
     }
   }
   visit(root,0);
 }
 function renderCode(text) {
   code.replaceChildren();
   text.split('\\n').forEach((line, i) => {
     const row = document.createElement('div');
     const gutter = document.createElement('span');
     gutter.className = 'ln';
     gutter.textContent = String(i + 1);
     row.appendChild(gutter);
     const content = document.createElement('span');
     content.textContent = line;
     row.appendChild(content);
     code.appendChild(row);
   });
 }
 function show(name) {
   if (!byName.has(name)) return;
   if (!openTabs.includes(name)) openTabs.push(name);
   current = name;
   const segments=name.split('/');
   for(let i=1;i<segments.length;i++)expanded.add(segments.slice(0,i).join('/'));
   tabs.replaceChildren();
   for (const fileName of openTabs) {
     const tab = document.createElement('button');
     tab.type = 'button';
     tab.className = fileName === name ? 'active' : '';
     tab.textContent = fileName.split('/').pop();
     tab.addEventListener('click', () => show(fileName));
     tabs.appendChild(tab);
   }
   renderCode(byName.get(name).text);
   renderTree();
 }
 const sourceControl = document.querySelectorAll('.rail-item')[2];
 sourceControl?.addEventListener('click', () => {
   // Source Control remains the visual-only demonstration mode.
 });
 show(files[0].name);
})();
</script>""".replace("PAYLOAD", payload).replace("PROJECT_NAME_PAYLOAD", json.dumps(session.root.name, ensure_ascii=False))


def attach_workspace(html_source: str, session: WorkspaceSession) -> str:
    if "</body>" not in html_source:
        raise ValueError("Missing HTML body")
    return html_source.replace("</body>", workspace_bootstrap(session) + "</body>", 1)

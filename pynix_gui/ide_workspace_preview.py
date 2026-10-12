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
  "folder": "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' > <path d='M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z' /> </svg> ",
  "folder-open": "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' > <path d='m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2' /> </svg> ",
  "file": "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' > <path d='M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z' /> <path d='M14 2v5a1 1 0 0 0 1 1h5' /> </svg> ",
  "file-code": "<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' > <path d='M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z' /> <path d='M14 2v5a1 1 0 0 0 1 1h5' /> <path d='M10 12.5 8 15l2 2.5' /> <path d='m14 12.5 2 2.5-2 2.5' /> </svg> "
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
   function appendRow(entry, depth, isRoot=false) {
     const isOpen=expanded.has(entry.path);
     const line=document.createElement('div');
     line.className='entry project-entry'+(isRoot?' project-root':'');
     line.style.paddingLeft=(12+Math.min(depth,12)*16)+'px';
     if(entry.path===current)line.classList.add('workspace-selected');
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
     glyph.className='project-glyph '+(entry.folder?'folder-icon':('file-'+extension));
     glyph.innerHTML=entry.folder?(isOpen?icon['folder-open']:icon.folder):(extension==='pnx'||extension==='py'?icon['file-code']:icon.file);
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
     line.addEventListener('click',activate);
     line.addEventListener('keydown',e=>{
       if(e.key==='Enter'||e.key===' '){e.preventDefault();activate()}
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
</script>""".replace("PROJECT_NAME_PAYLOAD", json.dumps(session.root.name, ensure_ascii=False)).replace("PAYLOAD", payload)


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
    if not snapshot.available:
        return html_source
    payload = json.dumps({
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

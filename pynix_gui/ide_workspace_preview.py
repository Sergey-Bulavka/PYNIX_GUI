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
     let activatedByPointer=false;
     line.addEventListener('pointerdown',e=>{
       if(e.button!==0)return;
       activatedByPointer=true;
       e.preventDefault();
       activate();
     });
     // WKWebView can deliver click without pointerdown on the first
     // window-activation press. Do not require a second click.
     line.addEventListener('click',e=>{
       if(e.button!==0||activatedByPointer)return;
       e.preventDefault();
       activate();
     });
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
   const file=byName.get(name);
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
   document.dispatchEvent(new CustomEvent('pynix:file-opened',{detail:{source:name}}));
   renderTree();
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
   file.tokens=payload.tokens||null;
   file.unloaded=false;
   if(current===payload.source)renderCode(file);
 };
 document.addEventListener('pynix:navigate', event=>{
   const target=event.detail||{};
   if(!byName.has(target.source))return;
   show(target.source);
   const rows=[...code.querySelectorAll('.source-line')];
   const selected=rows[Math.max(0,Number(target.line||1)-1)];
   if(selected){
     selected.scrollIntoView({block:'center'});
     selected.classList.add('source-line-target');
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

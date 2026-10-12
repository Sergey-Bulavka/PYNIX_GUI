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
 function escapeText(s) {
   const el = document.createElement('span');
   el.textContent = s;
   return el.innerHTML;
 }
 function renderTree() {
   tree.innerHTML = '<div class="tree-title">PROJECT FILES <span>···</span></div>';
   for (const file of files) {
     const line = document.createElement('div');
     line.className = 'entry';
     line.tabIndex = 0;
     line.setAttribute('role', 'button');
     line.setAttribute('aria-label', 'Open ' + file.name);
     line.textContent = '◇  ' + file.name;
     if (file.name === current) line.classList.add('workspace-selected');
     line.addEventListener('click', () => show(file.name));
     line.addEventListener('keydown', e => {
       if(e.key === 'Enter'){e.preventDefault();show(file.name)}
     });
     tree.appendChild(line);
   }
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
</script>""".replace("PAYLOAD", payload)


def attach_workspace(html_source: str, session: WorkspaceSession) -> str:
    if "</body>" not in html_source:
        raise ValueError("Missing HTML body")
    return html_source.replace("</body>", workspace_bootstrap(session) + "</body>", 1)

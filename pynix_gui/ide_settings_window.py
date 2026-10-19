# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""First native PyCharm-style Settings window for PYNIX V4.

Only editor font settings are editable until the corresponding runtime
consumers exist. Settings are global; project defaults are not conflated.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


DEFAULTS = {"editor.font_size": 13.0, "editor.line_height": 1.2}
CATEGORIES = (
    ("Appearance & Behavior", ("Appearance", "System Settings")),
    ("Keymap", ()),
    ("Editor", (
        "General", "Code Editing", "Font", "Color Scheme", "Code Style",
        "Inspections", "File and Code Templates", "File Encodings",
        "Live Templates", "File Types", "Intentions", "Language Injections",
        "Minimap", "Reader Mode", "TODO",
    )),
    ("Plugins", ()), ("Version Control", ()),
    ("Build, Execution, Deployment", ()), ("Languages & Frameworks", ()),
    ("Tools", ()), ("Advanced Settings", ()),
)


def validate_editor_settings(payload: object) -> dict[str, float]:
    if not isinstance(payload, dict) or set(payload) != set(DEFAULTS):
        raise ValueError("Invalid Settings keys")
    result = {}
    for name, (lower, upper) in {
        "editor.font_size": (8.0, 36.0),
        "editor.line_height": (1.0, 2.5),
    }.items():
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Invalid numeric setting: " + name)
        value = float(value)
        if not lower <= value <= upper:
            raise ValueError("Settings value out of range: " + name)
        result[name] = value
    return result


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or (
            Path.home() / "Library" / "Application Support" /
            "PYNIX" / "ide-settings-v1.json"
        )

    def read(self) -> dict[str, float]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return validate_editor_settings(raw)
        except (OSError, UnicodeError, ValueError, TypeError):
            return dict(DEFAULTS)

    def write(self, values: object) -> dict[str, float]:
        validated = validate_editor_settings(values)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent,
                prefix=".pynix-settings-", suffix=".tmp", delete=False
            ) as stream:
                temporary = Path(stream.name)
                os.fchmod(stream.fileno(), 0o600)
                json.dump(validated, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
            return validated
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def editor_font_script(settings: dict[str, float]) -> str:
    """Safe script for current workspace editor and syntax/gutter overlays."""
    valid = validate_editor_settings(settings)
    payload = json.dumps(valid)
    return (
        "(function(){const s=" + payload + ";"
        "let style=document.getElementById('pynix-user-editor-font');"
        "if(!style){style=document.createElement('style');"
        "style.id='pynix-user-editor-font';document.head.appendChild(style);}"
        "const size=s['editor.font_size'];"
        "const line=s['editor.line_height'];"
        "style.textContent="
        "'.workspace-mode .pynix-source-input,"
        ".workspace-mode .pynix-edit-highlight,"
        ".workspace-mode .pynix-edit-gutter'"
        "+'{font-size:'+size+'px!important;line-height:'+line+'!important}';"
        "window.dispatchEvent(new Event('resize'));"
        "})();"
    )


SETTINGS_CSS = r"""
:root{color-scheme:dark;font:13px -apple-system,BlinkMacSystemFont,system-ui,sans-serif}
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden;background:#191a1c;color:#c9cbd0}
.shell{display:grid;height:100vh;grid-template-columns:235px minmax(0,1fr);grid-template-rows:minmax(0,1fr) 49px}
.nav{grid-column:1;grid-row:1;min-width:0;overflow:auto;background:#1b1c20;border-right:1px solid #33353a;padding:10px 5px}
.search{margin:0 3px 9px;width:calc(100% - 6px);height:30px;padding:0 10px;background:#24262b;color:#dedfe2;border:1px solid #494b52;border-radius:6px;outline:none}
.search:focus{border-color:#3878e5}
.treegroup{margin:2px 0}
.node{display:block;width:100%;padding:5px 9px;border:0;background:transparent;color:#c7cad2;font:inherit;text-align:left;cursor:pointer;border-radius:3px}
.node.parent{font-weight:600}.node.child{padding-left:28px}
.node:hover{background:#30333b}.node.active{background:#304c7c;color:#e9f0ff}
.node.hidden{display:none}
.main{grid-column:2;grid-row:1;display:flex;flex-direction:column;min-width:0;min-height:0}
.header{height:54px;flex:none;padding:15px 18px 8px;font-size:13px;font-weight:600}
.content{overflow:auto;flex:1;padding:4px 18px 28px}
.desc{line-height:1.5;max-width:760px;margin-top:16px}
.links{display:flex;flex-direction:column;align-items:flex-start;gap:7px;padding-left:18px}
.link{border:0;background:none;color:#75aaff;cursor:pointer;padding:0;font:inherit}
.link:hover{text-decoration:underline}
.setting{display:flex;gap:14px;align-items:center;margin:15px 0}
.setting input{font:inherit;background:#24262b;color:#d7dae0;border:1px solid #4a4e57;border-radius:5px;padding:6px 8px;width:94px}
.setting label{min-width:148px}
.note{color:#848892;font-size:12px;max-width:630px;line-height:1.5;margin:14px 0}
.preview{padding:14px 18px;white-space:pre-wrap;min-height:120px;border:1px solid #32343a;background:#1c1d20;font-family:monospace}
.footer{grid-column:1/3;grid-row:2;display:flex;justify-content:flex-end;align-items:center;gap:10px;padding:0 16px;border-top:1px solid #303138}
.footer button{font:inherit;border:1px solid #454851;background:#26282d;color:#d8dae0;border-radius:5px;padding:5px 16px;cursor:pointer}
.footer button.primary{background:#356dda;border-color:#356dda;color:white;min-width:72px}
.footer button:disabled{opacity:.4;cursor:default}
.footer .help{margin-right:auto;background:transparent;border:0;font-size:16px;padding:6px}
.warning{color:#e8b779;margin:12px 0 0}
"""


SETTINGS_JS = r"""
(() => {
 const categories=__CATEGORIES__;
 const initial=__INITIAL__;
 let draft={...initial},dirty=false,current='Editor';
 const nav=document.getElementById('nav'),body=document.getElementById('content');
 const path=document.getElementById('pagePath'),apply=document.getElementById('apply');
 const send=(data)=>window.webkit?.messageHandlers?.pynixSettings?.postMessage(data);
 const esc=value=>String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
 const groups=new Map(categories),buttons=new Map();
 let expanded=new Set(['Editor']);
 const hasChildren=name=>(groups.get(name)||[]).length>0;
 const isChild=name=>categories.find(([group,children])=>children.includes(name))?.[0]||null;
 const drawTree=()=>{
  nav.replaceChildren();
  const term=document.getElementById('filter').value.trim().toLowerCase();
  for(const [group,children] of categories){
   const matching=children.filter(x=>x.toLowerCase().includes(term));
   if(term&&!group.toLowerCase().includes(term)&&!matching.length)continue;
   const entry=(label,isSub)=>{
    const b=document.createElement('button');b.type='button';
    b.className='node '+(isSub?'child':'parent')+(label===current?' active':'');
    b.textContent=(!isSub&&children.length?(expanded.has(group)?'⌄ ':'› '):'')+label;
    b.addEventListener('click',()=>{
     if(!isSub&&children.length){if(expanded.has(group))expanded.delete(group);else expanded.add(group);}
     showPage(label);
    });
    nav.appendChild(b);
   };
   entry(group,false);
   if(expanded.has(group)||term)for(const child of children){
    if(!term||child.toLowerCase().includes(term)||group.toLowerCase().includes(term))entry(child,true);
   }
  }
 };
 const link=(label)=>{
  const button=document.createElement('button');button.className='link';button.type='button';
  button.textContent=label;button.addEventListener('click',()=>showPage(label));body.appendChild(button);
 };
 const paragraph=(text,klass='desc')=>{
  const p=document.createElement('p');p.className=klass;p.textContent=text;body.appendChild(p);
 };
 const setting=(label,key,step,min,max)=>{
  const row=document.createElement('div');row.className='setting';
  const l=document.createElement('label');l.textContent=label;
  const input=document.createElement('input');input.type='number';
  input.min=String(min);input.max=String(max);input.step=String(step);input.value=String(draft[key]);
  l.htmlFor='setting-'+key;input.id=l.htmlFor;
  input.addEventListener('input',()=>{
   draft[key]=Number(input.value);
   const valid=Object.keys(draft).every(k=>Number.isFinite(draft[k]))&&
    draft['editor.font_size']>=8&&draft['editor.font_size']<=36&&
    draft['editor.line_height']>=1&&draft['editor.line_height']<=2.5;
   dirty=true;apply.disabled=!valid;
   document.getElementById('ok').disabled=!valid;
  });
  row.append(l,input);body.appendChild(row);
 };
 const showPage=(name)=>{
  current=name;body.replaceChildren();path.textContent=(isChild(name)?isChild(name)+'  ›  ':'')+name;
  drawTree();
  if(name==='Editor'){
   paragraph('Personalize source-code appearance, highlighting, tabs, caret behavior, templates and encodings.');
   const links=document.createElement('div');links.className='links';body.appendChild(links);
   for(const label of groups.get('Editor')){
    const b=document.createElement('button');b.type='button';b.className='link';
    b.textContent=label;b.addEventListener('click',()=>showPage(label));links.appendChild(b);
   }
  }else if(name==='Font'){
   paragraph('Editor font. These options affect the source editor only, not the IDE interface or terminal.');
   setting('Size (px)', 'editor.font_size', 0.5, 8, 36);
   setting('Line height', 'editor.line_height', 0.1, 1, 2.5);
   const preview=document.createElement('pre');preview.className='preview';
   preview.textContent='def hello_world():\n    print("PYNIX IDE")\n\n# Editor font preview';
   body.appendChild(preview);
   const sync=()=>{preview.style.fontSize=String(draft['editor.font_size'])+'px';preview.style.lineHeight=String(draft['editor.line_height']);};
   body.querySelectorAll('input').forEach(x=>x.addEventListener('input',sync));sync();
  }else if(name==='File Encodings'){
   paragraph('UTF-8 without BOM is the current PYNIX default.');
   paragraph('Per-file encoding conversion requires filesystem and unsaved-buffer safeguards and is not yet available.', 'note');
  }else if(name==='Appearance'){
   paragraph('Appearance: dark native IDE theme. Global UI font, menu scaling and theme selection will be connected in the next Settings batch.');
   paragraph('Editor font is configured separately under Editor → Font.', 'note');
  }else if(name==='TODO'){
   paragraph('Default patterns: TODO and FIXME.');
   paragraph('Editable TODO filters will be available once the comment-token index is connected.', 'note');
  }else{
   paragraph('This section follows the PyCharm Settings structure.');
   paragraph('No editable controls are shown until the corresponding PYNIX runtime feature is implemented.', 'note');
  }
 };
 document.getElementById('filter').addEventListener('input',drawTree);
 document.getElementById('cancel').addEventListener('click',()=>send({action:'close'}));
 document.getElementById('apply').addEventListener('click',()=>send({action:'save',values:draft,close:false}));
 document.getElementById('ok').addEventListener('click',()=>{
  if(dirty)send({action:'save',values:draft,close:true});
  else send({action:'close'});
 });
 window.pynixSettingsSaved=result=>{
  if(result?.error){
   document.getElementById('error').textContent=result.error;return;
  }
  initial['editor.font_size']=draft['editor.font_size'];
  initial['editor.line_height']=draft['editor.line_height'];
  dirty=false;apply.disabled=true;document.getElementById('error').textContent='';
 };
 document.addEventListener('keydown',e=>{
  if(e.key==='Escape')send({action:'close'});
  if(e.key==='Enter'&&e.metaKey&&!document.getElementById('ok').disabled)
   document.getElementById('ok').click();
 });
 showPage('Editor');
})();
"""


def settings_html(values: dict[str, float], page: str = "Editor") -> str:
    validated = validate_editor_settings(values)
    available = {parent for parent, _ in CATEGORIES}
    available.update(child for _, children in CATEGORIES for child in children)
    if page not in available:
        page = "Editor"
    categories = json.dumps(CATEGORIES, ensure_ascii=False)
    initial = json.dumps(validated)
    # Replace tokens in JS source, never interpolate into HTML attributes.
    script = SETTINGS_JS.replace("__CATEGORIES__", categories).replace("__INITIAL__", initial)
    script = script.replace("showPage('Editor');", "showPage(" + json.dumps(page) + ");")
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Settings — PYNIX</title><style>' + SETTINGS_CSS +
        '</style></head><body><div class="shell">'
        '<aside class="nav"><input id="filter" class="search"'
        ' aria-label="Search settings" placeholder="Search settings…">'
        '<nav id="nav" aria-label="Settings categories"></nav></aside>'
        '<main class="main"><div class="header" id="pagePath">Editor</div>'
        '<section class="content" id="content"></section></main>'
        '<footer class="footer"><button class="help" title="Help"'
        ' disabled>?</button><span id="error" class="warning"></span>'
        '<button id="cancel">Cancel</button><button id="apply" disabled>Apply</button>'
        '<button class="primary" id="ok">OK</button></footer>'
        '</div><script>' + script + '</script></body></html>'
    )

"""V4.8 WebKit message bridge for read-only compiler language navigation.

The website cannot choose an executable or arbitrary path. The host pins the
project and interpreter and validates requests in the existing tooling adapter.
"""
from __future__ import annotations

import json
from pathlib import Path

COMMANDS = frozenset(("definition", "references", "type-at"))


def validate_request(value: object, available: set[str]) -> tuple[str, str, int, int]:
    if not isinstance(value, dict):
        raise ValueError("Invalid navigation request")
    command, source = value.get("command"), value.get("source")
    line, column = value.get("line"), value.get("column")
    if command not in COMMANDS or not isinstance(source, str) or source not in available:
        raise ValueError("Unknown navigation action or unopened source")
    if type(line) is not int or type(column) is not int or not (1 <= line <= 1_000_000 and 1 <= column <= 100_000):
        raise ValueError("Invalid source position")
    if not source.lower().endswith(".pnx"):
        raise ValueError("Language navigation requires a .pnx file")
    return command, source, line, column


def result_script(result: dict, command: str) -> str:
    """Use JSON serialization, never splice raw diagnostic text into JS."""
    payload = json.dumps({"command": command, "result": result}, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return "window.pynixNavigationResult(" + payload + ");"


def navigation_controls() -> str:
    return """<script>
(() => {
 if(!document.body.classList.contains('workspace-mode'))return;
 const code=document.querySelector('.editor .code');
 const tabs=document.querySelector('.terminal-tabs');
 const output=document.querySelector('.terminal-console');
 const toolbar=document.querySelector('.workspace-toolbar');
 if(!code||!tabs||!output||!toolbar)return;
 const handler=window.webkit?.messageHandlers?.pynixNavigation;
 let source=window.pynixActiveSource||null, line=1, column=1;
 document.addEventListener('pynix:file-opened', e=>{source=e.detail.source;line=1;column=1});
 code.addEventListener('click', e=>{
   const row=e.target.closest('.source-line');
   if(!row)return;
   line=Number(row.dataset.line);
   const label=row.querySelector('.source-text');
   const caret=document.caretRangeFromPoint?.(e.clientX,e.clientY);
   if(label && caret && label.contains(caret.startContainer)){
     const preceding=document.createRange();
     preceding.selectNodeContents(label);
     preceding.setEnd(caret.startContainer,caret.startOffset);
     column=preceding.toString().length+1;
   } else column=1;
   code.querySelectorAll('.source-line-target').forEach(el=>el.classList.remove('source-line-target'));
   row.classList.add('source-line-target');
   const status=document.querySelector('.bottom');
   if(status)status.title=source+':'+line+':'+column;
 });
 const commands=[['definition','Definition'],['references','References'],['type-at','Type']];
 for(const [command,label] of commands){
   const button=document.createElement('button');
   button.type='button';button.className='nav-action';
   button.textContent=label;
   button.title='Query compiler at selected file and code position';
   button.addEventListener('click',()=>{
     if(!source || !source.endsWith('.pnx')) {
       window.pynixNavigationResult({command,result:{error:'Open a PYNIX source file first'}});
       return;
     }
     if(!handler){window.pynixNavigationResult({command,result:{error:'Native navigation bridge unavailable'}});return;}
     handler.postMessage({command,source,line,column});
   });
   toolbar.appendChild(button);
 }
 const outputTab=[...tabs.children].find(el=>el.textContent.trim()==='OUTPUT');
 window.pynixNavigationResult=packet=>{
   const result=packet.result||{};
   output.replaceChildren();
   const add=text=>{
     const row=document.createElement('div');
     row.className='navigation-result';row.textContent=text;output.appendChild(row);
   };
   outputTab?.click();
   if(result.error){add(result.error);return;}
   add('PYNIX · '+packet.command+' · '+source+':'+line+':'+column);
   if(packet.command==='definition'){
     const d=result.definition;
     if(!d){add('No definition at this position');return;}
     add((d.qualifiedName||d.name||'')+' · '+d.source+':'+(d.start?.line||1));
     if(d.source)document.dispatchEvent(new CustomEvent('pynix:navigate',{detail:{source:d.source,line:d.start?.line||1}}));
   } else if(packet.command==='references'){
     const refs=result.references||[];
     add('References: '+refs.length);
     for(const ref of refs.slice(0,200)){
       const row=document.createElement('button');
       row.className='navigation-result nav-location';
       row.textContent=ref.source+':'+(ref.start?.line||1)+':'+(ref.start?.column||1);
       row.addEventListener('click',()=>document.dispatchEvent(
         new CustomEvent('pynix:navigate',{detail:{source:ref.source,line:ref.start?.line||1}})));
       output.appendChild(row);
     }
   } else if(packet.command==='type-at'){
     add(result.expression?JSON.stringify(result.expression):'No expression at this position');
   }
 };
})();
</script>"""


def attach_navigation_controls(document: str) -> str:
    if "</body>" not in document:
        raise ValueError("Missing HTML body")
    return document.replace("</body>", navigation_controls()+"</body>", 1)

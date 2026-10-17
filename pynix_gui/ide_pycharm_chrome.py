# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Native PYNIX IDE chrome geometry modeled after the supplied PyCharm screenshot.

Move existing DOM controls, retaining their listeners. New affordances dispatch
real PYNIX actions; unavailable ones remain explicitly disabled.
"""
from __future__ import annotations
import json
from pathlib import Path

from .ide_icon_parity import BUNDLED_ICONS
from .ide_jetbrains_icons import JetBrainsIconCatalog

CHROME_STYLE = """<style id="pynix-pycharm-chrome">
.workspace-mode .workspace-toolbar{
 position:relative!important;display:flex!important;align-items:center!important;
 gap:10px!important;background:#2b2932!important
}
.workspace-mode .workspace-toolbar>span:not(.current-branch):not(.toolbar-spacer){
 display:none!important
}
.workspace-mode .workspace-toolbar>button[title="Visual preview"]{display:none!important}
/* A single compact PyCharm project switcher, followed by a separate
   real Git-branch button. Their vector chevrons belong INSIDE each hit target. */
.workspace-mode .workspace-toolbar .pynix-toolbar-identity{
 display:flex!important;align-items:center!important;gap:12px!important;
 flex:0 0 auto!important;min-width:0!important;
 height:40px!important;white-space:nowrap!important;
 position:relative!important;z-index:6!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch{
 box-sizing:border-box!important;display:inline-flex!important;
 align-items:center!important;justify-content:flex-start!important;
 flex:0 1 auto!important;min-width:0!important;
 height:33px!important;border:1px solid transparent!important;
 background:transparent!important;border-radius:9px!important;
 color:#c6c7cf!important;padding:3px 7px!important;
 white-space:nowrap!important;cursor:pointer!important;
 font:500 13px/1.1 -apple-system,BlinkMacSystemFont,system-ui,sans-serif!important;
 transition:background-color 110ms ease!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project{
 gap:7px!important;padding-left:5px!important;padding-right:8px!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-branch{
 gap:7px!important;padding-left:7px!important;padding-right:8px!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project:hover,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch:hover{
 background:#3b3945!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project:focus-visible,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch:focus-visible{
 outline:2px solid #80b8f4!important;outline-offset:-2px!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project-badge{
 flex:0 0 23px!important;display:inline-flex!important;align-items:center!important;
 justify-content:center!important;width:23px!important;height:23px!important;
 background:#9657c9!important;border-radius:5px!important;
 color:#f8f4fc!important;font:600 12px/1 system-ui,sans-serif!important;
 letter-spacing:-.6px!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project-name,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch-name{
 display:block!important;max-width:160px!important;
 min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;
 white-space:nowrap!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project-chevron,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch-chevron{
 flex:0 0 16px!important;width:16px!important;height:16px!important;
 display:block!important;color:#b8b8c3!important;
 margin-left:0!important;margin-right:0!important;transform:none!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-branch-icon{
 display:block!important;flex:0 0 20px!important;
 width:20px!important;height:20px!important;transform:none!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project-chevron *,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch-chevron *,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch-icon *{
 shape-rendering:geometricPrecision!important
}
.workspace-mode.pynix-window-inactive .workspace-toolbar .pynix-toolbar-identity{
 opacity:.55!important
}
@media(max-width:1060px){
 .workspace-mode .workspace-toolbar .pynix-toolbar-identity{
  gap:4px!important
 }
 .workspace-mode .workspace-toolbar .pynix-toolbar-project-name,
 .workspace-mode .workspace-toolbar .pynix-toolbar-branch-name{
  max-width:85px!important
 }
}
@media(prefers-reduced-motion:reduce){
 .workspace-mode .workspace-toolbar .pynix-toolbar-project,
 .workspace-mode .workspace-toolbar .pynix-toolbar-branch{
  transition:none!important
 }
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center{
 position:absolute;left:70%;top:3px;transform:translateX(-50%);
 height:37px;display:flex;align-items:center;gap:8px;
 white-space:nowrap;z-index:5
}
.workspace-mode .workspace-toolbar .pynix-pycharm-right{
 margin-left:auto;display:flex;align-items:center;gap:7px;z-index:5
}
.workspace-mode .pynix-pycharm-icon-button{
 display:inline-flex;align-items:center;justify-content:center;
 width:31px;height:31px;min-width:31px;padding:5px;box-sizing:border-box;
 border:0;border-radius:6px;background:transparent;color:#c1c3cb;
 cursor:pointer
}
.workspace-mode .pynix-pycharm-icon-button:hover{background:#41414b}
.workspace-mode .pynix-pycharm-icon-button:focus-visible,
.workspace-mode .pynix-project-quick-button:focus-visible{
 outline:2px solid #80b8f4;outline-offset:-2px
}
.workspace-mode .pynix-pycharm-icon-button svg{width:19px;height:19px}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-mode{
 min-width:120px!important;height:28px!important;
 background:transparent!important;border:0!important;color:#d1d1d7!important;
 font-size:12px!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-action,
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary{
 min-width:29px!important;width:29px!important;height:29px!important;
 padding:5px!important;background:transparent!important;border:0!important;
 font-size:0!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-action .pynix-jetbrains-icon,
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary .pynix-jetbrains-icon{
 width:18px!important;height:18px!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-action svg,
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary svg{
 color:#57c27d!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-tools-menu>summary{
 width:30px!important;height:30px!important;display:flex!important;
 align-items:center!important;justify-content:center!important;
 padding:0!important;background:transparent!important;font-size:18px!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-stop-action:disabled{
 display:none!important
}
.workspace-mode .workspace-toolbar>.pynix-save-action{display:none!important}
.workspace-mode .tree .tree-title.pynix-project-header{
 display:flex!important;align-items:center!important;height:31px!important;
 min-height:31px!important;padding:0 7px 0 12px!important;
 box-sizing:border-box!important;gap:3px!important
}
.workspace-mode .pynix-project-header>span:first-child{
 font-weight:600!important;white-space:nowrap!important;min-width:52px!important;
 font-size:12px!important
}
.workspace-mode .pynix-project-header-actions{margin-left:auto!important;gap:1px!important}
.workspace-mode .pynix-project-header-actions>span:first-child{display:none!important}
.workspace-mode .pynix-project-quick-button,
.workspace-mode .pynix-project-header-button{
 display:inline-flex!important;align-items:center!important;justify-content:center!important;
 box-sizing:border-box!important;flex:0 0 24px!important;width:24px!important;
 height:26px!important;min-width:24px!important;padding:3px!important;
 background:transparent!important;border:0!important;border-radius:5px!important;
 color:#afb1b9!important;font:16px system-ui!important;cursor:pointer
}
.workspace-mode .pynix-project-quick-button:hover,
.workspace-mode .pynix-project-header-button:hover{background:#3c4048!important}
.workspace-mode .pynix-project-quick-button svg{width:16px;height:16px;display:block}
.workspace-mode .pynix-project-quick-button:disabled{opacity:.4;cursor:not-allowed}
.workspace-mode .pynix-project-header .pynix-project-more-menu{position:relative}
.workspace-mode .pynix-project-header .pynix-project-header-button svg,
.workspace-mode .pynix-project-more-menu>summary svg{
 display:block!important;width:16px!important;height:16px!important
}
.workspace-mode .tree .pynix-project-header-actions{
 opacity:0!important;pointer-events:none!important;
 transition:opacity 100ms ease
}
.workspace-mode .tree .pynix-project-header:hover .pynix-project-header-actions,
.workspace-mode .tree .pynix-project-header:focus-within .pynix-project-header-actions{
 opacity:1!important;pointer-events:auto!important
}
.workspace-mode .pynix-project-more-menu>summary{list-style:none}
.workspace-mode .pynix-project-more-menu>summary::-webkit-details-marker{display:none}
.workspace-mode .pynix-project-more-menu>div{
 position:absolute;top:29px;right:0;z-index:100;background:#303137;
 border:1px solid #4a4b50;border-radius:7px;padding:6px;
 box-shadow:0 9px 26px #0008;min-width:155px
}
.workspace-mode .pynix-project-more-menu>div button{
 display:block;width:100%;text-align:left;border:0;background:transparent;
 color:#ddd;padding:7px;border-radius:4px;cursor:pointer
}
.workspace-mode .pynix-project-more-menu>div button:hover{background:#444750}
.workspace-mode .bottom .pynix-status-breadcrumb{
 display:inline-flex;align-items:center;gap:6px;color:#aeb1ba;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap
}
.workspace-mode .bottom .pynix-status-breadcrumb::before{content:'›';color:#7d818a}
@media(max-width:1160px){
 .workspace-mode .workspace-toolbar .pynix-pycharm-center{
  position:static;transform:none;margin-left:auto
 }
 .workspace-mode .workspace-toolbar .pynix-pycharm-right{margin-left:0}
 .workspace-mode .workspace-toolbar .current-branch{display:none!important}
}
@media(max-width:930px){
 .workspace-mode .workspace-toolbar .pynix-pycharm-right{gap:1px}
 .workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-mode{
  min-width:90px!important;max-width:105px!important
 }
}
</style>"""

CHROME_SCRIPT = r"""<script>
(() => {
 const icons=__CHROME_ICONS__;
 const iconless=__ICONLESS__;
 const makeIcon=(key)=>{
  const source=icons[key];
  if(!source)return null;
  const parsed=new DOMParser().parseFromString(source,'image/svg+xml');
  if(parsed.documentElement.localName!=='svg'||parsed.querySelector('parsererror'))return null;
  const svg=document.importNode(parsed.documentElement,true);
  svg.setAttribute('aria-hidden','true');
  svg.setAttribute('focusable','false');
  return svg;
 };
 const toolButton=(label,icon,action)=>{
  const button=document.createElement('button');
  button.type='button';button.className='pynix-pycharm-icon-button';
  button.title=label;button.setAttribute('aria-label',label);
  const svg=iconless?null:makeIcon(icon);
  if(svg)button.appendChild(svg);
  else button.textContent=label;
  button.addEventListener('click',action);
  return button;
 };
 const initIdentity=()=>{
  const toolbar=document.querySelector('.workspace-mode .workspace-toolbar');
  if(!toolbar||toolbar.querySelector('.pynix-toolbar-identity'))return;
  const title=toolbar.querySelector(':scope>strong');
  const legacyProject=toolbar.querySelector(':scope>.current-branch');
  // attach_workspace provides the real project directory name. The arrow
  // was previously a separate DOM child inside .current-branch.
  const projectName=(legacyProject?.textContent||'').trim()||
                    (title?.textContent||'PYNIX').trim();
  const projectLabel=projectName.startsWith('⑂')?
                     (title?.textContent||'PYNIX').trim():projectName;
  const left=document.createElement('div');
  left.className='pynix-toolbar-identity';
  const build=(className,label,aria,action)=>{
   const button=document.createElement('button');
   button.type='button';button.className=className;
   button.title=label;button.setAttribute('aria-label',aria);
   button.dataset.pynixTooltip=label;
   button.addEventListener('click',action);
   return button;
  };
  const project=build('pynix-toolbar-project',projectLabel,
   'Project: '+projectLabel+' — Show Project tool window',()=>{
    document.querySelectorAll('.workspace-mode .rail>.rail-item')[0]?.click();
   });
  const brand=document.createElement('span');
  brand.className='pynix-toolbar-project-badge';
  brand.textContent='PY';
  brand.setAttribute('aria-hidden','true');
  const projectText=document.createElement('span');
  projectText.className='pynix-toolbar-project-name';
  projectText.textContent=projectLabel;
  project.append(brand,projectText);
  const projectArrow=makeIcon('general/chevronDown');
  if(projectArrow){
   projectArrow.classList.add('pynix-toolbar-project-chevron');
   project.appendChild(projectArrow);
  }
  // Actual branch name is read from the existing read-only Git snapshot.
  const snapshot=window.pynixGitSnapshot;
  const branchName=snapshot?.available&&snapshot.branch?
                   snapshot.branch:'';
  const branchLabel=branchName||'Git';
  const branchTitle=branchName?'Git Branch: '+branchName:
                    'Git: No current branch';
  const branch=build('pynix-toolbar-branch',branchTitle,
   branchTitle+' — Show Git tool window',()=>{
    document.querySelectorAll('.workspace-mode .rail>.rail-item')[2]?.click();
   });
  const branchIcon=makeIcon('toolwindows/vcs');
  if(branchIcon){
   branchIcon.classList.add('pynix-toolbar-branch-icon');
   branch.appendChild(branchIcon);
  }
  const branchText=document.createElement('span');
  branchText.className='pynix-toolbar-branch-name';
  branchText.textContent=branchLabel;
  branch.appendChild(branchText);
  const branchArrow=makeIcon('general/chevronDown');
  if(branchArrow){
   branchArrow.classList.add('pynix-toolbar-branch-chevron');
   branch.appendChild(branchArrow);
  }
  left.append(project,branch);
  toolbar.insertBefore(left,title||legacyProject||toolbar.firstChild);
  // Delete the obsolete disconnected text and arrow: one button replaces
  // the old PYNIX label, and a different button represents the Git branch.
  title?.remove();
  legacyProject?.remove();
 };
 const initToolbar=()=>{
  const toolbar=document.querySelector('.workspace-mode .workspace-toolbar');
  if(!toolbar||toolbar.querySelector('.pynix-pycharm-center'))return;
  const center=document.createElement('div');
  center.className='pynix-pycharm-center';
  const right=document.createElement('div');
  right.className='pynix-pycharm-right';
  const select=toolbar.querySelector('.pynix-run-mode');
  const run=toolbar.querySelector('.pynix-run-action');
  const debug=toolbar.querySelector('.pynix-debug-primary');
  const stop=toolbar.querySelector('.pynix-stop-action');
  const tools=toolbar.querySelector('.pynix-tools-menu');
  for(const el of [select,run,debug,stop,tools])if(el)center.appendChild(el);
  if(tools){
   const summary=tools.querySelector(':scope>summary');
   if(summary){
    summary.replaceChildren(iconless?document.createTextNode('More'):
      (makeIcon('general/moreVertical')||document.createTextNode('⋮')));
    summary.title='More run and editor actions';
    summary.setAttribute('aria-label','More run and editor actions');
   }
   const items=tools.querySelector('.pynix-tools-menu-items');
   const save=toolbar.querySelector('.pynix-save-action');
   if(items&&save)items.prepend(save);
   const debugStatus=toolbar.querySelector('.pynix-debug-status');
   if(items&&debugStatus)items.appendChild(debugStatus);
  }
  right.append(
   toolButton('Search in project','general/search',()=>{
    document.querySelectorAll('.workspace-mode .rail>.rail-item')[1]?.click();
   }),
   toolButton('Settings','general/settings',()=>{
    document.querySelectorAll('.workspace-mode .rail>.rail-item')[5]?.click();
   })
  );
  toolbar.append(center,right);
 };
 const quick=(label,icon,action)=>{
  const button=document.createElement('button');
  button.type='button';button.className='pynix-project-quick-button';
  button.title=label;button.setAttribute('aria-label',label);
  const svg=iconless?null:makeIcon(icon);
  if(svg)button.appendChild(svg);
  else button.textContent=({'New PYNIX file':'New','Select opened file':'Find',
   'Expand visible folders (up to 30)':'Expand',
   'Hide Project tool window':'Hide'})[label]||label;
  button.addEventListener('click',action);
  return button;
 };
 const initProjectHeader=()=>{
  const head=document.querySelector('.workspace-mode .tree .pynix-project-header');
  if(!head||head.dataset.pynixPyCharmHeader)return;
  head.dataset.pynixPyCharmHeader='1';
  const title=head.querySelector(':scope>span:first-child');
  if(title){title.textContent='Project';title.title='Project';}
  const actions=head.querySelector('.pynix-project-header-actions');
  if(!actions)return;
  const collapse=actions.querySelector('.pynix-project-header-button');
  const count=actions.querySelector(':scope>span:first-child');
  if(count)head.title=count.textContent;
  const create=quick('New PYNIX file','general/add',()=>{
   document.querySelector('.pynix-new-source')?.click();
  });
  const locate=quick('Select opened file','general/locate',()=>{
   document.querySelector('.workspace-mode .project-entry.workspace-selected')
    ?.scrollIntoView({block:'nearest'});
  });
  const expand=quick('Expand visible folders (up to 30)','general/expandAll',()=>{
   // Tree rows are rebuilt on every expansion. Re-query between clicks and
   // cap the work so a large project remains responsive.
   for(let i=0;i<30;i++){
    const row=document.querySelector(
     '.workspace-mode .tree .project-entry:has(.project-chevron.collapsed)');
    if(!row)break;
    row.click();
   }
  });
  const more=document.createElement('details');
  more.className='pynix-project-more-menu';
  const summary=document.createElement('summary');
  summary.className='pynix-project-quick-button';
  summary.replaceChildren(iconless?document.createTextNode('More'):
   (makeIcon('general/moreVertical')||document.createTextNode('⋮')));
  summary.title='Project view options';
  summary.setAttribute('aria-label','Project view options');
  const menu=document.createElement('div');
  const collapseItem=document.createElement('button');
  collapseItem.type='button';collapseItem.textContent='Collapse all folders';
  collapseItem.addEventListener('click',()=>{collapse?.click();more.open=false;});
  menu.appendChild(collapseItem);
  more.append(summary,menu);
  const minimize=quick('Hide Project tool window','general/hide',()=>{
   document.querySelectorAll('.workspace-mode .rail>.rail-item')[0]?.click();
  });
  if(collapse){
   collapse.replaceChildren(iconless?document.createTextNode('Fold'):
    (makeIcon('general/collapseAll')||document.createTextNode('⌃')));
   collapse.title='Collapse project folders';
  }
  actions.replaceChildren(create,locate,expand);
  if(collapse)actions.appendChild(collapse);
  actions.append(more,minimize);
 };
 const updateBreadcrumb=()=>{
  const host=document.querySelector('.workspace-mode .bottom>span:nth-of-type(1)');
  if(!host)return;
  let label=host.querySelector('.pynix-status-breadcrumb');
  if(!label){
   label=document.createElement('span');
   label.className='pynix-status-breadcrumb';host.appendChild(label);
  }
  const active=document.querySelector('.workspace-mode .editor-tabs .pynix-editor-tab.active');
  const tab=active?.querySelector('.pynix-editor-tab-label');
  const name=(tab?.textContent||'').trim();
  if(name)label.textContent=name;
 };
 const startup=()=>{
  initToolbar();initIdentity();initProjectHeader();updateBreadcrumb();
  const tree=document.querySelector('.workspace-mode .tree');
  if(tree)new MutationObserver(initProjectHeader).observe(tree,{childList:true});
  const tabs=document.querySelector('.workspace-mode .editor-tabs');
  if(tabs)new MutationObserver(updateBreadcrumb).observe(tabs,{
   childList:true,subtree:true,attributes:true,attributeFilter:['class']
  });
 };
 if(document.readyState==='complete')startup();
 else window.addEventListener('load',startup,{once:true});
})();
</script>"""


def apply_pycharm_chrome(document: str, directory: Path = BUNDLED_ICONS, *,
                         dark: bool = True, iconless: bool = False) -> str:
    """Attach screenshot-matched chrome without replacing native behaviors."""
    if "</body>" not in document or 'id="pynix-pycharm-chrome"' in document:
        return document
    try:
        if iconless and not directory.is_dir():
            # Keep the text controls functional in portable environments
            # without the verified JetBrains SVG pack.
            data = {}
        else:
            catalog = JetBrainsIconCatalog(directory)
            # The project/branch controls are the two explicitly restored
            # original JetBrains SVGs in an otherwise iconless native chrome.
            identity_keys = ("general/chevronDown", "toolwindows/vcs")
            keys = identity_keys if iconless else identity_keys + (
                "general/search","general/settings","general/add",
                "general/locate","general/expandAll","general/collapseAll",
                "general/moreVertical","general/hide"
            )
            data = {key: catalog.svg(key,dark=dark,
                                     tool_window=key=="toolwindows/vcs")
                    for key in keys}
    except (OSError,ValueError,KeyError,json.JSONDecodeError):
        return document
    payload = json.dumps(data,ensure_ascii=True).replace("<","\\u003c")
    script = CHROME_SCRIPT.replace("__CHROME_ICONS__",payload).replace(
        "__ICONLESS__", "true" if iconless else "false"
    )
    return document.replace("</body>",CHROME_STYLE+script+"</body>",1)

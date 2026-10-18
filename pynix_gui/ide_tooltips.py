# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Shared PyCharm-style hover/focus tooltips for native PYNIX IDE controls.

WKWebView native title tooltips are unreliable. Install one delegated overlay
instead; it survives DOM replacement, preserved event handlers and resizing.
Shortcut labels match the screenshot, but do not register fake key bindings.
"""
from __future__ import annotations
import json


TOOLTIP_SHORTCUTS = {
    # Original screenshots: upper left + left bottom + right top.
    "Project": "⌘1",
    "Commit": "⌘0",
    "Structure": "⌘7",
    "Bookmarks": "⌘2",
    "Find": "⌘3",
    "Run": "⌘4",
    "Debug": "⌘5",
    "Services": "⌘8",
    "Terminal": "⌥F12",
    "Problems": "⌘6",
    "Git": "⌘9",
    "AI Chat": "⌥⇧1",
}

TOOLTIP_STYLE = """<style id="pynix-native-tooltips-style">
.workspace-mode .pynix-native-tooltip{
 position:fixed!important;z-index:10000!important;
 display:flex;align-items:center;justify-content:space-between;gap:15px;
 max-width:min(370px,calc(100vw - 16px));width:max-content;
 min-height:31px;box-sizing:border-box;
 padding:6px 10px;border:1px solid #70737b;border-radius:7px;
 background:#34353b;color:#d9dbe0;
 box-shadow:0 4px 12px #000a;
 font:13px/1.4 -apple-system,BlinkMacSystemFont,system-ui,sans-serif;
 white-space:nowrap;pointer-events:none!important;
 -webkit-user-select:none;user-select:none;
}
.workspace-mode .pynix-native-tooltip[hidden]{
 display:none!important;
}
.workspace-mode .pynix-native-tooltip-name{
 min-width:0;overflow:hidden;text-overflow:ellipsis;
 white-space:pre-line;
}
.workspace-mode .pynix-native-tooltip-shortcut{
 flex:0 0 auto;white-space:nowrap;color:#afb2bb;
 font:13px/1.4 -apple-system,BlinkMacSystemFont,system-ui,sans-serif;
}
@media(prefers-reduced-motion:reduce){
 .workspace-mode .pynix-native-tooltip{transition:none!important}
}
</style>"""

TOOLTIP_SCRIPT = r"""<script id="pynix-native-tooltips-script">
(() => {
 if(window.pynixNativeTooltipsInstalled)return;
 window.pynixNativeTooltipsInstalled=true;
 const shortcuts=__TOOLTIP_SHORTCUTS__;
 // Event delegation includes controls created later by the workspace,
 // PyCharm chrome, debugger or Project tree MutationObserver.
 const selectors=[
  '.pynix-extra-tool',
  '.pynix-tool-profile-more',
  '.pynix-project-quick-button',
  '.pynix-project-header-button',
  '.pynix-project-more-menu>summary',
  '.pynix-toolbar-project',
  '.pynix-toolbar-branch',
  '.pynix-pycharm-icon-button',
  '.pynix-pycharm-center>.pynix-run-action',
  '.pynix-pycharm-center>.pynix-debug-primary',
  '.pynix-pycharm-center>.pynix-stop-action',
  '.pynix-pycharm-center>.pynix-run-mode',
  '.pynix-current-config',
  '.pynix-config-options button',
  '.pynix-run-with-params',
  '.pynix-pycharm-center>.pynix-tools-menu>summary',
  '.workspace-toolbar button[title]',
  '.pynix-tool-window-toggle',
  '.pynix-tool-window-restore',
  '.pynix-debug-panel-toolbar button[title]',
  '.pynix-editor-tab button[title]',
  '.pynix-editor-tab [title]',
  '.pynix-tabs-action',
  '.pynix-project-header-actions [title]',
 ].join(',');
 let tip=null,nameNode=null,shortcutNode=null;
 let hovered=null,focused=null,scheduled=0;
 const clearScheduled=()=>{
  if(scheduled){window.clearTimeout(scheduled);scheduled=0;}
 };
 const hide=()=>{
  clearScheduled();
  if(tip)tip.hidden=true;
 };
 const ensure=()=>{
  if(tip)return true;
  const host=document.querySelector('.workspace-mode');
  if(!host)return false;
  tip=document.createElement('div');
  tip.className='pynix-native-tooltip';
  tip.hidden=true;
  tip.setAttribute('role','tooltip');
  tip.setAttribute('aria-live','off');
  nameNode=document.createElement('span');
  nameNode.className='pynix-native-tooltip-name';
  shortcutNode=document.createElement('span');
  shortcutNode.className='pynix-native-tooltip-shortcut';
  tip.append(nameNode,shortcutNode);
  // The tooltip is a child of body, NOT the clipped/scrolling sidebar.
  document.body.appendChild(tip);
  return true;
 };
 const getLabel=button=>{
  if(!button)return '';
  let text=button.dataset.pynixTooltip||button.dataset.toolWindow||
   button.getAttribute('title')||button.getAttribute('aria-label')||'';
  text=text.replace(/\s*— not implemented in PYNIX IDE\s*$/,'').trim();
  if(!text)text=(button.textContent||'').trim();
  return text;
 };
 const resolve=event=>{
  const el=event.target;
  if(!el||typeof el.closest!=='function')return null;
  const button=el.closest(selectors);
  return button?.closest('.workspace-mode')?button:null;
 };
 const position=button=>{
  const bounds=button.getBoundingClientRect();
  const size=tip.getBoundingClientRect();
  const viewportWidth=document.documentElement.clientWidth;
  const viewportHeight=document.documentElement.clientHeight;
  const gap=7,margin=5;
  let x,y;
  if(button.closest('.ide>.rail')){
   x=bounds.right+gap;
   y=bounds.top+(bounds.height-size.height)/2;
  }else if(button.closest('.right-tools')){
   x=bounds.left-size.width-gap;
   y=bounds.top+(bounds.height-size.height)/2;
  }else if(button.closest('.integrated-terminal,.terminal-toolbar,.bottom')){
   x=bounds.left+(bounds.width-size.width)/2;
   y=bounds.top-size.height-gap;
  }else{
   x=bounds.left+(bounds.width-size.width)/2;
   y=bounds.bottom+gap;
  }
  x=Math.max(margin,Math.min(x,viewportWidth-size.width-margin));
  y=Math.max(margin,Math.min(y,viewportHeight-size.height-margin));
  tip.style.left=Math.round(x)+'px';
  tip.style.top=Math.round(y)+'px';
 };
 const show=button=>{
  if(!button||!button.isConnected||document.hidden||!ensure())return;
  const label=getLabel(button);
  if(!label)return;
  nameNode.textContent=label;
  const shortcut=button.dataset.pynixShortcut||shortcuts[label]||'';
  shortcutNode.textContent=shortcut;
  shortcutNode.hidden=!shortcut;
  tip.style.visibility='hidden';
  tip.hidden=false;
  position(button);
  tip.style.visibility='visible';
 };
 const prepare=button=>{
  // Browser-native title popups can appear late, in a different style,
  // or not at all in WKWebView. Retain their text without double popups.
  if(button.hasAttribute('title')){
   const nativeTitle=button.getAttribute('title')||'';
   if(nativeTitle&&!button.dataset.pynixTooltip)
    button.dataset.pynixTooltip=nativeTitle;
   button.removeAttribute('title');
  }
  if(!button.hasAttribute('aria-label')){
   const accessible=getLabel(button);
   if(accessible)button.setAttribute('aria-label',accessible);
  }
 };
 const enter=button=>{
  if(hovered===button)return;
  hovered=button;
  hide();
  prepare(button);
  scheduled=window.setTimeout(()=>{
   scheduled=0;
   if(hovered===button)show(button);
  },340);
 };
 document.addEventListener('pointerover',event=>{
  const button=resolve(event);
  if(!button)return;
  if(button===hovered)return;
  enter(button);
 },true);
 document.addEventListener('pointerout',event=>{
  if(!hovered)return;
  const from=resolve(event);
  if(from!==hovered)return;
  const next=event.relatedTarget;
  if(next&&hovered.contains(next))return;
  hovered=null;
  hide();
 },true);
 document.addEventListener('focusin',event=>{
  const button=resolve(event);
  if(!button)return;
  focused=button;
  prepare(button);
  clearScheduled();
  show(button);
 },true);
 document.addEventListener('focusout',event=>{
  if(!focused)return;
  const next=event.relatedTarget;
  if(next&&focused.contains(next))return;
  focused=null;
  if(!hovered)hide();
 },true);
 document.addEventListener('pointerdown',hide,true);
 document.addEventListener('keydown',event=>{
  if(event.key==='Escape')hide();
 },true);
 window.addEventListener('scroll',hide,true);
 window.addEventListener('resize',hide);
 window.addEventListener('blur',()=>{
  hovered=null;focused=null;hide();
 });
})();
</script>"""


def apply_native_tooltips(document: str) -> str:
    """Enable a single keyboard-accessible and pointer-accessible tooltip layer."""
    if "</body>" not in document or 'id="pynix-native-tooltips-style"' in document:
        return document
    shortcuts = json.dumps(TOOLTIP_SHORTCUTS, ensure_ascii=True)
    script = TOOLTIP_SCRIPT.replace("__TOOLTIP_SHORTCUTS__", shortcuts)
    return document.replace("</body>", TOOLTIP_STYLE + script + "</body>", 1)

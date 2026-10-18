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

# The IDE product version, independently documented in PYNIX_IDE/docs/VERSIONING.md.
IDE_BETA_VERSION = "1.1.26-dev"

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
/* Keep the original PYNIX run-mode <select> in the DOM for its existing
   backend listeners, but use a real compact JetBrains-style configuration
   button as its visible control. */
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-mode{
 display:none!important;
}
.workspace-mode .workspace-toolbar .pynix-current-config{
 display:inline-flex!important;align-items:center!important;justify-content:flex-start!important;
 flex:0 1 148px!important;box-sizing:border-box!important;
 min-width:86px!important;max-width:164px!important;height:33px!important;
 gap:7px!important;padding:4px 8px!important;
 border:1px solid transparent!important;border-radius:9px!important;
 background:transparent!important;color:#c9cbd2!important;
 cursor:pointer!important;white-space:nowrap!important;
 font:500 13px/1.2 -apple-system,BlinkMacSystemFont,system-ui,sans-serif!important;
}
.workspace-mode .workspace-toolbar .pynix-current-config:hover,
.workspace-mode .workspace-toolbar .pynix-current-config[aria-expanded="true"]{
 background:#3b3945!important;
}
.workspace-mode .workspace-toolbar .pynix-current-config:focus-visible{
 outline:2px solid #80b8f4!important;outline-offset:-2px!important;
}
.workspace-mode .workspace-toolbar .pynix-current-config-label{
 min-width:0!important;flex:1 1 auto!important;overflow:hidden!important;
 text-overflow:ellipsis!important;white-space:nowrap!important;
}
.workspace-mode .workspace-toolbar .pynix-current-config-arrow{
 flex:0 0 16px!important;width:16px!important;height:16px!important;
 display:block!important;transform:none!important;
}
.workspace-mode .workspace-toolbar .pynix-config-options{
 position:absolute!important;top:37px!important;left:0!important;
 display:flex!important;flex-direction:column!important;gap:2px!important;
 width:210px!important;padding:6px!important;border-radius:9px!important;
 background:#28292d!important;border:1px solid #575a62!important;
 box-shadow:0 14px 30px #0009!important;z-index:170!important;
}
.workspace-mode .workspace-toolbar .pynix-config-options[hidden]{display:none!important}
.workspace-mode .workspace-toolbar .pynix-config-options button{
 border:0!important;background:transparent!important;color:#d1d2d7!important;
 border-radius:6px!important;width:100%!important;min-height:29px!important;
 padding:6px 9px!important;text-align:left!important;
 font:12px/1.3 -apple-system,BlinkMacSystemFont,system-ui,sans-serif!important;
 cursor:pointer!important;
}
.workspace-mode .workspace-toolbar .pynix-config-options button:hover,
.workspace-mode .workspace-toolbar .pynix-config-options button[aria-checked="true"]{
 background:#34517d!important;color:#edf1fa!important
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
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-action:hover,
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary:hover{
 background:#3b3945!important;border-radius:9px!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-run-action svg,
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary svg{
 display:block!important;width:19px!important;height:19px!important
}

.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-tools-menu>summary{
 width:33px!important;height:33px!important;display:flex!important;
 align-items:center!important;justify-content:center!important;
 padding:0!important;background:transparent!important;font-size:18px!important;
 border-radius:8px!important;cursor:pointer!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-tools-menu[open]>summary,
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-tools-menu>summary:hover{
 background:#3b3945!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center .pynix-tools-menu-items{
 width:298px!important;max-width:calc(100vw - 12px)!important;
 border-radius:11px!important;background:#292a2f!important;
 border:1px solid #62646c!important;
 box-shadow:0 12px 32px #000a!important;padding:7px!important;
}
.workspace-mode .workspace-toolbar .pynix-run-with-params{
 box-sizing:border-box!important;display:flex!important;align-items:center!important;
 gap:11px!important;width:100%!important;min-height:34px!important;
 padding:5px 10px!important;text-align:left!important;border-radius:7px!important;
 background:transparent!important;border:0!important;
 color:#d1d3d8!important;font:13px/1.3 system-ui,-apple-system,sans-serif!important
}
.workspace-mode .workspace-toolbar .pynix-run-with-params svg{
 display:block!important;flex:0 0 20px!important;
 width:20px!important;height:20px!important
}
.workspace-mode .workspace-toolbar .pynix-run-with-params[aria-disabled="true"]{
 opacity:1!important;cursor:default!important
}
.workspace-mode .workspace-toolbar .pynix-run-with-params:hover,
.workspace-mode .workspace-toolbar .pynix-run-with-params:focus-visible{
 background:#304d7f!important;color:#f1f4fc!important;
 outline:none!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-stop-action:disabled{
 display:none!important
}
.workspace-mode .workspace-toolbar>.pynix-save-action{display:none!important}
.workspace-mode .tree .tree-title.pynix-project-header{
 display:flex!important;align-items:center!important;
 /* Do not re-introduce a legacy fixed 31px height here. */
 padding:0 7px 0 12px!important;
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
 .workspace-mode .workspace-toolbar .pynix-pycharm-center>.pynix-current-config{
  flex-basis:114px!important;max-width:114px!important;
 }
}
@media(prefers-reduced-motion:reduce){
 .workspace-mode .workspace-toolbar .pynix-current-config{transition:none!important}
}

/* Search Everywhere and release/status elements belong to IDE V4 chrome. */
.workspace-mode .pynix-pycharm-right .pynix-ide-beta{
 display:inline-flex;align-items:center;justify-content:center;
 box-sizing:border-box;white-space:nowrap;flex:0 0 auto;height:33px;
 padding:0 14px;border:2px solid #416e50;border-radius:20px;
 background:rgba(43,90,54,.07);color:#73b887;
 font:500 12px/1 -apple-system,BlinkMacSystemFont,system-ui,sans-serif
}
.workspace-mode .pynix-pycharm-right .pynix-ide-settings{position:relative}
.workspace-mode .pynix-pycharm-right .pynix-ide-settings[data-updates-available="true"]::after{
 content:"";position:absolute;top:4px;right:4px;display:block;
 width:7px;height:7px;border:1px solid #2b2932;border-radius:50%;
 background:#c29b55;pointer-events:none
}
.workspace-mode .pynix-search-everywhere-backdrop{
 position:fixed;inset:0;z-index:8100;background:rgba(0,0,0,.25);
 display:flex;align-items:flex-start;justify-content:center;
 padding:65px 12px 16px;box-sizing:border-box
}
.workspace-mode .pynix-search-everywhere-backdrop[hidden]{display:none!important}
.workspace-mode .pynix-search-everywhere-dialog{
 box-sizing:border-box;width:100%;max-width:670px;
 max-height:min(600px,calc(100vh - 85px));
 border:1px solid #656971;border-radius:11px;background:#2d2e34;
 box-shadow:0 16px 46px #0009;color:#dedfe5;
 display:flex;flex-direction:column;overflow:hidden;
 font:13px/1.4 -apple-system,BlinkMacSystemFont,system-ui,sans-serif
}
.workspace-mode .pynix-search-everywhere-heading{
 font-weight:600;padding:13px 15px 3px;font-size:14px
}
.workspace-mode .pynix-search-everywhere-input{
 box-sizing:border-box;width:calc(100% - 24px);height:38px;margin:9px 12px;
 border:1px solid #777b85;border-radius:7px;background:#202127;color:#f1f2f4;
 padding:0 12px;font:14px -apple-system,BlinkMacSystemFont,system-ui,sans-serif;
 outline:none
}
.workspace-mode .pynix-search-everywhere-input:focus{border-color:#8ca9d9}
.workspace-mode .pynix-search-everywhere-results{
 overflow-y:auto;min-height:36px;padding:0 8px 9px
}
.workspace-mode .pynix-search-everywhere-result{
 box-sizing:border-box;display:flex;align-items:center;gap:10px;width:100%;
 min-height:34px;padding:6px 8px;border:0;border-radius:5px;
 color:#e2e3e7;background:transparent;text-align:left;cursor:pointer
}
.workspace-mode .pynix-search-everywhere-result[aria-selected="true"],
.workspace-mode .pynix-search-everywhere-result:hover{background:#36557c}
.workspace-mode .pynix-search-everywhere-kind{
 color:#9da4b4;font-size:11px;flex:0 0 84px
}
.workspace-mode .pynix-search-everywhere-name{
 font-size:13px;min-width:0;overflow:hidden;text-overflow:ellipsis;
 white-space:nowrap
}
.workspace-mode .pynix-search-everywhere-path{
 color:#a8acb7;font-size:11px;margin-left:auto;min-width:0;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap
}
.workspace-mode .pynix-search-everywhere-empty{
 padding:12px;color:#a8aab3
}
@media(max-width:930px){
 .workspace-mode .pynix-pycharm-right .pynix-ide-beta{
  padding:0 8px;font-size:11px
 }
}

/* Project V4: one quiet toolbar on hover anywhere within the tree, not only
   within its 32px header. No action moves or changes the tree row geometry. */
/* Standard Project width fits all six icon buttons and the view selector;
   existing user-resized --explorer-width continues to win. */
.workspace-mode .tree{
 container-type:inline-size;width:var(--explorer-width,310px)!important;
 max-width:calc(100vw - 450px)!important;
}
.workspace-mode .tree .pynix-project-header{
 position:relative!important;isolation:isolate!important;overflow:visible!important;
}
.workspace-mode .tree .pynix-project-header-actions{
 display:flex!important;align-items:center!important;justify-content:flex-end!important;
 flex:0 0 auto!important;gap:1px!important;
 opacity:0!important;pointer-events:none!important;
}
.workspace-mode .tree:hover .pynix-project-header-actions,
.workspace-mode .tree:focus-within .pynix-project-header-actions,
.workspace-mode .tree .pynix-project-header-actions:has(details[open]){
 opacity:1!important;pointer-events:auto!important;
}
.workspace-mode .tree .pynix-project-view-switcher{flex:0 0 auto;min-width:0}
.workspace-mode .tree .pynix-project-view-switcher>summary{
 width:auto!important;min-width:68px!important;padding:0 4px!important;
 display:inline-flex!important;align-items:center!important;gap:6px!important;
 color:#d0d2d7!important;font-size:13px!important;font-weight:600!important
}
.workspace-mode .tree .pynix-project-view-switcher>summary svg{
 width:14px!important;height:14px!important;
}
.workspace-mode .tree .pynix-project-view-label{
 display:inline-block;min-width:0;white-space:nowrap;
}
.workspace-mode .tree .pynix-project-quick-button,
.workspace-mode .tree .pynix-project-header-button{
 display:inline-flex!important;align-items:center!important;justify-content:center!important;
 width:22px!important;height:26px!important;min-width:22px!important;
 flex:0 0 22px!important;padding:3px!important;
 box-sizing:border-box!important;border:0!important;border-radius:6px!important;
 background:transparent!important;color:#b5b7be!important;
}
.workspace-mode .tree .pynix-project-quick-button>svg,
.workspace-mode .tree .pynix-project-header-button>svg{
 display:block!important;width:18px!important;height:18px!important;
 max-width:18px!important;max-height:18px!important;
}
.workspace-mode .tree .pynix-project-quick-button:hover,
.workspace-mode .tree .pynix-project-header-button:hover,
.workspace-mode .tree .pynix-project-quick-button:focus-visible,
.workspace-mode .tree .pynix-project-header-button:focus-visible,
.workspace-mode .tree details[open]>summary.pynix-project-quick-button{
 background:#3a3d45!important;outline:none!important;color:#e1e3e8!important;
}
.workspace-mode .tree .pynix-project-header-separator{
 display:block!important;align-self:center;flex:0 0 1px!important;
 width:1px!important;height:21px!important;min-width:1px!important;
 margin:0 3px!important;background:#505158!important
}
.workspace-mode .tree .pynix-project-view-switcher>summary,
.workspace-mode .tree .pynix-project-create-menu>summary,
.workspace-mode .tree .pynix-project-more-menu>summary{
 list-style:none!important;cursor:pointer!important;
}
.workspace-mode .tree .pynix-project-view-switcher>summary::-webkit-details-marker,
.workspace-mode .tree .pynix-project-create-menu>summary::-webkit-details-marker,
.workspace-mode .tree .pynix-project-more-menu>summary::-webkit-details-marker{
 display:none!important;
}
.workspace-mode .tree .pynix-project-create-menu>summary:after{
 content:"";position:absolute;bottom:3px;right:2px;width:5px;height:5px;
 border-right:1px solid #aeb0b8;transform:rotate(45deg);
}
.workspace-mode .tree .pynix-project-create-menu,
.workspace-mode .tree .pynix-project-more-menu,
.workspace-mode .tree .pynix-project-view-switcher{position:relative!important}
.workspace-mode .tree .pynix-project-popup{
 position:absolute!important;top:30px!important;right:0!important;
 z-index:400!important;min-width:158px!important;width:max-content!important;
 max-width:min(265px,90vw)!important;background:#303137!important;
 border:1px solid #53565f!important;border-radius:8px!important;padding:5px!important;
 box-shadow:0 12px 28px #0008!important
}
.workspace-mode .tree .pynix-project-popup>button{
 display:block!important;width:100%!important;min-height:28px!important;
 border:0!important;border-radius:5px!important;padding:4px 9px!important;
 text-align:left!important;color:#dadbe0!important;background:transparent!important;
 white-space:nowrap!important;font:12px/1.4 -apple-system,system-ui,sans-serif!important
}
.workspace-mode .tree .pynix-project-popup>button:hover,
.workspace-mode .tree .pynix-project-popup>button:focus-visible{
 background:#3a4c69!important;color:#fff!important
}
.workspace-mode .tree .project-root .pynix-project-root-name{
 flex:0 0 auto!important;font-weight:600!important;
 color:#c7c9ce!important;overflow:visible!important;
}
.workspace-mode .tree .project-root .pynix-project-root-path{
 flex:1 1 auto!important;min-width:0!important;
 overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;
 color:#767980!important;font-weight:400!important;font-size:12px!important;
}
.workspace-mode .tree .project-root{overflow:hidden!important}
@container (max-width:250px){
 .pynix-project-header-actions>.pynix-project-quick-button:nth-of-type(1),
 .pynix-project-header-actions>.pynix-project-quick-button:nth-of-type(2),
 .pynix-project-header-actions>.pynix-project-header-button{
  display:none!important;
 }
 /* Narrow panes keep New, Options and Hide accessible; the three hidden
    actions remain available in Options until the user widens the pane. */
}
@media(prefers-reduced-motion:reduce){
 .workspace-mode .tree .pynix-project-header-actions{transition:none!important}
}

/* V4 live window-resize invariant: one flex row owns all three toolbar
   groups. Never absolutely position Current File / Run / Debug at 70%. */
.workspace-mode .workspace-toolbar{
 display:flex!important;align-items:center!important;flex-wrap:nowrap!important;
 min-width:0!important;gap:8px!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-identity{
 flex:0 1 auto!important;min-width:0!important;max-width:100%!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch{
 min-width:0!important;flex:0 1 auto!important
}
.workspace-mode .workspace-toolbar>.toolbar-spacer{
 display:block!important;flex:1 1 0px!important;min-width:0!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-center{
 position:relative!important;left:auto!important;top:auto!important;
 transform:none!important;flex:0 0 auto!important;
 min-width:0!important;margin:0!important;
 display:flex!important;align-items:center!important;gap:7px!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-right{
 position:relative!important;flex:0 1 auto!important;min-width:0!important;
 margin:0!important;display:flex!important;align-items:center!important;
 justify-content:flex-end!important;gap:6px!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-right .pynix-pycharm-icon-button{
 flex:0 0 31px!important;min-width:31px!important;width:31px!important;
 height:31px!important;padding:5px!important;font-size:0!important
}
.workspace-mode .workspace-toolbar .pynix-pycharm-right .pynix-ide-beta{
 box-sizing:border-box!important;flex:0 1 auto!important;min-width:0!important;
 max-width:100%!important;overflow:hidden!important;text-overflow:ellipsis!important;
 padding-inline:9px!important;white-space:nowrap!important
}
.workspace-mode .workspace-toolbar .pynix-toolbar-project-name,
.workspace-mode .workspace-toolbar .pynix-toolbar-branch-name{
 min-width:0!important;flex:0 1 auto!important
}
@media(max-width:1060px){
 .workspace-mode .workspace-toolbar{gap:6px!important}
 .workspace-mode .workspace-toolbar .pynix-toolbar-identity{gap:5px!important}
 .workspace-mode .workspace-toolbar .pynix-pycharm-center{gap:4px!important}
 .workspace-mode .workspace-toolbar .pynix-pycharm-right{gap:3px!important}
 .workspace-mode .workspace-toolbar .pynix-toolbar-project-name,
 .workspace-mode .workspace-toolbar .pynix-toolbar-branch-name{max-width:64px!important}
}
/* Breakpoints shorten labels, never switch between position models. */
@media(max-width:930px){
 .workspace-mode .workspace-toolbar .pynix-current-config{
  flex-basis:104px!important;max-width:104px!important
 }
 .workspace-mode .workspace-toolbar .pynix-pycharm-right .pynix-ide-beta{
  font-size:0!important;padding-inline:7px!important
 }
 .workspace-mode .workspace-toolbar .pynix-pycharm-right .pynix-ide-beta::before{
  content:attr(data-compact);
  font:500 11px/1 -apple-system,BlinkMacSystemFont,system-ui,sans-serif
 }
 .workspace-mode .workspace-toolbar .pynix-toolbar-project-name,
 .workspace-mode .workspace-toolbar .pynix-toolbar-branch-name{max-width:52px!important}
}
/* Restored SVG controls use 29/31px hit areas even with iconless mode on.
   Otherwise old text fallback min-width 43/48px can reintroduce collisions. */
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-right .pynix-pycharm-icon-button{
 min-width:31px!important;width:31px!important;font-size:0!important;
 padding:5px!important
}
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center>.pynix-run-action,
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center>.pynix-debug-primary{
 flex:0 0 29px!important;min-width:29px!important;width:29px!important;
 font-size:0!important;padding:5px!important
}
.workspace-mode.pynix-iconless .workspace-toolbar .pynix-pycharm-center>.pynix-tools-menu>summary{
 flex:0 0 33px!important;min-width:33px!important;width:33px!important;
 font-size:0!important;padding:0!important
}

/* The Explorer header and editor tab strip belong to the same 43px row.
   Match the original .tree-title.pynix-project-header specificity: a weaker
   selector with !important could not override its old 31px height. */
.workspace-mode .tree .tree-title.pynix-project-header{
 box-sizing:border-box!important;position:sticky!important;top:0!important;
 z-index:35!important;height:43px!important;min-height:43px!important;
 max-height:43px!important;margin:0!important;
 padding:0 8px!important;display:flex!important;align-items:center!important;
 background:#1e1f22!important;border-bottom:1px solid #34363c!important;
 border-radius:9px 9px 0 0!important;
}
.workspace-mode .tree{
 scroll-padding-top:43px!important;
}
.workspace-mode .editor-tabs{
 height:43px!important;min-height:43px!important;max-height:43px!important;
}

/* Real editor V4 tabs: one clipped strip plus persistent right actions.
   Popups attach to body because the editor-tab row must clip tab overflow. */
.workspace-mode .editor-tabs{
 display:flex!important;align-items:center!important;flex-wrap:nowrap!important;
 box-sizing:border-box!important;height:43px!important;min-height:43px!important;
 max-height:43px!important;overflow:hidden!important;gap:0!important;
 padding:5px 6px 9px!important
}
.workspace-mode .editor-tabs .pynix-tabs-strip{
 flex:1 1 auto!important;min-width:0!important;width:0!important;
 display:flex!important;align-items:center!important;gap:4px!important;
 overflow:hidden!important;white-space:nowrap!important
}
.workspace-mode .editor-tabs .pynix-editor-tab[hidden]{
 display:none!important
}
.workspace-mode .editor-tabs .pynix-tabs-actions{
 display:flex!important;align-items:center!important;justify-content:flex-end!important;
 flex:0 0 auto!important;gap:3px!important;padding:0 2px 0 5px!important;
 height:100%!important;min-width:0!important
}
.workspace-mode .editor-tabs .pynix-tabs-action{
 box-sizing:border-box!important;flex:0 0 29px!important;
 display:inline-flex!important;align-items:center!important;justify-content:center!important;
 width:29px!important;min-width:29px!important;height:29px!important;min-height:29px!important;
 margin:0!important;padding:5px!important;border:0!important;border-radius:7px!important;
 background:transparent!important;color:#bfc1c7!important;cursor:pointer!important
}
.workspace-mode .editor-tabs .pynix-tabs-action[hidden]{
 display:none!important
}
.workspace-mode .editor-tabs .pynix-tabs-action>svg{
 width:19px!important;height:19px!important;display:block!important;flex:0 0 19px!important
}
.workspace-mode .editor-tabs .pynix-tabs-action:hover,
.workspace-mode .editor-tabs .pynix-tabs-action:focus-visible,
.workspace-mode .editor-tabs .pynix-tabs-action[aria-expanded="true"]{
 background:#3a3d45!important;color:#f0f1f4!important;
 outline:none!important
}
.workspace-mode>.pynix-tabs-popup{
 box-sizing:border-box;position:fixed;z-index:11000;
 min-width:246px;max-width:min(420px,calc(100vw - 12px));
 max-height:min(570px,calc(100vh - 12px));overflow-y:auto;
 background:#2e3036;border:1px solid #575a63;border-radius:9px;
 padding:6px;box-shadow:0 12px 35px #0009
}
.workspace-mode>.pynix-tabs-popup[hidden]{display:none!important}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-row{
 display:flex;align-items:center;min-height:32px;border-radius:6px;
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-item{
 display:flex;align-items:center;gap:9px;flex:1 1 auto;min-width:0;min-height:32px;
 background:transparent;border:0;border-radius:6px;color:#d4d5da;
 font:13px/1.4 -apple-system,BlinkMacSystemFont,system-ui,sans-serif;
 padding:5px 9px;text-align:left;cursor:pointer
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-row.active{
 background:#304d79
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-item:hover:not(:disabled),
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-item:focus-visible,
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-close:hover{
 background:#365785;color:#fff;outline:none
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-item:disabled{
 opacity:.46;cursor:default
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-label{
 flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-shortcut{
 flex:0 0 auto;color:#a6a8b1;font-size:12px;margin-left:12px
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-close{
 flex:0 0 25px;width:25px;height:25px;border:0;border-radius:5px;
 background:transparent;color:#c5c6cd;font-size:19px;cursor:pointer
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-divider{
 height:1px;background:#484b53;margin:6px 4px
}

/* V4 PyCharm tab-action menu: compact density, full-row mouse/keyboard
   selection, source glyphs and shortcuts matching the same 13px text scale.
   This is intentionally the last layer; legacy popup styles remain above. */
.workspace-mode>.pynix-tabs-popup{
 box-sizing:border-box!important;
 width:min(228px,calc(100vw - 12px))!important;
 min-width:0!important;max-width:calc(100vw - 12px)!important;
 max-height:min(485px,calc(100vh - 16px))!important;
 padding:4px!important;border-radius:7px!important;
 background:#2e3036!important;border:1px solid #55575f!important;
 box-shadow:0 8px 20px rgba(0,0,0,.58)!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-row{
 box-sizing:border-box!important;display:flex!important;align-items:center!important;
 min-height:27px!important;border-radius:5px!important;
 padding:0!important;margin:0!important;
 background:transparent!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-item{
 box-sizing:border-box!important;
 display:flex!important;align-items:center!important;min-width:0!important;
 flex:1 1 0%!important;min-height:27px!important;height:27px!important;
 padding:4px 8px!important;margin:0!important;gap:7px!important;
 background:transparent!important;border:0!important;border-radius:5px!important;
 color:#d2d4da!important;cursor:pointer!important;
 font:400 13px/20px -apple-system,BlinkMacSystemFont,system-ui,sans-serif!important;
 text-align:left!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-shortcut{
 flex:0 0 auto!important;margin-left:auto!important;padding-left:7px!important;
 font:500 13.5px/20px -apple-system,BlinkMacSystemFont,system-ui,sans-serif!important;
 letter-spacing:0!important;color:#aeb1bc!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-label{
 min-width:0!important;flex:1 1 auto!important;white-space:nowrap!important;
 text-overflow:ellipsis!important;overflow:hidden!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-row:is(
 :hover,:focus-within,.pynix-keyboard-selected){
 background:#304d7b!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-row:is(
 :hover,:focus-within,.pynix-keyboard-selected) .pynix-tabs-menu-item:not(:disabled){
 background:transparent!important;color:#f0f2f7!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-row:is(
 :hover,:focus-within,.pynix-keyboard-selected) .pynix-tabs-menu-shortcut{
 color:#d0d9e8!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-item:disabled{
 color:#868991!important;opacity:.78!important;cursor:default!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-row:has(.pynix-tabs-menu-item:disabled){
 background:transparent!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-menu-close{
 flex:0 0 24px!important;width:24px!important;height:24px!important;
 margin-right:2px!important;padding:0!important;font-size:17px!important;
 border-radius:5px!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tabs-divider{
 box-sizing:border-box!important;height:1px!important;
 margin:4px 5px!important;background:#41444c!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tab-file-glyph{
 flex:0 0 18px!important;width:18px!important;height:18px!important;
 display:inline-flex!important;align-items:center!important;justify-content:center!important
}
.workspace-mode>.pynix-tabs-popup .pynix-tab-file-glyph svg{
 width:17px!important;height:17px!important;max-width:17px!important;
 max-height:17px!important;display:block!important
}
/* Real project-scoped editor tab preferences */
.workspace-mode .editor-tabs[data-pynix-icons="false"] .pynix-tab-file-glyph{
 display:none!important
}
.workspace-mode .editor-tabs[data-pynix-close="true"] .pynix-editor-tab .pynix-editor-tab-close{
 visibility:visible!important;pointer-events:auto!important
}
.workspace-mode .editor-tabs[data-pynix-compact="true"] .pynix-editor-tab{
 height:26px!important;min-height:26px!important;max-height:26px!important;
 padding:0 4px!important;gap:3px!important
}
.workspace-mode .editor{position:relative!important}
.workspace-mode .pynix-editor-minimap{
 position:absolute!important;z-index:21!important;
 box-sizing:border-box!important;
 right:0!important;top:43px!important;bottom:0!important;
 width:82px!important;min-width:82px!important;
 border-left:1px solid #363a41!important;background:#232529!important;
 overflow:hidden!important
}
.workspace-mode .pynix-editor-minimap[hidden]{display:none!important}
.workspace-mode .pynix-editor-minimap canvas{
 display:block;width:100%;height:100%;cursor:pointer;outline:none
}
.workspace-mode .pynix-editor-minimap canvas:focus-visible{
 outline:1px solid #7fa4d6!important;outline-offset:-2px!important
}

/* IDE V4 Project text size parity. The source editor's live CSS uses
   13px (both editable text and read-only code). Previous Project styles
   still forced 12px on .entry/.project-label and the muted root path.
   Keep the 24px tree row geometry, SVG sizes and Project toolbar intact. */
.workspace-mode .tree .project-entry{
 font-size:13px!important;
}
.workspace-mode .tree .project-entry .project-label,
.workspace-mode .tree .project-entry .pynix-project-root-name,
.workspace-mode .tree .project-entry .pynix-project-root-path{
 font-size:13px!important;
}

/* Native V4 PyCharm terminal tool-window: preserve the original content
   controller; only the visible chrome changes. The editor and Project tree
   get ALL released height because the dock and resizer leave flex layout. */
.workspace-mode .layout>.section:first-child>.card:first-child>.ide{
 height:auto!important;min-height:0!important;flex:1 1 0%!important;
 max-height:none!important;overflow:hidden!important
}
.workspace-mode .ide>.tree,
.workspace-mode .ide>.editor{
 min-height:0!important;
}
.workspace-mode .integrated-terminal.pynix-tool-window-collapsed{
 display:none!important;height:0!important;min-height:0!important;
 margin:0!important;flex:0 0 0px!important
}
.workspace-mode .terminal-resizer[hidden]{
 display:none!important;height:0!important;min-height:0!important
}
.workspace-mode .pynix-tool-window-restore{
 display:none!important
}
/* Old VS Code-like "Terminal / Problems / Output / Debug Console" tabs stay
   in DOM as programmatic command targets, but the visible dock is PyCharm. */
.workspace-mode .integrated-terminal .terminal-tabs,
.workspace-mode .integrated-terminal .pynix-terminal-session{
 display:none!important
}
.workspace-mode .integrated-terminal{
 display:flex;flex-direction:column;
 background:#1e1f22!important;border:0!important;
 border-radius:9px!important;overflow:hidden!important;
 min-height:135px;max-height:55vh
}
.workspace-mode .integrated-terminal .pynix-terminal-dock-bar{
 box-sizing:border-box!important;order:0!important;
 display:flex!important;align-items:center!important;flex:0 0 36px!important;
 min-width:0!important;height:36px!important;min-height:36px!important;
 padding:0 8px 0 12px!important;gap:6px!important;
 background:#242528!important;border-bottom:1px solid #393a3f!important;
 color:#cfd1d6!important;
 font:500 12px/1 -apple-system,BlinkMacSystemFont,system-ui,sans-serif!important
}
.workspace-mode .pynix-terminal-dock-title{
 flex:0 0 auto;min-width:66px;max-width:150px;
 color:#d5d7dc;font-size:13px;font-weight:600;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis
}
.workspace-mode .pynix-terminal-dock-session{
 box-sizing:border-box;display:inline-flex;align-items:center;gap:4px;
 min-width:0;height:27px;max-width:180px;padding:0 4px 0 10px;
 background:#363941;border:1px solid #494b53;border-radius:7px;
 color:#e0e1e5;font-size:12px
}
.workspace-mode .pynix-terminal-dock-session[hidden]{display:none!important}
.workspace-mode .pynix-terminal-dock-action{
 box-sizing:border-box!important;display:inline-flex!important;
 align-items:center!important;justify-content:center!important;
 width:27px!important;min-width:27px!important;height:27px!important;min-height:27px!important;
 margin:0!important;padding:0!important;
 border:0!important;border-radius:6px!important;
 background:transparent!important;color:#bfc2ca!important;
 font:400 18px/1 -apple-system,BlinkMacSystemFont,system-ui,sans-serif!important;
 cursor:pointer!important
}
.workspace-mode .pynix-terminal-dock-action:hover:not(:disabled),
.workspace-mode .pynix-terminal-dock-action:focus-visible,
.workspace-mode .pynix-terminal-dock-bar details[open]>summary{
 background:#3a3d45!important;color:#f1f2f6!important
}
.workspace-mode .pynix-terminal-dock-action:disabled{
 opacity:.42!important;cursor:default!important
}
.workspace-mode .pynix-terminal-dock-bar details{position:relative;flex:0 0 auto}
.workspace-mode .pynix-terminal-dock-bar details>summary{
 list-style:none;cursor:pointer
}
.workspace-mode .pynix-terminal-dock-bar details>summary::-webkit-details-marker{
 display:none!important
}
.workspace-mode .pynix-terminal-dock-popup{
 position:absolute;z-index:300;top:calc(100% + 7px);right:0;
 box-sizing:border-box;width:max-content;min-width:153px;max-width:240px;
 padding:4px;background:#2e3036;border:1px solid #555760;
 border-radius:8px;box-shadow:0 12px 27px #0009
}
.workspace-mode .pynix-terminal-dock-popup>button{
 box-sizing:border-box;display:block;width:100%;min-height:28px;
 padding:4px 10px;border:0;border-radius:5px;background:transparent;
 text-align:left;color:#d9dbe2;white-space:nowrap;font:12px/18px -apple-system,system-ui,sans-serif;
 cursor:pointer
}
.workspace-mode .pynix-terminal-dock-popup>button:hover,
.workspace-mode .pynix-terminal-dock-popup>button:focus-visible{
 background:#314b78!important;color:#fff!important
}
.workspace-mode .pynix-terminal-dock-gap{
 display:block;flex:1 1 0;min-width:0
}
.workspace-mode .pynix-terminal-dock-agents{
 flex:0 1 auto;min-width:0;border:0;border-radius:5px;
 background:transparent;color:#9da1ab;
 font:500 12px/1 -apple-system,system-ui,sans-serif;
 white-space:nowrap;cursor:default;padding:5px
}
.workspace-mode .pynix-terminal-dock-agents:disabled{opacity:.7}
.workspace-mode .integrated-terminal .terminal-console{
 order:2!important;flex:1 1 0%!important;min-height:0!important;
 box-sizing:border-box!important;background:#1e1f22!important;
 color:#bfc4cd!important;border:0!important;
 padding:9px 13px!important;overflow:auto!important;
 font:13px/19px ui-monospace,SFMono-Regular,Menlo,monospace!important
}
.workspace-mode .integrated-terminal .pynix-debug-panel-toolbar{
 order:1!important
}
@media(max-width:850px){
 .workspace-mode .pynix-terminal-dock-title{min-width:49px}
 .workspace-mode .pynix-terminal-dock-session{max-width:110px}
 .workspace-mode .pynix-terminal-dock-agents{display:none}
}

/* Separate live system PTYs and PYNIX compiler console. */
.workspace-mode .integrated-terminal .terminal-console[hidden],
.workspace-mode .integrated-terminal .pynix-system-terminal[hidden],
.workspace-mode .integrated-terminal .pynix-language-terminal[hidden],
.workspace-mode .pynix-terminal-dock-bar [hidden]{display:none!important}
.workspace-mode .pynix-system-terminal,.workspace-mode .pynix-language-terminal{
 order:2!important;display:flex!important;flex-direction:column!important;
 box-sizing:border-box!important;flex:1 1 0%!important;min-width:0!important;
 min-height:0!important;overflow:hidden!important;padding:6px 11px!important;
 gap:3px!important;background:#1e1f22!important
}
.workspace-mode .pynix-terminal-log{
 flex:1 1 auto!important;min-height:0!important;overflow:auto!important;
 padding:3px 0!important;margin:0!important;min-width:0!important;
 background:transparent!important;color:#d4d7dd!important;
 font:13px/19px ui-monospace,SFMono-Regular,Menlo,monospace!important;
 white-space:pre-wrap!important;overflow-wrap:anywhere!important
}
.workspace-mode .pynix-terminal-input{
 box-sizing:border-box!important;flex:0 0 26px!important;width:100%!important;
 resize:none!important;min-height:26px!important;max-height:26px!important;
 border:0!important;border-top:1px solid #383b42!important;
 outline:none!important;border-radius:0!important;background:transparent!important;
 padding:4px 2px!important;color:#dce2e9!important;
 font:13px/19px ui-monospace,SFMono-Regular,Menlo,monospace!important
}
.workspace-mode .pynix-terminal-session-tabs{
 display:flex!important;align-items:center!important;gap:3px!important;
 flex:0 1 auto!important;min-width:0!important;max-width:min(50%,560px)!important;
 overflow-x:auto!important;scrollbar-width:none!important;height:32px!important
}
.workspace-mode .pynix-terminal-session-tabs::-webkit-scrollbar{display:none}
.workspace-mode .pynix-terminal-session-tab{
 display:flex!important;align-items:center!important;flex:0 0 auto!important;
 height:30px!important;max-width:180px!important;
 border-radius:7px!important;padding:0 3px 0 7px!important;
 background:transparent!important;border:1px solid transparent!important;
 color:#c6c8d0!important
}
.workspace-mode .pynix-terminal-session-tab.active{
 background:#363940!important;border-color:#4a4d56!important;color:#e4e7ec!important
}
.workspace-mode .pynix-terminal-session-select,.workspace-mode .pynix-terminal-session-close{
 display:inline-flex!important;align-items:center!important;justify-content:center!important;
 height:24px!important;background:transparent!important;color:inherit!important;
 border:0!important;padding:0!important;cursor:pointer!important
}
.workspace-mode .pynix-terminal-session-select{
 flex:1 1 auto!important;min-width:0!important;
 font:500 12px/1 -apple-system,system-ui,sans-serif!important;
 white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important
}
.workspace-mode .pynix-terminal-session-close{
 width:23px!important;min-width:23px!important;font-size:17px!important;border-radius:5px!important
}
.workspace-mode .pynix-terminal-session-close:hover{background:#4c5059!important}
.workspace-mode .pynix-terminal-shell-dropdown{position:relative!important}
.workspace-mode .pynix-terminal-shell-chevron{
 display:inline-flex!important;align-items:center!important;justify-content:center!important;
 padding:0!important;line-height:0!important
}
.workspace-mode .pynix-terminal-shell-chevron svg{
 display:block!important;width:15px!important;height:15px!important;
 min-width:15px!important;flex:0 0 15px!important
}
.workspace-mode .pynix-terminal-dock-menu-separator{
 height:1px!important;background:#494b52!important;margin:4px 6px!important
}
.workspace-mode .pynix-terminal-new,.workspace-mode .pynix-terminal-shell-dropdown{
 opacity:0!important;pointer-events:none!important
}
.workspace-mode .integrated-terminal:hover .pynix-terminal-new,
.workspace-mode .integrated-terminal:hover .pynix-terminal-shell-dropdown,
.workspace-mode .integrated-terminal:focus-within .pynix-terminal-new,
.workspace-mode .integrated-terminal:focus-within .pynix-terminal-shell-dropdown,
.workspace-mode .pynix-terminal-shell-dropdown[open]{
 opacity:1!important;pointer-events:auto!important
}
.workspace-mode .pynix-terminal-dock-bar details[hidden]{display:none!important}
.workspace-mode .pynix-terminal-dock-popup{z-index:600!important}
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
  // Titlebar Search/Settings glyphs remain visible in iconless mode.
  const allowedInIconless=icon==='general/search'||icon==='general/settings';
  const svg=(iconless&&!allowedInIconless)?null:makeIcon(icon);
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
 const createRunConfig=(center,select)=>{
  if(!select||center.querySelector('.pynix-current-config'))return;
  const button=document.createElement('button');
  button.type='button';
  button.className='pynix-current-config';
  button.dataset.pynixTooltip='Run configuration: Current File';
  button.setAttribute('aria-label','Run configuration: Current File');
  button.setAttribute('aria-expanded','false');
  button.setAttribute('aria-haspopup','menu');
  const name=document.createElement('span');
  name.className='pynix-current-config-label';
  const arrow=makeIcon('general/chevronDown');
  if(arrow){
   arrow.classList.add('pynix-current-config-arrow');
   button.append(name,arrow);
  }else{
   name.textContent='Current File';
   const chevron=document.createElement('span');
   chevron.textContent='⌄';chevron.setAttribute('aria-hidden','true');
   button.append(name,chevron);
  }
  const popup=document.createElement('div');
  popup.className='pynix-config-options';popup.hidden=true;
  popup.setAttribute('role','menu');
  const options=[
   ['run','Current File'],
   ['check','Check Project'],
  ];
  const close=()=>{
   popup.hidden=true;
   button.setAttribute('aria-expanded','false');
  };
  const sync=()=>{
   const value=select.value;
   name.textContent=value==='check'?'Check Project':'Current File';
   button.dataset.pynixTooltip='Run configuration: '+name.textContent;
   button.setAttribute('aria-label',button.dataset.pynixTooltip);
   for(const item of popup.children)
    item.setAttribute('aria-checked',String(item.dataset.mode===value));
  };
  for(const [value,label] of options){
   const item=document.createElement('button');
   item.type='button';item.textContent=label;
   item.dataset.mode=value;item.setAttribute('role','menuitemradio');
   item.addEventListener('click',()=>{
    select.value=value;
    select.dispatchEvent(new Event('change',{bubbles:true}));
    sync();close();button.focus();
   });
   popup.appendChild(item);
  }
  button.addEventListener('click',()=>{
   popup.hidden=!popup.hidden;
   button.setAttribute('aria-expanded',String(!popup.hidden));
   if(!popup.hidden)popup.querySelector('[aria-checked="true"]')?.focus();
  });
  document.addEventListener('pointerdown',event=>{
   if(!button.contains(event.target)&&!popup.contains(event.target))close();
  },true);
  popup.addEventListener('keydown',event=>{
   if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
   event.preventDefault();
   const options=[...popup.querySelectorAll('button')];
   const index=options.indexOf(document.activeElement);
   const target=event.key==='Home'?0:event.key==='End'?options.length-1:
    (index+(event.key==='ArrowDown'?1:-1)+options.length)%options.length;
   options[target]?.focus();
  });
  document.addEventListener('keydown',event=>{
   if(event.key==='Escape'&&!popup.hidden){close();button.focus();}
  },true);
  select.addEventListener('change',sync);
  center.insertBefore(button,select);
  center.appendChild(popup);
  sync();
 };
 const updateRunActionTooltips=()=>{
  const active=document.querySelector('.workspace-mode .editor-tabs .pynix-editor-tab.active');
  const label=active?.querySelector('.pynix-editor-tab-label');
  const name=(label?.textContent||'').replace(/\s*\*\s*$/,'').trim();
  const run=document.querySelector('.pynix-pycharm-center>.pynix-run-action');
  const debug=document.querySelector('.pynix-pycharm-center>.pynix-debug-primary');
  const actions=[[run,'Run','⌃R'],[debug,'Debug','⌃D']];
  for(const [control,verb,shortcut] of actions){
   if(!control)continue;
   // Labels follow PyCharm, but the real PYNIX run handler still launches
   // the workspace project. Never replace it with a fake file runner.
   const text=name?verb+" '"+name+"'":verb+' project';
   control.dataset.pynixTooltip=text;
   control.dataset.pynixShortcut=shortcut;
   control.setAttribute('aria-label',text);
   control.removeAttribute('title');
  }
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
  createRunConfig(center,select);
  // Keep the existing button nodes and their original run/debug listeners.
  for(const [button,key] of [[run,'run/run'],[debug,'run/debug']]){
   if(!button)continue;
   const icon=makeIcon(key);
   if(icon){
    icon.classList.add('pynix-jetbrains-icon');
    button.replaceChildren(icon);
   }
  }
  if(tools){
   const summary=tools.querySelector(':scope>summary');
   if(summary){
    summary.replaceChildren(makeIcon('general/moreVertical')||
      document.createTextNode('⋮'));
    summary.title='More Actions';
    summary.dataset.pynixTooltip='More Actions';
    summary.setAttribute('aria-label','More Actions');
   }
   const items=tools.querySelector('.pynix-tools-menu-items');
   const save=toolbar.querySelector('.pynix-save-action');
   if(items&&save)items.prepend(save);
   if(items&&!items.querySelector('.pynix-run-with-params')){
    // Parameters are not supported by ProjectRunner yet. Preserve a truthful
    // disabled menu item rather than pretending arguments are forwarded.
    const params=document.createElement('button');
    params.type='button';params.className='pynix-run-with-params';
    params.textContent='Run with Parameters...';
    const edit=makeIcon('general/edit');
    if(edit)params.prepend(edit);
    params.setAttribute('aria-disabled','true');
    params.setAttribute('aria-label','Run with Parameters (not yet supported)');
    params.dataset.pynixTooltip='Run with Parameters (not yet supported by PYNIX)';
    params.setAttribute('tabindex','0');
    // Do not use HTML disabled: allow hover and keyboard focus for the
    // explanatory tooltip. No click listener means no fake run command.
    items.prepend(params);
   }
   const debugStatus=toolbar.querySelector('.pynix-debug-status');
   if(items&&debugStatus)items.appendChild(debugStatus);
  }
  const search=toolButton('Search Everywhere','general/search',()=>{
   window.pynixOpenSearchEverywhere?.();
  });
  search.classList.add('pynix-ide-search');
  search.dataset.pynixTooltip=[
   'Search Everywhere ⇧ ⇧','Searches for:',
   '- Classes','- Files','- Tool Windows','- Actions','- Settings'
  ].join('\n');
  const settings=toolButton('IDE and Project Settings','general/settings',()=>{
   document.querySelectorAll('.workspace-mode .rail>.rail-item')[5]?.click();
  });
  settings.classList.add('pynix-ide-settings');
  const updateSettingsIndicator=()=>{
   // The signal is false until a real update service explicitly sets it.
   const available=window.pynixIDEUpdatesAvailable===true;
   settings.dataset.updatesAvailable=String(available);
   settings.dataset.pynixTooltip=available?
    'Updates available. IDE and Project Settings':'IDE and Project Settings';
   settings.setAttribute('aria-label',settings.dataset.pynixTooltip);
  };
  updateSettingsIndicator();
  document.addEventListener('pynix:updates-available',updateSettingsIndicator);
  const beta=document.createElement('span');
  beta.className='pynix-ide-beta';
  beta.textContent='Beta Version · __IDE_VERSION__';
  beta.dataset.compact='β · __IDE_VERSION__';
  beta.setAttribute('aria-label','PYNIX IDE beta version __IDE_VERSION__');
  right.append(search,settings,beta);
  // Two equally flexible empty regions center Run/Debug between the
  // identity and status clusters without absolute coordinates. Both may
  // shrink to zero during native continuous window resizing.
  const trailingSpacer=document.createElement('div');
  trailingSpacer.className='toolbar-spacer pynix-pycharm-trailing-spacer';
  trailingSpacer.setAttribute('aria-hidden','true');
  toolbar.append(center,trailingSpacer,right);
  updateRunActionTooltips();
 };
 const quick=(label,icon,action)=>{
  const button=document.createElement('button');
  button.type='button';button.className='pynix-project-quick-button';
  button.title=label;button.setAttribute('aria-label',label);
  const svg=makeIcon(icon);
  if(svg)button.appendChild(svg);else button.textContent=label;
  button.addEventListener('click',action);
  return button;
 };
 const menu=(className,label,icon,items)=>{
  const details=document.createElement('details');
  details.className=className;
  const summary=document.createElement('summary');
  summary.className='pynix-project-quick-button';
  summary.title=label;summary.setAttribute('aria-label',label);
  summary.setAttribute('aria-haspopup','menu');
  const glyph=makeIcon(icon);
  if(glyph)summary.appendChild(glyph);else summary.textContent=label;
  const popup=document.createElement('div');
  popup.className='pynix-project-popup';popup.setAttribute('role','menu');
  for(const [caption,handler] of items){
   const button=document.createElement('button');
   button.type='button';button.textContent=caption;button.setAttribute('role','menuitem');
   button.addEventListener('click',()=>{details.open=false;handler();});
   popup.appendChild(button);
  }
  details.append(summary,popup);
  details.addEventListener('keydown',event=>{
   if(event.key==='Escape'&&details.open){event.preventDefault();details.open=false;summary.focus();}
  });
  // Only the active menu is outside-click dismissible. Bind once globally
  // to avoid retaining dead DOM on every renderTree() rebuild.
  return details;
 };
 document.addEventListener('pointerdown',event=>{
  document.querySelectorAll('.tree .pynix-project-header details[open]').forEach(details=>{
   if(!details.contains(event.target))details.open=false;
  });
 });
 const initProjectHeader=()=>{
  const head=document.querySelector('.workspace-mode .tree .pynix-project-header');
  if(!head||head.dataset.pynixPyCharmHeader)return;
  head.dataset.pynixPyCharmHeader='1';
  const title=head.querySelector(':scope>span:first-child');
  const actions=head.querySelector('.pynix-project-header-actions');
  if(!actions)return;
  const collapse=actions.querySelector('.pynix-project-header-button');
  const view=menu('pynix-project-view-switcher','Project view','general/chevronDown',[
   ['✓ Project',()=>{}]
  ]);
  const viewLabel=document.createElement('span');
  viewLabel.className='pynix-project-view-label';viewLabel.textContent='Project';
  view.querySelector('summary').prepend(viewLabel);
  if(title)title.replaceWith(view);
  const create=menu('pynix-project-create-menu','New File or Directory…','general/add',[
   ['New File…',()=>window.pynixCreateProjectEntry?.('file')],
   ['New Directory…',()=>window.pynixCreateProjectEntry?.('directory')],
  ]);
  const divider=document.createElement('span');
  divider.className='pynix-project-header-separator';
  divider.setAttribute('role','separator');divider.setAttribute('aria-orientation','vertical');
  const locate=quick('Select Opened File','general/locate',()=>{
   window.pynixProjectSelectOpenedFile?.();
  });
  locate.dataset.pynixShortcut='⌥F1, 1';
  const expand=quick('Expand Selected','general/expandAll',()=>{
   window.pynixProjectExpandSelected?.();
  });
  expand.dataset.pynixTooltip='Expand Selected\nPress ⇧⌘+ to expand all nodes';
  const collapseAction=collapse||quick('Collapse All','general/collapseAll',()=>{
   window.pynixProjectCollapseAll?.();
  });
  collapseAction.replaceChildren(makeIcon('general/collapseAll')||
   document.createTextNode('Collapse'));
  collapseAction.title='Collapse All';
  collapseAction.setAttribute('aria-label','Collapse All');
  const more=menu('pynix-project-more-menu','Options','general/moreVertical',[
   ['Select Opened File',()=>window.pynixProjectSelectOpenedFile?.()],
   ['Expand All',()=>window.pynixProjectExpandSelected?.(true)],
   ['Collapse All',()=>window.pynixProjectCollapseAll?.()],
  ]);
  const hide=quick('Hide','general/hide',()=>{
   document.querySelectorAll('.workspace-mode .rail>.rail-item')[0]?.click();
  });
  hide.dataset.pynixShortcut='⇧⎋';
  actions.replaceChildren(create,divider,locate,expand,collapseAction,more,hide);
 };
 let selectFileChordUntil=0;
 document.addEventListener('keydown',event=>{
  if(event.altKey&&!event.metaKey&&!event.ctrlKey&&event.key==='F1'){
   selectFileChordUntil=performance.now()+1300;event.preventDefault();return;
  }
  if(event.key==='1'&&!event.metaKey&&!event.altKey&&!event.ctrlKey&&
     performance.now()<selectFileChordUntil){
   selectFileChordUntil=0;event.preventDefault();
   window.pynixProjectSelectOpenedFile?.();return;
  }
  if(event.metaKey&&!event.altKey&&!event.ctrlKey){
   if(event.shiftKey&&(event.key==='+'||event.key==='=')){
    event.preventDefault();window.pynixProjectExpandSelected?.(true);return;
   }
   if(!event.shiftKey&&event.key==='-'){
    event.preventDefault();window.pynixProjectCollapseAll?.();return;
   }
  }
  if(event.shiftKey&&event.key==='Escape'){
   const pane=document.querySelector('.workspace-mode .tree');
   if(pane&&!pane.hidden&&pane.contains(document.activeElement)){
    event.preventDefault();
    document.querySelectorAll('.workspace-mode .rail>.rail-item')[0]?.click();
   }
  }
 });
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
  if(tabs)new MutationObserver(()=>{
   updateBreadcrumb();
   updateRunActionTooltips();
  }).observe(tabs,{
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
            # Project toolbar glyphs are visible in both default and opt-in
            # icon modes, alongside the existing Run/Debug/search controls.
            keys = ("general/chevronDown", "toolwindows/vcs",
                    "general/moreVertical", "general/edit", "run/run",
                    "run/debug", "general/search", "general/settings",
                    "general/add", "general/locate", "general/expandAll",
                    "general/collapseAll", "general/hide")
            data = {key: catalog.svg(key,dark=dark,
                                     tool_window=key=="toolwindows/vcs")
                    for key in keys}
    except (OSError,ValueError,KeyError,json.JSONDecodeError):
        return document
    payload = json.dumps(data,ensure_ascii=True).replace("<","\\u003c")
    script = CHROME_SCRIPT.replace("__CHROME_ICONS__",payload).replace(
        "__ICONLESS__", "true" if iconless else "false"
    )
    script = script.replace("__IDE_VERSION__", IDE_BETA_VERSION)
    return document.replace("</body>",CHROME_STYLE+script+"</body>",1)

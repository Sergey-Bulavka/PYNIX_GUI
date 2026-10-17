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
 color:#d0d2d7!important;font-size:12px!important;font-weight:600!important
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
  toolbar.append(center,right);
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

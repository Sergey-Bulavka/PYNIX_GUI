"""The active native V4 dock behaves like one real PyCharm tool window."""

from pathlib import Path
import shutil
import subprocess

import pytest

from pynix_gui.ide_terminal_dock import TERMINAL_DOCK_JS
from pynix_gui.ide_pycharm_chrome import CHROME_STYLE, apply_pycharm_chrome
from pynix_gui.ide_edge_profile import EXISTING_ACTIONS
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession


def test_same_sidebar_button_opens_and_closes_real_terminal_dock():
    for expected in (
        "const railTerminal=document.querySelectorAll('.workspace-mode .rail>.rail-item')[4];",
        "railTerminal?.addEventListener('click',()=>{",
        "if(visible()&&selectedTool==='TERMINAL')setToolWindowVisible(false);",
        "else choose('TERMINAL');",
        "railTerminal?.classList.toggle('active',open&&selected);",
        "railTerminal?.setAttribute('aria-pressed',String(open&&selected));",
        "toolTabs.addEventListener('click',sync);",
        "window.pynixTerminalDock={sync,show:()=>choose('TERMINAL')",
        "setToolWindowVisible(false);",
    ):
        assert expected in TERMINAL_DOCK_JS,expected
    assert EXISTING_ACTIONS["Terminal"] == "rail:4"
    assert EXISTING_ACTIONS["PYNIX Terminal"] == "rail:4"


def test_pycharm_dock_header_is_the_only_visible_tool_navigation():
    assert "title.textContent='Terminal'" in TERMINAL_DOCK_JS
    assert "local.textContent='Local'" in TERMINAL_DOCK_JS
    assert "session.append(local,closeSession)" in TERMINAL_DOCK_JS
    assert "header.insertBefore" not in TERMINAL_DOCK_JS
    assert "terminal.insertBefore(header,debugPanelBar.nextSibling)" in TERMINAL_DOCK_JS
    assert "const views=[['Terminal','TERMINAL'],['Problems','PROBLEMS']" in TERMINAL_DOCK_JS
    assert "['Output','OUTPUT'],['Debug Console','DEBUG CONSOLE']]" in TERMINAL_DOCK_JS
    for expected in (
        ".workspace-mode .integrated-terminal .terminal-tabs,",
        ".workspace-mode .integrated-terminal .pynix-terminal-session{",
        "display:none!important",
        ".pynix-terminal-dock-bar",
        ".pynix-terminal-dock-session",
        ".pynix-terminal-dock-popup",
        ".pynix-terminal-dock-action:hover:not(:disabled)",
        ".integrated-terminal .terminal-console",
    ):
        assert expected in CHROME_STYLE,expected
    # Existing tool tabs remain in the DOM, preserving run/debug routing.
    assert "toolTabs.querySelectorAll('strong,span')" in TERMINAL_DOCK_JS
    assert "tab?.click();" in TERMINAL_DOCK_JS


def test_decorative_unimplemented_services_cannot_claim_working_actions():
    assert "add.disabled=true" in TERMINAL_DOCK_JS
    assert "agents.disabled=true" in TERMINAL_DOCK_JS
    assert "Multiple terminal sessions not implemented" in TERMINAL_DOCK_JS
    assert "AI Agents are not yet available" in TERMINAL_DOCK_JS


def test_hiding_dock_removes_its_height_and_resizer_in_css_flex_layout():
    final=CHROME_STYLE.split("/* Native V4 PyCharm terminal tool-window:",1)[1]
    for declaration in (
        "height:auto!important;min-height:0!important;flex:1 1 0%!important;",
        ".integrated-terminal.pynix-tool-window-collapsed{",
        "display:none!important;height:0!important;min-height:0!important;",
        "margin:0!important;flex:0 0 0px!important",
        ".terminal-resizer[hidden]{",
        "display:none!important;height:0!important;min-height:0!important",
        ".integrated-terminal .terminal-console{",
        "flex:1 1 0%!important;min-height:0!important;",
    ):
        assert declaration in final,declaration
    assert "terminal-height" not in final  # user's resized height remains retained
    assert "workspace-main" not in final  # no invented duplicate layout


def test_merged_workspace_installs_real_terminal_controller_once(tmp_path):
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    html=workspace_bootstrap(WorkspaceSession(tmp_path))
    assert "__PYNIX_TERMINAL_DOCK__" not in html
    assert html.count("window.pynixTerminalDock={sync,show:") == 1
    assert "window.pynixTerminalDock?.sync();" in html
    assert "terminal.classList.toggle('pynix-tool-window-collapsed',!visible);" in html
    assert "if(terminalResizer)terminalResizer.hidden=!visible;" in html
    assert "const dockRestore=document.createElement('button');" in html
    assert "dockRestore.hidden=visible;" in html
    assert "setToolWindowVisible(true);" in html # native run/debug results
    assert "tab?.click();" in html
    assert "railTerminal?.addEventListener('click'" in html


def test_native_v4_embed_and_full_chrome_js_syntax(tmp_path):
    node=shutil.which("node")
    if node is None:
        pytest.skip("Node.js not installed")
    (tmp_path/"main.pnx").write_text("function main()\n",encoding="utf-8")
    document=workspace_bootstrap(WorkspaceSession(tmp_path))
    script=document.split("<script>",1)[1].split("</script>",1)[0]
    result=subprocess.run([node,"--check"],input=script,capture_output=True,
                          text=True,encoding="utf-8",timeout=20)
    assert result.returncode==0,result.stderr
    full=apply_pycharm_chrome(
        '<html><head></head><body class="workspace-mode"></body></html>',
        iconless=True,
    )
    assert "Native V4 PyCharm terminal tool-window" in full


def test_terminal_rail_clicks_and_tool_menu_actually_toggle_in_node():
    """A DOM-like Node harness exercises events, not just CSS text matching."""
    node=shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    fixture=r"""
class Fake{
 constructor(name='div'){
  this.name=name;this.children=[];this.events={};this.attrs={};
  this.className='';this.hidden=false;this.disabled=false;this.title='';
  const classes=new Set();
  this.classList={
   toggle:(key,yes)=>{if(yes)classes.add(key);else classes.delete(key);},
   contains:key=>classes.has(key)
  };
 }
 append(...items){this.children.push(...items);}
 appendChild(item){this.children.push(item);return item;}
 insertBefore(item){this.children.push(item);}
 setAttribute(key,value){this.attrs[key]=value;}
 getAttribute(key){return this.attrs[key];}
 addEventListener(name,cb){(this.events[name]??=[]).push(cb);}
 emit(name,event={}){for(const fn of this.events[name]||[])fn(event);}
 click(){this.emit('click',{target:this});}
 querySelectorAll(selector){
  return selector==='strong,span'?this.children:
   selector==='[role="tab"]'?this.children:[];
 }
}
const terminal=new Fake('terminal'),toolTabs=new Fake('tabs');
const debugPanelBar=new Fake('debug');
const railTerminal=new Fake('rail');
const terminalResizer={hidden:false},dockRestore={hidden:true};
let selectedTool='TERMINAL',layoutChanges=[];
let rail=[new Fake(),new Fake(),new Fake(),new Fake(),railTerminal];
const dockMode=['TERMINAL','PROBLEMS','OUTPUT','DEBUG CONSOLE'];
for(const name of dockMode){
 const tab=new Fake('tab');
 tab.textContent=name;tab.attrs.role='tab';
 tab.click=()=>{
  selectedTool=name;
  setToolWindowVisible(true);
  toolTabs.emit('click',{target:tab});
 };
 toolTabs.children.push(tab);
}
const document={
 createElement:name=>new Fake(name),
 querySelectorAll:()=>rail,
 addEventListener:()=>{}
};
const window={};
function setToolWindowVisible(state){
 terminal.classList.toggle('pynix-tool-window-collapsed',!state);
 terminalResizer.hidden=!state;
 dockRestore.hidden=state;
 layoutChanges.push(state);
 window.pynixTerminalDock?.sync();
}
"""
    checks=r"""
const require=(condition,message)=>{if(!condition)throw Error(message);};
require(terminal.classList.contains('pynix-tool-window-collapsed'),'Initial Terminal must be hidden');
require(terminalResizer.hidden,'Initial resizer must be hidden');
railTerminal.click();
require(!terminal.classList.contains('pynix-tool-window-collapsed'),'Click must open Terminal');
require(railTerminal.classList.contains('active'),'Sidebar must activate');
railTerminal.click();
require(terminal.classList.contains('pynix-tool-window-collapsed'),'Second click must hide');
require(!railTerminal.classList.contains('active'),'Sidebar must deactivate');
toolTabs.children[1].click();
require(!terminal.classList.contains('pynix-tool-window-collapsed'),'Problems must reopen dock');
require(selectedTool==='PROBLEMS','Problems selected');
railTerminal.click();
require(selectedTool==='TERMINAL','Sidebar must switch from Problems to Terminal');
require(!terminal.classList.contains('pynix-tool-window-collapsed'),'Terminal remains visible');
window.pynixTerminalDock.hide();
require(terminal.classList.contains('pynix-tool-window-collapsed'),'Hide action must collapse');
window.pynixTerminalDock.show();
require(!terminal.classList.contains('pynix-tool-window-collapsed'),'Show action must reopen');
require(layoutChanges.join(',')==='false,true,false,true,true,false,true',
  'Unexpected dock transitions: '+JSON.stringify(layoutChanges));
console.log('terminal toggle events passed');
"""
    script=fixture+TERMINAL_DOCK_JS+checks
    result=subprocess.run([node,"-e",script],text=True,
                          encoding="utf-8",capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert "terminal toggle events passed" in result.stdout

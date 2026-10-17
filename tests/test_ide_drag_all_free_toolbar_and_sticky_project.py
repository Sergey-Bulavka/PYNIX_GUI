"""Native macOS free-titlebar drag zones and stationary Explorer header."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from examples.ide_native_v4 import TOOLBAR_DRAG_SCRIPT, toolbar_drag_frame
from pynix_gui.ide_pycharm_chrome import CHROME_STYLE, apply_pycharm_chrome


def test_native_hit_zones_reject_controls_and_invalid_geometry():
    assert toolbar_drag_frame(1500,950,{"x":200,"y":10,"width":40,"height":24}) == (
        200,916,40,24
    )
    for area in (
        {"x":50,"y":10,"width":80,"height":24}, # Mac traffic lights
        {"x":200,"y":2,"width":80,"height":24}, # window resize edge
        {"x":200,"y":45,"width":80,"height":24}, # editor/tab content
        {"x":200,"y":10,"width":11,"height":24}, # too small for a native target
        {"x":200,"y":10,"width":80,"height":float("nan")},
    ):
        assert toolbar_drag_frame(1500,950,area) is None


def test_free_titlebar_gap_compilation_never_drags_over_clickable_buttons():
    node=shutil.which("node")
    if node is None:
        pytest.skip("Node.js needed for dynamic DOM geometry test")
    code=TOOLBAR_DRAG_SCRIPT.split("<script>",1)[1].split("</script>",1)[0]
    fixture=r"""
const rectangles=[
 [96,186],     // project switcher
 [194,278],    // git branch
 [475,592],    // run configuration
 [600,629],    // run button
 [637,666],    // debug button
 [674,707],    // actions menu
 [921,952],    // Search Everywhere
 [960,991],    // Settings
 [999,1171]    // beta status
];
let delivered=[];
let events={};
function box(x1,x2){return {left:x1,right:x2,width:x2-x1,top:0,bottom:44,height:44};}
const buttons=rectangles.map((r)=>({getBoundingClientRect:()=>box(...r)}));
const toolbar={
 getBoundingClientRect:()=>({left:0,right:1200,top:0,bottom:44,width:1200,height:44}),
 querySelectorAll:()=>buttons,
 querySelector:(q)=>q==='.pynix-pycharm-center'||q==='.pynix-toolbar-identity'?{}:null
};
global.window={
 webkit:{messageHandlers:{pynixToolbarDragRegion:{postMessage:(areas)=>delivered.push(areas)}}},
 addEventListener:(name,fn)=>{events[name]=fn;}
};
global.document={querySelector:()=>toolbar};
global.ResizeObserver=class{observe(){}};
global.MutationObserver=class{observe(){}};
global.requestAnimationFrame=(fn)=>fn();
"""
    verify=r"""
if(delivered.length===0)throw Error('No drag regions');
const areas=delivered[delivered.length-1];
if(areas.length<3)throw Error('Expected several distinct free gaps');
for(const a of areas){
 if(a.x<86||a.x+a.width>1182||a.y!==10||a.height!==24)
   throw Error('Unsafe drag rectangle '+JSON.stringify(a));
 for(const [l,r] of rectangles){
   if(a.x<r+5&&a.x+a.width>l-5)
     throw Error('Drag rectangle overlaps a button: '+JSON.stringify(a));
 }
}
rectangles[0][1]+=15;
events.resize();
if(delivered.length<2)throw Error('Resize did not refresh drag geometry');
console.log(JSON.stringify({count:areas.length,refreshed:delivered.length}));
"""
    script=fixture+code+verify
    result=subprocess.run([node,"-e",script],text=True,encoding="utf-8",
                          capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr
    parsed=json.loads(result.stdout)
    assert parsed["count"]>=3 and parsed["refreshed"]>=2


def test_uninitialized_toolbar_never_exposes_a_full_width_drag_overlay():
    assert "if(!toolbar.querySelector('.pynix-pycharm-center')||" in TOOLBAR_DRAG_SCRIPT
    assert "pynixToolbarDragRegion?.postMessage([])" in TOOLBAR_DRAG_SCRIPT
    assert "mutation.observe(toolbar,{childList:true,subtree:true})" in TOOLBAR_DRAG_SCRIPT
    assert "window.addEventListener('load',update,{once:true})" in TOOLBAR_DRAG_SCRIPT
    native=(Path(__file__).resolve().parents[1]/
            "examples/ide_native_v4.py").read_text("utf-8")
    assert "for _ in range(20):" in native
    assert "content_view.addSubview_(drag_view)" in native
    assert "drag_view.setHidden_(True)" in native
    assert "drag_view.setHidden_(False)" in native
    assert 'drag_geometry["areas"] = payload[:20] if isinstance(payload, list) else []' in native
    assert "title_drag_area = ToolbarDragView.alloc()" not in native


def test_project_header_sticky_aligns_with_editor_tabs_in_both_icon_modes():
    anchor="/* The Explorer header and editor tab strip belong to the same 43px row."
    assert anchor in CHROME_STYLE
    css=CHROME_STYLE[CHROME_STYLE.index(anchor):]
    for rule in ("position:sticky!important;top:0!important",
                 "z-index:35!important;height:43px!important;min-height:43px!important",
                 "max-height:43px!important;margin:0!important",
                 "scroll-padding-top:43px!important",
                 ".workspace-mode .editor-tabs{",
                 "height:43px!important;min-height:43px!important;max-height:43px!important"):
        assert rule in css
    sample='<html><body class="workspace-mode"></body></html>'
    for iconless in (True,False):
        page=apply_pycharm_chrome(sample,iconless=iconless)
        assert anchor in page
        assert "position:sticky!important;top:0!important" in page

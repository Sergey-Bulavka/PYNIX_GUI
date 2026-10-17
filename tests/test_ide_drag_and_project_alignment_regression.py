"""Regression for disappearing macOS dragging and misaligned Project header."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from examples.ide_native_v4 import normalize_toolbar_drag_areas, toolbar_drag_frame
from pynix_gui.ide_project_header_sync import (
    PROJECT_HEADER_SYNC_SCRIPT, PROJECT_HEADER_SYNC_STYLE,
    apply_project_header_alignment,
)


class SimulatedObjCNSArray:
    """Matches WebKit NSArray's iterable bridge, but is NOT a Python list."""
    def __init__(self, items):
        self.items = items

    def __iter__(self):
        return iter(self.items)


def test_webkit_nsarray_is_not_silently_rejected_as_non_list():
    rectangles=SimulatedObjCNSArray([
        {"x":330, "y":10, "width":40, "height":24},
        {"x":700, "y":10, "width":55, "height":24},
    ])
    assert not isinstance(rectangles,list)
    converted=normalize_toolbar_drag_areas(rectangles)
    assert len(converted)==2
    assert toolbar_drag_frame(1200,800,converted[0]) == (330,766,40,24)
    assert toolbar_drag_frame(1200,800,converted[1]) == (700,766,55,24)


def test_malformed_drag_bridge_messages_fail_closed():
    for bad in (None, "str", b"binary", 12, {"x":300}):
        assert normalize_toolbar_drag_areas(bad)==[]
    # Never allow a page to install an unbounded pool of native overlays.
    batch=SimulatedObjCNSArray(
        [{"x":220+i*12, "y":10, "width":12, "height":24}
         for i in range(100)]
    )
    assert len(normalize_toolbar_drag_areas(batch))==20
    assert normalize_toolbar_drag_areas([[1,2], "unsafe", {"x":99}]) == [
        [1,2], {"x":99}
    ]  # every payload is still validated by toolbar_drag_frame


def test_appkit_handler_uses_bridge_normalizer():
    native=(Path(__file__).resolve().parents[1]/
            "examples/ide_native_v4.py").read_text("utf-8")
    assert 'drag_geometry["areas"] = normalize_toolbar_drag_areas(payload)' in native
    handler=native.split("class ToolbarDragRegionHandler",1)[1].split("toolbar_drag_handler =",1)[0]
    assert "isinstance(payload, list)" not in handler
    assert "for index, drag_view in enumerate(toolbar_drag_areas):" in native
    assert "frame = toolbar_drag_frame(bounds.width, bounds.height, area)" in native


def test_project_header_style_is_dynamic_and_idempotent():
    html="<html><body><div class='workspace-mode'></div></body></html>"
    output=apply_project_header_alignment(html)
    assert output.count('id="pynix-project-header-measure"')==1
    assert output.count('id="pynix-project-header-alignment"')==1
    assert apply_project_header_alignment(output)==output
    assert apply_project_header_alignment("no body")== "no body"
    for required in (
        "position:sticky!important;top:0!important",
        "height:var(--pynix-project-header-height,43px)!important",
        "min-height:var(--pynix-project-header-height,43px)!important",
        "max-height:var(--pynix-project-header-height,43px)!important",
        "scroll-padding-top:var(--pynix-project-header-height,43px)!important",
        "right.bottom-left.top",
        "observer.observe(tree);",
        "observer.observe(tabs);",
    ):
        assert required in PROJECT_HEADER_SYNC_STYLE+PROJECT_HEADER_SYNC_SCRIPT


def test_project_header_tracks_measured_editor_tabs_bottom():
    node=shutil.which("node")
    if node is None:
        pytest.skip("Node.js needed for visual geometry math")
    script=PROJECT_HEADER_SYNC_SCRIPT.split("<script",1)[1].split(">",1)[1].split("</script>",1)[0]
    fixture=r"""
const assigned=[];
let callback;
const left={top:14,height:750};
const right={top:14,bottom:99,height:85};
const tree={
 getBoundingClientRect:()=>left,
 style:{setProperty:(key,value)=>assigned.push([key,value])}
};
const tabs={getBoundingClientRect:()=>right};
global.document={
 querySelector:(s)=>s==='.workspace-mode .tree'?tree:
                   s==='.workspace-mode .editor-tabs'?tabs:null
};
global.window={addEventListener:()=>{}};
global.ResizeObserver=class{
 constructor(fn){callback=fn;}
 observe(){}
};
global.requestAnimationFrame=(fn)=>fn();
"""
    verification=r"""
if(assigned[0][0]!=='--pynix-project-header-height'||assigned[0][1]!=='85px')
 throw Error('Unexpected alignment '+JSON.stringify(assigned));
right.bottom=115;right.height=101;
callback();
if(assigned[1][1]!=='101px')
 throw Error('Resize did not align the bottom edge '+JSON.stringify(assigned));
callback();
if(assigned.length!==2)
 throw Error('Redundant measurements caused a layout loop');
console.log(JSON.stringify(assigned));
"""
    result=subprocess.run([node,"-e",fixture+script+verification],
                          text=True,encoding="utf-8",capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert len(json.loads(result.stdout))==2


def test_actual_v4_installs_dynamic_alignment_after_theme():
    native=(Path(__file__).resolve().parents[1]/
            "examples/ide_native_v4.py").read_text("utf-8")
    assert "document = apply_project_header_alignment(document)" in native
    assert native.index("document = apply_project_header_alignment(document)") > native.index(
        "document = apply_editor_darcula(document)"
    )


def test_real_foundation_nsarray_bridge_on_macos_when_pyobjc_is_available():
    import sys
    if sys.platform != "darwin":
        pytest.skip("Objective-C Foundation is macOS-only")
    try:
        from Foundation import NSArray
    except ImportError:
        pytest.skip("PyObjC Foundation not installed in runner")
    body = NSArray.arrayWithArray_([
        {"x": 333, "y": 10, "width": 45, "height": 24}
    ])
    rects = normalize_toolbar_drag_areas(body)
    assert len(rects) == 1
    assert toolbar_drag_frame(1300, 900, rects[0]) == (333, 866, 45, 24)

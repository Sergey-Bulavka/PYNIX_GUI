# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
import ast
from pathlib import Path
import pytest

from pynix_gui.ide_icons_v4 import ICON_NAMES, PALETTE, paint_asset

def test_v4_categories_complete():
    assert {"folder","folder-open","file","pnx","test","toml",
            "explorer","search","git","branch","commit","sync",
            "run","debug","terminal","settings","problems","output"} <= set(ICON_NAMES)

def test_v4_gallery_parses_and_covers_five_sizes():
    source=Path("examples/ide_icon_gallery.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "(14,16,18,20,24)" in source
    assert "applicationShouldTerminateAfterLastWindowClosed_" in source

def test_v4_palette_valid_hex_colors():
    for value in PALETTE.values():
        assert len(value)==7 and value.startswith("#")
        int(value[1:],16)

def test_v4_unknown_name_rejected():
    with pytest.raises(ValueError,match="Unknown V4 icon"):
        paint_asset(None,0,0,"invalid")


class _Path:
    def moveToPoint_(self,p): pass
    def lineToPoint_(self,p): pass
    def closePath(self): pass
    def fill(self): pass

class _Bezier:
    @staticmethod
    def bezierPath(): return _Path()

class _Color:
    def setFill(self): pass

class _NSColor:
    @staticmethod
    def colorWithCalibratedRed_green_blue_alpha_(*args): return _Color()

class _AppKit:
    NSBezierPath=_Bezier
    NSColor=_NSColor
    NSMakePoint=staticmethod(lambda x,y: (x,y))

@pytest.mark.parametrize("name",["folder","folder-open","file","pnx","test","toml"])
def test_v4_filled_assets_render_without_native_appkit(name):
    paint_asset(_AppKit,10,20,name,size=16)

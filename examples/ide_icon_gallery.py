# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Native macOS V4 icon gallery. Review shapes before IDE integration."""
import sys
from pynix_gui.ide_icons_v4 import ICON_NAMES, paint_asset

def main():
    if sys.platform != "darwin":
        raise SystemExit("Icon gallery requires macOS")
    import AppKit
    import objc
    from Foundation import NSObject
    class Delegate(NSObject):
        def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
            return True
    class Gallery(AppKit.NSView):
        def isFlipped(self):
            return True
        def drawRect_(self, rect):
            bg=AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.08,0.1,0.14,1)
            bg.setFill()
            AppKit.NSBezierPath.fillRect_(self.bounds())
            font=AppKit.NSFont.systemFontOfSize_(12)
            bright=AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.88,0.91,0.96,1)
            caption={AppKit.NSFontAttributeName:font,AppKit.NSForegroundColorAttributeName:bright}
            for i,name in enumerate(ICON_NAMES):
                y=44+i*30
                AppKit.NSString.stringWithString_(name).drawAtPoint_withAttributes_(
                    AppKit.NSMakePoint(22,y),caption)
                for j,size in enumerate((14,16,18,20,24)):
                    paint_asset(AppKit,200+j*100,y,name,size=size)
            for j,size in enumerate((14,16,18,20,24)):
                AppKit.NSString.stringWithString_(str(size)+" px").drawAtPoint_withAttributes_(
                    AppKit.NSMakePoint(200+j*100,12),caption)
    app=AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
    delegate=Delegate.alloc().init()
    app.setDelegate_(delegate)
    window=AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        AppKit.NSMakeRect(100,100,760,680),
        AppKit.NSWindowStyleMaskTitled|AppKit.NSWindowStyleMaskClosable|
        AppKit.NSWindowStyleMaskResizable, AppKit.NSBackingStoreBuffered,False)
    window.setTitle_("PYNIX IDE — Icon Gallery V4")
    view=Gallery.alloc().initWithFrame_(window.contentView().bounds())
    view.setAutoresizingMask_(AppKit.NSViewWidthSizable|AppKit.NSViewHeightSizable)
    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)
    app.activateIgnoringOtherApps_(True)
    app.run()

if __name__=="__main__":
    main()

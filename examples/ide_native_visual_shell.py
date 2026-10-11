# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
"""PYNIX IDE native *visual-only* shell for macOS.

Run: python -m examples.ide_native_visual_shell

This is the pixel-level appearance acceptance prototype. It does not simulate
filesystem, compiler or editor behavior; the GUI toolkit integration follows
only after visual acceptance. Requires PyObjC/AppKit.
"""
from __future__ import annotations

import sys

from pynix_gui.ide_iconography import draw_icon


PALETTE = {
    "canvas": "#10151E",
    "title": "#171D28",
    "toolbar": "#1A2330",
    "rail": "#171F2B",
    "sidebar": "#1C2634",
    "editor": "#151C28",
    "editor_header": "#202B39",
    "terminal": "#202B39",
    "status": "#253A52",
    "border": "#384453",
    "text": "#E3EBF5",
    "subtle": "#ACB8C7",
    "faint": "#8393A8",
    "accent": "#70B7FF",
    "selected": "#314A63",
    "green": "#95D8AD",
    "yellow": "#F0CC86",
    "purple": "#C6A4FA",
    "red": "#EC8D9B",
}
PROJECT_TREE = (
    (0, "PYNIX", "folder", False),
    (1, "src", "folder", False),
    (2, "main.pnx", "file", True),
    (2, "gui.pnx", "file", False),
    (2, "tooling.pnx", "file", False),
    (1, "tests", "folder", False),
    (2, "test_main.pnx", "file", False),
    (1, "assets", "folder", False),
    (1, "pynix.toml", "file", False),
)
SAMPLE_LINES = (
    (("keyword", "function"), ("text", " main"), ("subtle", "()")),
    (),
    (("text", "    message"), ("subtle", " = "), ("green", '"Hello PYNIX"')),
    (("text", "    count"), ("subtle", " = "), ("yellow", "3")),
    (),
    (("keyword", "    for"), ("text", " item "), ("keyword", "in"), ("text", " 1..count")),
    (("keyword", "        print"), ("subtle", "("), ("text", "message"), ("subtle", ")")),
    (),
    (("keyword", "    return"), ("text", " true")),
)
SYNTAX = {"keyword": "purple", "text": "text", "subtle": "subtle", "green": "green", "yellow": "yellow"}


def _rgb(appkit, code):
    v = PALETTE.get(code, code).lstrip("#")
    return appkit.NSColor.colorWithCalibratedRed_green_blue_alpha_(
        int(v[0:2], 16) / 255.0, int(v[2:4], 16) / 255.0,
        int(v[4:6], 16) / 255.0, 1.0,
    )


def native_shell_class(appkit):
    import objc

    class PynixIDEShell(appkit.NSView):
        def isFlipped(self):
            return True

        @objc.python_method
        def _fill(self, x, y, w, h, color, radius=0):
            if w <= 0 or h <= 0:
                return
            _rgb(appkit, color).setFill()
            rect = appkit.NSMakeRect(x, y, w, h)
            path = (appkit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                rect, radius, radius) if radius else
                appkit.NSBezierPath.bezierPathWithRect_(rect))
            path.fill()

        @objc.python_method
        def _rule(self, x, y, w, h=1):
            self._fill(x, y, w, h, "border")

        @objc.python_method
        def _label(self, x, y, value, *, size=12, color="text",
                   weight="regular", mono=False):
            font = (appkit.NSFont.monospacedSystemFontOfSize_weight_(size, appkit.NSFontWeightRegular) if mono else (appkit.NSFont.boldSystemFontOfSize_(size) if weight == "bold" else appkit.NSFont.systemFontOfSize_(size)))
            attrs = {appkit.NSFontAttributeName: font,
                     appkit.NSForegroundColorAttributeName: _rgb(appkit, color)}
            appkit.NSString.stringWithString_(value).drawAtPoint_withAttributes_(
                appkit.NSMakePoint(x, y), attrs)
            return appkit.NSString.stringWithString_(value).sizeWithAttributes_(attrs).width

        @objc.python_method
        def _icon(self, x, y, kind, color="subtle"):
            name = {"file": "pnx"}.get(kind, kind)
            draw_icon(appkit, x, y, name, _rgb(appkit, color), size=18)

        @objc.python_method
        def _chip(self, x, y, width, label, active=False):
            self._fill(x, y, width, 29, "selected" if active else "editor_header", 6)
            self._label(x+12, y+6, label, size=12,
                        color="text" if active else "subtle", weight="bold" if active else "regular")

        def drawRect_(self, dirty):
            w, h = self.bounds().size
            w, h = float(w), float(h)
            context = appkit.NSGraphicsContext.currentContext()
            if context is not None:
                context.setShouldAntialias_(True)
            self._fill(0, 0, w, h, "canvas")
            title_h, toolbar_h, status_h = 47, 43, 27
            body_top, body_bottom = title_h+toolbar_h, h-status_h
            rail_w = 49
            sidebar_w = min(270, max(208, w*0.19))
            content_x = rail_w + sidebar_w
            content_w = max(100, w-content_x)
            bottom_h = min(200, max(153, (h-body_top-status_h)*0.245))
            terminal_y = body_bottom-bottom_h
            tabs_h, crumb_h = 39, 28

            # Integrated window chrome and primary toolbar
            self._fill(0, 0, w, title_h, "title")
            self._label(24, 13, "PYNIX", size=16, color="text", weight="bold")
            self._label(89, 15, "IDE", size=12, color="accent", weight="bold")
            self._label(max(220, w*0.46), 16, "PYNIX  /  src  /  main.pnx",
                        size=12, color="subtle")
            self._rule(0, title_h-1, w)
            self._fill(0, title_h, w, toolbar_h, "toolbar")
            for i, name in enumerate(("File", "Edit", "View", "Navigate", "Code", "Run", "Tools", "Help")):
                self._label(20 + (0 if i==0 else sum([44,47,52,79,57,42,52,47][:i])),
                            title_h+13, name, color="subtle", size=12)
            self._fill(w-156, title_h+6, 118, 30, "selected", 6)
            self._icon(w-143, title_h+12, "run", "accent")
            self._label(w-120, title_h+12, "Run main.pnx", size=12, weight="bold")
            self._rule(0, body_top-1, w)

            # Left activity rail with actual vector icons
            self._fill(0, body_top, rail_w, body_bottom-body_top, "rail")
            self._rule(rail_w-1, body_top, 1, body_bottom-body_top)
            self._fill(3, body_top+18, 3, 38, "accent", 1)
            self._fill(8, body_top+18, 33, 38, "#2A4056", 6)
            for i, icon_name in enumerate(("explorer", "search", "run", "terminal", "settings")):
                self._icon(17, body_top+29+i*54, icon_name,
                           "accent" if i == 0 else "subtle")

            # Explorer pane
            self._fill(rail_w, body_top, sidebar_w, body_bottom-body_top, "sidebar")
            self._rule(content_x-1, body_top, 1, body_bottom-body_top)
            self._label(rail_w+16, body_top+18, "EXPLORER", size=11, color="subtle", weight="bold")
            self._icon(content_x-35, body_top+16, "more", "faint")
            self._rule(rail_w+12, body_top+48, sidebar_w-24)
            ty=body_top+62
            for index, (depth,name,kind,selected) in enumerate(PROJECT_TREE):
                yy=ty + index*27
                xx=rail_w+17+depth*17
                if selected:
                    self._fill(rail_w+7, yy-3, sidebar_w-14, 25, "#304A64", 5)
                if kind=="folder":
                    self._icon(xx-2, yy-1, "chevron-right" if name=="assets" else "chevron-down", "faint")
                    xx += 13
                self._icon(xx, yy+1, ("folder-open" if name in ("PYNIX", "src", "tests") else "folder") if kind == "folder" else ("pnx" if name.endswith(".pnx") else "file"), "accent" if selected else "subtle")
                self._label(xx+21, yy+1, name, size=12,
                            color="text" if selected else "subtle",
                            weight="bold" if selected else "regular")
            self._rule(rail_w+12, body_bottom-92, sidebar_w-24)
            self._label(rail_w+16, body_bottom-76, "OUTLINE", color="subtle", size=11, weight="bold")
            self._label(rail_w+22, body_bottom-48, "ƒ   main()", color="text", size=12)
            self._label(rail_w+43, body_bottom-28, "message  :  String", color="faint", size=11)

            # Main editor with flush, integrated tabs
            self._fill(content_x, body_top, content_w, terminal_y-body_top, "editor")
            self._fill(content_x, body_top, content_w, tabs_h, "editor_header")
            self._fill(content_x, body_top, 158, tabs_h, "editor")
            self._fill(content_x, body_top, 158, 2, "accent")
            self._rule(content_x+158, body_top+7, 1, tabs_h-14)
            self._icon(content_x+15, body_top+11, "file", "accent")
            self._label(content_x+37, body_top+12, "main.pnx", size=12, weight="bold")
            self._icon(content_x+133, body_top+11, "close", "subtle")
            self._icon(content_x+177, body_top+11, "file", "faint")
            self._label(content_x+199, body_top+12, "gui.pnx", size=12, color="faint")
            self._rule(content_x, body_top+tabs_h, content_w)
            self._fill(content_x, body_top+tabs_h, content_w, crumb_h, "editor")
            self._label(content_x+22, body_top+tabs_h+7,
                        "PYNIX  ›  src  ›  main.pnx", size=11, color="subtle")
            self._rule(content_x, body_top+tabs_h+crumb_h, content_w)
            code_top=body_top+tabs_h+crumb_h+15
            self._fill(content_x, code_top-15, 59, terminal_y-code_top+15, "canvas")
            self._rule(content_x+59, code_top-15, 1, terminal_y-code_top+15)
            self._fill(content_x+60, code_top+37, content_w-60, 23, "#1B2837")
            font_size=13
            for i,parts in enumerate(SAMPLE_LINES):
                y=code_top + i*23
                self._label(content_x+30, y+2, str(i+1), color="faint", size=11, mono=True)
                px=content_x+76
                for role,fragment in parts:
                    dx=self._label(px, y+1, fragment, size=font_size,
                                   color=SYNTAX[role], mono=True)
                    px+=dx
            self._fill(content_x+76, code_top+9*23+9, 1, 17, "accent")
            self._label(content_x+76, code_top+10*23+4,
                        "// Ready to build something great.", mono=True, color="faint", size=12)

            # Docked tool window; no large decorative empty cards.
            self._fill(content_x, terminal_y, content_w, bottom_h, "terminal")
            self._rule(content_x, terminal_y, content_w)
            tab_names=("PROBLEMS", "OUTPUT", "TERMINAL", "DEBUG CONSOLE")
            cx=content_x+19
            for name in tab_names:
                active=name=="TERMINAL"
                self._label(cx, terminal_y+13, name, size=11,
                            color="text" if active else "subtle",
                            weight="bold" if active else "regular")
                if active:
                    self._fill(cx, terminal_y+36, len(name)*6.3, 2, "accent")
                cx+=len(name)*8+36
            self._rule(content_x, terminal_y+39, content_w)
            self._label(content_x+22, terminal_y+63, "pynix $", mono=True, color="green", size=12)
            self._label(content_x+92, terminal_y+63,
                        "Project ready. No build is running.", mono=True, color="subtle", size=12)
            self._label(content_x+22, terminal_y+91, "›", color="accent", size=15, mono=True)

            # Always-visible status strip
            self._fill(0, body_bottom, w, status_h, "status")
            self._label(17, body_bottom+7, "●  Ready", color="green", size=11)
            self._label(135, body_bottom+7, "main.pnx", size=11)
            self._label(max(w-365, 310), body_bottom+7,
                        "Ln 11, Col 1    UTF-8    Spaces: 4    PYNIX",
                        color="subtle", size=11)

    return PynixIDEShell


def main():
    if sys.platform != "darwin":
        raise SystemExit("Native design preview currently requires macOS/AppKit")
    import AppKit
    import objc
    from Foundation import NSMakeRect, NSObject

    class IDEPreviewDelegate(NSObject):
        def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
            return True

    app = AppKit.NSApplication.sharedApplication()
    delegate = IDEPreviewDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
    style = (AppKit.NSWindowStyleMaskTitled
             | AppKit.NSWindowStyleMaskClosable
             | AppKit.NSWindowStyleMaskMiniaturizable
             | AppKit.NSWindowStyleMaskResizable)
    window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(120, 100, 1440, 900),
        style, AppKit.NSBackingStoreBuffered, False)
    window.setTitle_("PYNIX IDE — Native Visual Design V3")
    window.setMinSize_((1000, 640))
    shell = native_shell_class(AppKit).alloc().initWithFrame_(window.contentView().bounds())
    shell.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
    window.setContentView_(shell)
    window.makeKeyAndOrderFront_(None)
    app.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == "__main__":
    main()

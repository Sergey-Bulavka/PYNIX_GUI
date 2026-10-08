# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""macOS host realization for the PYNIX GUI layout engine."""

import sys
import warnings

from ._macos_host import MacOSHostBackend
from ..core import GUIEvent
from ..design import DARK, LIGHT, RADII, TYPOGRAPHY, button_visual, rgb, surface_color_role
from ..layout import layout


class _PythonGUIEventBridge:
    def __init__(self, backend, window):
        self._backend = backend
        self._window = window

    def windowShouldClose_(self, sender):
        self._backend._queue_close(self._window)
        return False

    def windowDidResize_(self, notification):
        self._backend._relayout(self._window)

    def controlActivated_(self, sender):
        self._backend._queue_control_activation(self._window, sender)

    def controlChanged_(self, sender):
        self._backend._queue_control_change(self._window, sender)

    def controlTextDidChange_(self, notification):
        self._backend._queue_text_change(self._window, notification.object())

    def textDidChange_(self, notification):
        self._backend._queue_text_change(self._window, notification.object())

    def tabPressed_(self, sender):
        self._backend._queue_tab_selection(self._window, sender)


_OBJC_GUI_EVENT_BRIDGE_TYPE = None


def _objc_gui_event_bridge_type():
    global _OBJC_GUI_EVENT_BRIDGE_TYPE

    if _OBJC_GUI_EVENT_BRIDGE_TYPE is not None:
        return _OBJC_GUI_EVENT_BRIDGE_TYPE

    import Foundation

    class PynixGUIEventBridge(Foundation.NSObject):
        def windowShouldClose_(self, sender):
            self._backend._queue_close(self._window)
            return False

        def windowDidResize_(self, notification):
            self._backend._relayout(self._window)

        def controlActivated_(self, sender):
            self._backend._queue_control_activation(self._window, sender)

        def controlChanged_(self, sender):
            self._backend._queue_control_change(self._window, sender)

        def controlTextDidChange_(self, notification):
            self._backend._queue_text_change(self._window, notification.object())

        def textDidChange_(self, notification):
            self._backend._queue_text_change(self._window, notification.object())

        def tabPressed_(self, sender):
            self._backend._queue_tab_selection(self._window, sender)

    _OBJC_GUI_EVENT_BRIDGE_TYPE = PynixGUIEventBridge
    return _OBJC_GUI_EVENT_BRIDGE_TYPE


class MacOSGUIBackend(MacOSHostBackend):
    """Cocoa realization of the platform-independent PYNIX GUI geometry contract."""

    __slots__ = (
        "_gui_views_by_window",
        "_gui_native_roots_by_window",
        "_gui_native_nodes_by_window",
        "_gui_split_views_by_window",
        "_gui_split_positions_by_window",
        "_gui_tab_labels_by_window",
        "_gui_controls_by_window",
        "_gui_control_meta_by_window",
        "_gui_tab_buttons_by_window",
    )

    def __init__(self, *, platform_name=None, appkit=None):
        super().__init__(platform_name=platform_name, appkit=appkit)
        self._gui_views_by_window = {}
        self._gui_native_roots_by_window = {}
        self._gui_native_nodes_by_window = {}
        self._gui_split_views_by_window = {}
        self._gui_split_positions_by_window = {}
        self._gui_tab_labels_by_window = {}
        self._gui_controls_by_window = {}
        self._gui_control_meta_by_window = {}
        self._gui_tab_buttons_by_window = {}

    def _bridge_for_window(self, window):
        bridge = self._bridges_by_window.get(window)
        if bridge is not None:
            return bridge

        if self.platform_name == "darwin" and self._appkit_override is None:
            bridge_type = _objc_gui_event_bridge_type()
            bridge = bridge_type.alloc().init()
            bridge._backend = self
            bridge._window = window
        else:
            bridge = _PythonGUIEventBridge(self, window)

        self._bridges_by_window[window] = bridge
        return bridge

    def render(self, window, view):
        appkit = self._load_appkit()
        if appkit is None:
            raise OSError("Cocoa GUI backend is unavailable.")

        self._capture_split_positions(window)

        bridge = self._bridge_for_window(window)
        if hasattr(window, "setDelegate_"):
            window.setDelegate_(bridge)

        native_nodes = {}
        split_views = {}
        tab_labels = {}
        controls = {}
        control_meta = {}
        tab_buttons = {}
        native_root = self._build_native_tree(
            appkit,
            view,
            native_nodes,
            split_views,
            tab_labels,
            controls,
            control_meta,
            tab_buttons,
            bridge,
            "system",
            path=(),
        )

        self._gui_views_by_window[window] = view
        self._gui_native_roots_by_window[window] = native_root
        self._gui_native_nodes_by_window[window] = native_nodes
        self._gui_split_views_by_window[window] = split_views
        self._gui_tab_labels_by_window[window] = tab_labels
        self._gui_controls_by_window[window] = controls
        self._gui_control_meta_by_window[window] = control_meta
        self._gui_tab_buttons_by_window[window] = tab_buttons

        window.setContentView_(native_root)
        self._relayout(window)
        self._apply_control_state(window, view)
        return None

    def _new_container(self, appkit):
        view = (
            appkit.NSView.alloc()
            .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
        )
        return view

    @staticmethod
    def _resolved_theme(appkit, requested):
        if requested in {"light", "dark"}:
            return requested

        try:
            application = appkit.NSApplication.sharedApplication()
            appearance = application.effectiveAppearance()
            dark_name = getattr(appkit, "NSAppearanceNameDarkAqua", "NSAppearanceNameDarkAqua")
            aqua_name = getattr(appkit, "NSAppearanceNameAqua", "NSAppearanceNameAqua")
            match = appearance.bestMatchFromAppearancesWithNames_(
                [dark_name, aqua_name]
            )
            if str(match) == str(dark_name):
                return "dark"
        except Exception:
            pass

        return "light"

    @classmethod
    def _native_color(cls, appkit, role, theme):
        semantic = surface_color_role(role)

        resolved = cls._resolved_theme(appkit, theme)
        palette = DARK if resolved == "dark" else LIGHT
        value = palette.get(semantic)
        if value is None:
            return None

        red, green, blue = rgb(value)
        return appkit.NSColor.colorWithSRGBRed_green_blue_alpha_(
            red,
            green,
            blue,
            1.0,
        )

    @classmethod
    def _apply_appearance(cls, appkit, native, theme):
        if not hasattr(native, "setAppearance_"):
            return

        resolved = cls._resolved_theme(appkit, theme)
        appearance_name = (
            getattr(appkit, "NSAppearanceNameDarkAqua", "NSAppearanceNameDarkAqua")
            if resolved == "dark"
            else getattr(appkit, "NSAppearanceNameAqua", "NSAppearanceNameAqua")
        )
        try:
            appearance = appkit.NSAppearance.appearanceNamed_(appearance_name)
            native.setAppearance_(appearance)
        except Exception:
            pass

    @staticmethod
    def _font_for_role(appkit, role):
        size, weight = TYPOGRAPHY.get(role, TYPOGRAPHY["body"])
        if weight == "monospace":
            method = getattr(
                appkit.NSFont,
                "monospacedSystemFontOfSize_weight_",
                None,
            )
            if method is not None:
                return method(
                    size,
                    getattr(appkit, "NSFontWeightRegular", 0.0),
                )

        weights = {
            "regular": getattr(appkit, "NSFontWeightRegular", 0.0),
            "medium": getattr(appkit, "NSFontWeightMedium", 0.23),
            "semibold": getattr(appkit, "NSFontWeightSemibold", 0.3),
            "bold": getattr(appkit, "NSFontWeightBold", 0.4),
        }
        method = getattr(appkit.NSFont, "systemFontOfSize_weight_", None)
        if method is not None:
            return method(size, weights.get(weight, weights["regular"]))
        return appkit.NSFont.systemFontOfSize_(size)

    @staticmethod
    def _set_button_title_color(appkit, button, color, font=None):
        if color is None:
            return

        try:
            import Foundation

            attributes = {
                appkit.NSForegroundColorAttributeName: color,
            }
            if font is not None:
                attributes[appkit.NSFontAttributeName] = font

            title = Foundation.NSAttributedString.alloc().initWithString_attributes_(
                str(button.title()),
                attributes,
            )
            button.setAttributedTitle_(title)
            return
        except Exception:
            pass

        try:
            cell = button.cell()
            if hasattr(cell, "setTextColor_"):
                cell.setTextColor_(color)
        except Exception:
            pass

    def _configure_surface(self, appkit, native, view, theme):
        role = view.role
        if view.kind == "separator":
            role = "separator"
        elif view.kind == "theme":
            role = "app"
        elif view.kind == "tabs" and role is None:
            role = "panel"

        if role is None:
            return

        if not hasattr(native, "setWantsLayer_"):
            return

        try:
            native.setWantsLayer_(True)
            layer = native.layer()
        except Exception:
            return

        if layer is None:
            return

        color = self._native_color(appkit, role, theme)
        if color is not None:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    layer.setBackgroundColor_(color.CGColor())
            except Exception:
                pass

        if view.kind in {"panel", "group"}:
            border = self._native_color(appkit, "separator", theme)
            if border is not None:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        layer.setBorderColor_(border.CGColor())
                    layer.setBorderWidth_(1.0)
                except Exception:
                    pass
            try:
                layer.setCornerRadius_(float(RADII["radius2"]))
            except Exception:
                pass

    def _build_native_tree(
        self,
        appkit,
        view,
        native_nodes,
        split_views,
        tab_labels,
        controls,
        control_meta,
        tab_buttons,
        bridge,
        theme,
        *,
        path,
    ):
        if view.kind in {"horizontalSplit", "verticalSplit"}:
            native = (
                appkit.NSSplitView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            native.setVertical_(view.kind == "horizontalSplit")

            first = self._build_native_tree(
                appkit,
                view.children[0],
                native_nodes,
                split_views,
                tab_labels,
                controls,
                control_meta,
                tab_buttons,
                bridge,
                theme,
                path=path + (0,),
            )
            second = self._build_native_tree(
                appkit,
                view.children[1],
                native_nodes,
                split_views,
                tab_labels,
                controls,
                control_meta,
                tab_buttons,
                bridge,
                theme,
                path=path + (1,),
            )
            native.addSubview_(first)
            native.addSubview_(second)

            if view.split_id is not None:
                split_views[view.split_id] = native
        elif view.kind == "text":
            native = appkit.NSTextField.labelWithString_(view.text)
            if hasattr(native, "setFont_"):
                native.setFont_(self._font_for_role(appkit, view.role))
            if hasattr(native, "setTextColor_"):
                native.setTextColor_(
                    self._native_color(appkit, "textPrimary", theme)
                )

        elif view.kind == "button":
            native = appkit.NSButton.buttonWithTitle_target_action_(
                view.text,
                bridge,
                "controlActivated:",
            )
            if hasattr(native, "setFont_"):
                native.setFont_(self._font_for_role(appkit, "label"))

            visual = button_visual(view.role)
            if hasattr(native, "setBordered_"):
                native.setBordered_(visual["bordered"])

            # Secondary intentionally keeps the active PYNIX/native bordered
            # surface. Custom white/raised bezel colors can make AppKit choose
            # an unreadable title color in Light mode.
            if (
                view.role in {"primary", "danger"}
                and visual["surface"] is not None
                and hasattr(native, "setBezelColor_")
            ):
                try:
                    native.setBezelColor_(
                        self._native_color(
                            appkit,
                            visual["surface"],
                            theme,
                        )
                    )
                except Exception:
                    pass

            title_color = self._native_color(
                appkit,
                visual["text"],
                theme,
            )
            self._set_button_title_color(
                appkit,
                native,
                title_color,
                self._font_for_role(appkit, "label"),
            )

            if hasattr(native, "setContentTintColor_"):
                try:
                    native.setContentTintColor_(title_color)
                except Exception:
                    pass

            controls[view.target] = native
            control_meta[native] = ("button", view.target)

        elif view.kind == "textField":
            native = (
                appkit.NSTextField.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            native.setStringValue_(view.value)
            if view.placeholder and hasattr(native, "setPlaceholderString_"):
                native.setPlaceholderString_(view.placeholder)
            if hasattr(native, "setDelegate_"):
                native.setDelegate_(bridge)
            if hasattr(native, "setBackgroundColor_"):
                native.setBackgroundColor_(
                    self._native_color(appkit, "surfaceSunken", theme)
                )
            if hasattr(native, "setTextColor_"):
                native.setTextColor_(
                    self._native_color(appkit, "textPrimary", theme)
                )
            if hasattr(native, "setFont_"):
                native.setFont_(self._font_for_role(appkit, "body"))
            controls[view.target] = native
            control_meta[native] = ("textField", view.target)

        elif view.kind == "textArea":
            native = (
                appkit.NSScrollView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            text_view = (
                appkit.NSTextView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            text_view.setString_(view.value)
            if hasattr(text_view, "setBackgroundColor_"):
                text_view.setBackgroundColor_(
                    self._native_color(appkit, "surfaceSunken", theme)
                )
            if hasattr(text_view, "setTextColor_"):
                text_view.setTextColor_(
                    self._native_color(appkit, "textPrimary", theme)
                )
            if hasattr(text_view, "setFont_"):
                text_view.setFont_(self._font_for_role(appkit, "body"))
            if hasattr(text_view, "setDelegate_"):
                text_view.setDelegate_(bridge)
            native.setDocumentView_(text_view)
            if hasattr(native, "setHasVerticalScroller_"):
                native.setHasVerticalScroller_(True)
            controls[view.target] = text_view
            control_meta[text_view] = ("textArea", view.target)

        elif view.kind in {"checkBox", "radioButton"}:
            native = appkit.NSButton.buttonWithTitle_target_action_(
                view.text,
                bridge,
                "controlChanged:",
            )
            if hasattr(native, "setButtonType_"):
                button_type = (
                    getattr(appkit, "NSButtonTypeRadio", 4)
                    if view.kind == "radioButton"
                    else getattr(appkit, "NSButtonTypeSwitch", 3)
                )
                native.setButtonType_(button_type)
            if hasattr(native, "setState_"):
                native.setState_(
                    getattr(appkit, "NSControlStateValueOn", 1)
                    if view.checked
                    else getattr(appkit, "NSControlStateValueOff", 0)
                )
            if hasattr(native, "setFont_"):
                native.setFont_(self._font_for_role(appkit, "label"))
            if hasattr(native, "setContentTintColor_"):
                try:
                    native.setContentTintColor_(
                        self._native_color(appkit, "accent", theme)
                    )
                except Exception:
                    pass
            controls[view.target] = native
            control_meta[native] = (view.kind, view.target)

        elif view.kind == "comboBox":
            native = (
                appkit.NSPopUpButton.alloc()
                .initWithFrame_pullsDown_(
                    appkit.NSMakeRect(0, 0, 0, 0),
                    False,
                )
            )
            for item in view.items:
                native.addItemWithTitle_(item)
            native.selectItemAtIndex_(view.selected)
            native.setTarget_(bridge)
            native.setAction_("controlChanged:")
            controls[view.target] = native
            control_meta[native] = ("comboBox", view.target)

        elif view.kind == "list":
            native = (
                appkit.NSScrollView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            document = self._new_container(appkit)
            row_height = 30.0
            document.setFrame_(
                appkit.NSMakeRect(
                    0,
                    0,
                    0,
                    max(row_height, row_height * len(view.items)),
                )
            )

            for index, item in enumerate(view.items):
                row = appkit.NSButton.buttonWithTitle_target_action_(
                    item,
                    bridge,
                    "controlChanged:",
                )
                if hasattr(row, "setBordered_"):
                    row.setBordered_(index == view.selected)
                if index == view.selected and hasattr(row, "setBezelColor_"):
                    try:
                        row.setBezelColor_(
                            self._native_color(
                                appkit,
                                "surfaceSelected",
                                theme,
                            )
                        )
                    except Exception:
                        pass
                row_text_role = (
                    "textPrimary"
                    if index != view.selected
                    else "textPrimary"
                )
                row_text_color = self._native_color(
                    appkit,
                    row_text_role,
                    theme,
                )
                self._set_button_title_color(
                    appkit,
                    row,
                    row_text_color,
                    self._font_for_role(appkit, "body"),
                )
                if hasattr(row, "setContentTintColor_"):
                    try:
                        row.setContentTintColor_(row_text_color)
                    except Exception:
                        pass
                if hasattr(row, "setTag_"):
                    row.setTag_(index)
                document.addSubview_(row)
                control_meta[row] = ("listItem", view.target, index)

            if hasattr(native, "setDocumentView_"):
                native.setDocumentView_(document)
            else:
                native.addSubview_(document)
            if hasattr(native, "setHasVerticalScroller_"):
                native.setHasVerticalScroller_(True)
            if hasattr(native, "setAutohidesScrollers_"):
                native.setAutohidesScrollers_(True)

            controls[view.target] = native
            control_meta[native] = ("list", view.target)

        elif view.kind == "slider":
            native = (
                appkit.NSSlider.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            native.setMinValue_(view.minimum_number)
            native.setMaxValue_(view.maximum_number)
            native.setDoubleValue_(view.number)
            if hasattr(native, "setContinuous_"):
                native.setContinuous_(False)
            native.setTarget_(bridge)
            native.setAction_("controlChanged:")
            if hasattr(native, "setContentTintColor_"):
                try:
                    native.setContentTintColor_(
                        self._native_color(appkit, "accent", theme)
                    )
                except Exception:
                    pass
            controls[view.target] = native
            control_meta[native] = ("slider", view.target)

        elif view.kind == "progressBar":
            native = (
                appkit.NSProgressIndicator.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            native.setMinValue_(view.minimum_number)
            native.setMaxValue_(view.maximum_number)
            native.setDoubleValue_(view.number)
            if hasattr(native, "setIndeterminate_"):
                native.setIndeterminate_(False)

            if hasattr(native, "setContentTintColor_"):
                try:
                    native.setContentTintColor_(
                        self._native_color(appkit, "accent", theme)
                    )
                except Exception:
                    pass

        elif view.kind in {"icon", "image"}:
            native = (
                appkit.NSImageView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            image = None
            if view.kind == "icon":
                symbol = getattr(appkit.NSImage, "imageWithSystemSymbolName_accessibilityDescription_", None)
                if symbol is not None:
                    try:
                        image = symbol(view.resource, view.resource)
                    except Exception:
                        image = None
                if image is None and hasattr(appkit.NSImage, "imageNamed_"):
                    image = appkit.NSImage.imageNamed_(view.resource)
            else:
                if hasattr(appkit.NSImage, "imageNamed_"):
                    image = appkit.NSImage.imageNamed_(view.resource)
                if image is None:
                    try:
                        image = appkit.NSImage.alloc().initWithContentsOfFile_(view.resource)
                    except Exception:
                        image = None
            if image is not None:
                native.setImage_(image)
            if view.kind == "icon" and hasattr(native, "setContentTintColor_"):
                try:
                    native.setContentTintColor_(
                        self._native_color(
                            appkit,
                            "textSecondary",
                            theme,
                        )
                    )
                except Exception:
                    pass
            if hasattr(native, "setImageScaling_"):
                native.setImageScaling_(getattr(appkit, "NSImageScaleProportionallyUpOrDown", 3))

        elif view.kind in {"enabled", "focused"}:
            native = self._new_container(appkit)
            child = self._build_native_tree(
                appkit,
                view.children[0],
                native_nodes,
                split_views,
                tab_labels,
                controls,
                control_meta,
                tab_buttons,
                bridge,
                theme,
                path=path + (0,),
            )
            native.addSubview_(child)

        elif view.kind == "theme":
            effective_theme = view.theme
            theme = effective_theme
            native = self._new_container(appkit)
            self._apply_appearance(appkit, native, effective_theme)
            child = self._build_native_tree(
                appkit,
                view.children[0],
                native_nodes,
                split_views,
                tab_labels,
                controls,
                control_meta,
                tab_buttons,
                bridge,
                effective_theme,
                path=path + (0,),
            )
            native.addSubview_(child)

        elif view.kind == "scroll":
            native = (
                appkit.NSScrollView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            child = self._build_native_tree(
                appkit,
                view.children[0],
                native_nodes,
                split_views,
                tab_labels,
                controls,
                control_meta,
                tab_buttons,
                bridge,
                theme,
                path=path + (0,),
            )
            if hasattr(native, "setDocumentView_"):
                native.setDocumentView_(child)
            else:
                native.addSubview_(child)
            if hasattr(native, "setHasVerticalScroller_"):
                native.setHasVerticalScroller_(True)
            if hasattr(native, "setHasHorizontalScroller_"):
                native.setHasHorizontalScroller_(True)
            if hasattr(native, "setAutohidesScrollers_"):
                native.setAutohidesScrollers_(True)
        else:
            native = self._new_container(appkit)
            for index, child in enumerate(view.children):
                native_child = self._build_native_tree(
                    appkit,
                    child,
                    native_nodes,
                    split_views,
                    tab_labels,
                    controls,
                    control_meta,
                    tab_buttons,
                    bridge,
                    theme,
                    path=path + (index,),
                )
                native.addSubview_(native_child)
                if view.kind == "tabs" and hasattr(native_child, "setHidden_"):
                    native_child.setHidden_(index != view.selected)

            if view.kind == "tabs":
                labels = []
                for index, text in enumerate(view.labels):
                    button = appkit.NSButton.buttonWithTitle_target_action_(
                        text,
                        bridge,
                        "tabPressed:",
                    )
                    if hasattr(button, "setBordered_"):
                        button.setBordered_(index == view.selected)
                    if index == view.selected and hasattr(button, "setBezelColor_"):
                        try:
                            button.setBezelColor_(
                                self._native_color(
                                    appkit,
                                    "surfaceSelected",
                                    theme,
                                )
                            )
                        except Exception:
                            pass
                    tab_text_color = self._native_color(
                        appkit,
                        "textPrimary",
                        theme,
                    )
                    self._set_button_title_color(
                        appkit,
                        button,
                        tab_text_color,
                        self._font_for_role(appkit, "label"),
                    )
                    if hasattr(button, "setContentTintColor_"):
                        try:
                            button.setContentTintColor_(tab_text_color)
                        except Exception:
                            pass
                    native.addSubview_(button)
                    labels.append(button)
                    tab_buttons[button] = (view.container_id, index)
                tab_labels[path] = tuple(labels)

        self._apply_appearance(appkit, native, theme)
        self._configure_surface(appkit, native, view, theme)
        native_nodes[path] = native

        if hasattr(native, "setAutoresizingMask_"):
            native.setAutoresizingMask_(0)

        return native

    def _control_meta(self, window, sender):
        return self._gui_control_meta_by_window.get(window, {}).get(sender)

    def _queue_control_activation(self, window, sender):
        meta = self._control_meta(window, sender)
        if meta is None:
            return
        _, target = meta
        self._event_queue(window).append(GUIEvent("ACTIVATE", target=target))

    def _queue_control_change(self, window, sender):
        meta = self._control_meta(window, sender)
        if meta is None:
            return
        kind, target = meta[:2]

        if kind == "checkBox":
            state = bool(sender.state())
            event = GUIEvent("CHANGE", target=target, checked=state)
        elif kind == "radioButton":
            event = GUIEvent("SELECTION", target=target, index=0)
        elif kind == "comboBox":
            event = GUIEvent(
                "SELECTION",
                target=target,
                index=int(sender.indexOfSelectedItem()),
            )
        elif kind == "listItem":
            event = GUIEvent(
                "SELECTION",
                target=target,
                index=int(meta[2]),
            )
        elif kind == "slider":
            event = GUIEvent(
                "CHANGE",
                target=target,
                number=float(sender.doubleValue()),
            )
        else:
            return

        self._event_queue(window).append(event)

    def _queue_text_change(self, window, sender):
        meta = self._control_meta(window, sender)
        if meta is None:
            return
        kind, target = meta
        if kind == "textField":
            value = str(sender.stringValue())
        elif kind == "textArea":
            value = str(sender.string()).replace("\r\n", "\n").replace("\r", "\n")
        else:
            return
        self._event_queue(window).append(
            GUIEvent("CHANGE", target=target, text=value)
        )

    def _queue_tab_selection(self, window, sender):
        meta = self._gui_tab_buttons_by_window.get(window, {}).get(sender)
        if meta is None:
            return
        target, index = meta
        self._event_queue(window).append(
            GUIEvent("SELECTION", target=target, index=index)
        )

    @staticmethod
    def _set_enabled_recursive(native, enabled):
        if hasattr(native, "setEnabled_"):
            try:
                native.setEnabled_(enabled)
            except Exception:
                pass
        if hasattr(native, "subviews"):
            try:
                children = native.subviews()
            except TypeError:
                children = native.subviews
            except Exception:
                children = ()
            for child in children or ():
                MacOSGUIBackend._set_enabled_recursive(child, enabled)

    def _apply_control_state(self, window, view):
        controls = self._gui_controls_by_window.get(window, {})

        def targets(node):
            result = []
            if node.target is not None and node.target in controls:
                result.append(node.target)
            for child in node.children:
                result.extend(targets(child))
            return result

        def visit(node, inherited_enabled=True):
            current_enabled = inherited_enabled
            if node.kind == "enabled":
                current_enabled = inherited_enabled and node.enabled
                native = self._gui_native_nodes_by_window[window].get(path_map.get(id(node), ()))
                if native is not None:
                    self._set_enabled_recursive(native, current_enabled)

            if node.kind == "focused" and node.focused:
                nested = targets(node.children[0])
                if len(nested) == 1:
                    control = controls[nested[0]]
                    try:
                        window.makeFirstResponder_(control)
                    except Exception:
                        pass

            for child in node.children:
                visit(child, current_enabled)

        path_map = {}
        def map_paths(node, path=()):
            path_map[id(node)] = path
            for index, child in enumerate(node.children):
                map_paths(child, path + (index,))
        map_paths(view)
        visit(view)

    def _content_extent(self, window):
        content = window.contentView()
        bounds = content.bounds()
        return float(bounds.size.width), float(bounds.size.height)

    def _capture_split_positions(self, window):
        positions = self._gui_split_positions_by_window.setdefault(window, {})

        for split_id, split in self._gui_split_views_by_window.get(window, {}).items():
            try:
                positions[split_id] = float(split.positionOfDividerAtIndex_(0))
            except Exception:
                pass

    def _seed_split_positions(self, view, positions):
        if view.kind in {"horizontalSplit", "verticalSplit"} and view.split_id is not None:
            positions.setdefault(view.split_id, float(view.split_position))

        for child in view.children:
            self._seed_split_positions(child, positions)

    def _relayout(self, window):
        view = self._gui_views_by_window.get(window)
        root = self._gui_native_roots_by_window.get(window)

        if view is None or root is None:
            return

        self._capture_split_positions(window)

        width, height = self._content_extent(window)
        positions = self._gui_split_positions_by_window.setdefault(window, {})
        self._seed_split_positions(view, positions)
        calculated = layout(
            view,
            width,
            height,
            split_positions=positions,
        )

        native_nodes = self._gui_native_nodes_by_window[window]
        tab_labels = self._gui_tab_labels_by_window.get(window, {})
        self._apply_layout(
            window,
            calculated,
            native_nodes,
            tab_labels,
            parent_rect=None,
            root_height=height,
            path=(),
        )

        if hasattr(root, "layoutSubtreeIfNeeded"):
            root.layoutSubtreeIfNeeded()

        for split_id, split in self._gui_split_views_by_window.get(window, {}).items():
            position = positions.get(split_id)
            if position is None:
                continue
            try:
                split.setPosition_ofDividerAtIndex_(position, 0)
            except Exception:
                pass

    def _apply_layout(
        self,
        window,
        node,
        native_nodes,
        tab_labels,
        *,
        parent_rect,
        root_height,
        path,
    ):
        appkit = self._load_appkit()
        native = native_nodes[path]
        rect = node.rect

        if parent_rect is None:
            x = 0.0
            y = 0.0
        else:
            x = rect.x - parent_rect.x
            # AppKit uses bottom-left coordinates; GUI layout uses top-left.
            parent_top = parent_rect.y
            y_from_top = rect.y - parent_top
            y = parent_rect.height - y_from_top - rect.height

        native.setFrame_(
            appkit.NSMakeRect(
                x,
                y,
                max(0.0, rect.width),
                max(0.0, rect.height),
            )
        )

        if node.view.kind == "list":
            try:
                document = native.documentView()
                rows = tuple(document.subviews())
            except Exception:
                document = None
                rows = ()

            if document is not None:
                row_height = 30.0
                content_width = max(0.0, rect.width - 14.0)
                content_height = max(rect.height, row_height * len(rows))
                document.setFrame_(
                    appkit.NSMakeRect(
                        0,
                        0,
                        content_width,
                        content_height,
                    )
                )
                for index, row in enumerate(rows):
                    row.setFrame_(
                        appkit.NSMakeRect(
                            0,
                            content_height - (index + 1) * row_height,
                            content_width,
                            row_height,
                        )
                    )

        if node.view.kind == "tabs":
            labels = tab_labels.get(path, ())
            if labels:
                strip_height = 32.0
                try:
                    flipped = native.isFlipped() is True
                except Exception:
                    flipped = False

                label_y = (
                    0.0
                    if flipped
                    else max(0.0, rect.height - strip_height)
                )
                cursor_x = 0.0

                for label in labels:
                    try:
                        fitting = label.fittingSize()
                        label_width = max(
                            96.0,
                            min(180.0, float(fitting.width) + 32.0),
                        )
                    except Exception:
                        label_width = 120.0

                    label.setFrame_(
                        appkit.NSMakeRect(
                            cursor_x,
                            label_y,
                            label_width,
                            strip_height,
                        )
                    )
                    cursor_x += label_width

        for index, child in enumerate(node.children):
            self._apply_layout(
                window,
                child,
                native_nodes,
                tab_labels,
                parent_rect=rect,
                root_height=root_height,
                path=path + (index,),
            )

    def close(self, window):
        result = super().close(window)
        self._gui_views_by_window.pop(window, None)
        self._gui_native_roots_by_window.pop(window, None)
        self._gui_native_nodes_by_window.pop(window, None)
        self._gui_split_views_by_window.pop(window, None)
        self._gui_split_positions_by_window.pop(window, None)
        self._gui_tab_labels_by_window.pop(window, None)
        self._gui_controls_by_window.pop(window, None)
        self._gui_control_meta_by_window.pop(window, None)
        self._gui_tab_buttons_by_window.pop(window, None)
        return result

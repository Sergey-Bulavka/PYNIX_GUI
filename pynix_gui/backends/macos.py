# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""macOS host realization for the PYNIX GUI layout engine."""

import json
import sys
import warnings

from ._macos_host import MacOSHostBackend
from ..core import GUIEvent
from ..commands import GUIDialog, GUIMenu, GUIMenuBar
from ..canvas import canvas_viewport, hit_test_scene
from ..design import DARK, LIGHT, RADII, TYPOGRAPHY, button_visual, rgb, surface_color_role
from ..layout import layout, measure


class _PythonGUIEventBridge:
    def __init__(self, backend, window):
        self._backend = backend
        self._window = window

    def windowShouldClose_(self, sender):
        self._backend._queue_close(self._window)
        return False

    def windowDidResize_(self, notification):
        self._backend._relayout(self._window)
        self._backend._queue_resize(self._window)

    def controlActivated_(self, sender):
        self._backend._queue_control_activation(self._window, sender)

    def controlChanged_(self, sender):
        self._backend._queue_control_change(self._window, sender)

    def controlTextDidChange_(self, notification):
        self._backend._queue_text_change(self._window, notification.object())

    def textDidChange_(self, notification):
        self._backend._queue_text_change(self._window, notification.object())

    def textViewDidChangeSelection_(self, notification):
        self._backend._queue_editor_selection(self._window, notification.object())

    def tabPressed_(self, sender):
        self._backend._queue_tab_selection(self._window, sender)

    def menuItemActivated_(self, sender):
        self._backend._queue_menu_activation(self._window, sender)

    def dialogAction_(self, sender):
        self._backend._queue_dialog_action(self._window, sender)


_OBJC_GUI_EVENT_BRIDGE_TYPE = None
_OBJC_GUI_NAV_BUTTON_TYPE = None
_OBJC_GUI_DRAG_SOURCE_TYPE = None
_OBJC_GUI_DROP_TARGET_TYPE = None
_OBJC_GUI_CANVAS_TYPE = None
_DRAG_PASTEBOARD_TYPE = "org.pynix.gui.drag-payload"


def _objc_gui_navigation_button_type():
    global _OBJC_GUI_NAV_BUTTON_TYPE

    if _OBJC_GUI_NAV_BUTTON_TYPE is not None:
        return _OBJC_GUI_NAV_BUTTON_TYPE

    import AppKit
    import objc

    class PynixGUINavigationButton(AppKit.NSButton):
        def acceptsFirstResponder(self):
            return True

        def keyDown_(self, event):
            try:
                characters = str(event.charactersIgnoringModifiers() or "")
            except Exception:
                characters = ""

            mapping = {
                "\uf700": "up",
                "\uf701": "down",
                "\uf702": "left",
                "\uf703": "right",
                "\r": "enter",
                "\n": "enter",
                "\x7f": "backspace",
            }
            key = mapping.get(characters)
            if key is None:
                try:
                    key_code = int(event.keyCode())
                except Exception:
                    key_code = -1
                key = {
                    126: "up",
                    125: "down",
                    123: "left",
                    124: "right",
                    36: "enter",
                    51: "backspace",
                }.get(key_code)

            if key is not None:
                self._pynix_backend._queue_structured_key(
                    self._pynix_window,
                    self,
                    key,
                )
                return

            objc.super(PynixGUINavigationButton, self).keyDown_(event)

    _OBJC_GUI_NAV_BUTTON_TYPE = PynixGUINavigationButton
    return _OBJC_GUI_NAV_BUTTON_TYPE




def _objc_gui_drag_source_type():
    global _OBJC_GUI_DRAG_SOURCE_TYPE

    if _OBJC_GUI_DRAG_SOURCE_TYPE is not None:
        return _OBJC_GUI_DRAG_SOURCE_TYPE

    import AppKit

    class PynixGUIDragSourceView(AppKit.NSView):
        def hitTest_(self, point):
            return self

        def mouseDragged_(self, event):
            payload = self._pynix_payload
            data = json.dumps(
                {
                    "source_id": self._pynix_source_id,
                    "kind": payload.kind,
                    "value": payload.value,
                    "operations": list(payload.operations),
                },
                separators=(",", ":"),
            )

            pasteboard_item = AppKit.NSPasteboardItem.alloc().init()
            pasteboard_item.setString_forType_(data, _DRAG_PASTEBOARD_TYPE)

            dragging_item = (
                AppKit.NSDraggingItem.alloc()
                .initWithPasteboardWriter_(pasteboard_item)
            )
            dragging_item.setDraggingFrame_contents_(
                self.bounds(),
                None,
            )

            self.beginDraggingSessionWithItems_event_source_(
                [dragging_item],
                event,
                self,
            )

        def draggingSession_sourceOperationMaskForDraggingContext_(
            self,
            session,
            context,
        ):
            mask = 0
            if "copy" in self._pynix_payload.operations:
                mask |= getattr(AppKit, "NSDragOperationCopy", 1)
            if "move" in self._pynix_payload.operations:
                mask |= getattr(AppKit, "NSDragOperationMove", 16)
            return mask

    _OBJC_GUI_DRAG_SOURCE_TYPE = PynixGUIDragSourceView
    return _OBJC_GUI_DRAG_SOURCE_TYPE


def _objc_gui_drop_target_type():
    global _OBJC_GUI_DROP_TARGET_TYPE

    if _OBJC_GUI_DROP_TARGET_TYPE is not None:
        return _OBJC_GUI_DROP_TARGET_TYPE

    import AppKit

    class PynixGUIDropTargetView(AppKit.NSView):
        def draggingEntered_(self, info):
            return self._pynix_backend._drop_operation_for_info(
                self,
                info,
            )

        def draggingUpdated_(self, info):
            return self._pynix_backend._drop_operation_for_info(
                self,
                info,
            )

        def prepareForDragOperation_(self, info):
            return (
                self._pynix_backend._drop_operation_for_info(self, info)
                != getattr(AppKit, "NSDragOperationNone", 0)
            )

        def performDragOperation_(self, info):
            return self._pynix_backend._queue_drop_from_info(
                self._pynix_window,
                self,
                info,
            )

    _OBJC_GUI_DROP_TARGET_TYPE = PynixGUIDropTargetView
    return _OBJC_GUI_DROP_TARGET_TYPE


def _objc_gui_canvas_type():
    global _OBJC_GUI_CANVAS_TYPE

    if _OBJC_GUI_CANVAS_TYPE is not None:
        return _OBJC_GUI_CANVAS_TYPE

    import AppKit

    class PynixGUICanvasView(AppKit.NSView):
        def isFlipped(self):
            return True

        def drawRect_(self, dirty_rect):
            self._pynix_backend._draw_canvas_native(self)

        def mouseDown_(self, event):
            try:
                point = self.convertPoint_fromView_(event.locationInWindow(), None)
            except Exception:
                return
            target = self._pynix_backend._canvas_hit_target(
                self._pynix_scene,
                float(point.x),
                float(point.y),
                float(self.bounds().size.width),
                float(self.bounds().size.height),
            )
            if target is not None:
                self._pynix_backend._event_queue(
                    self._pynix_window
                ).append(GUIEvent("ACTIVATE", target=target))

    _OBJC_GUI_CANVAS_TYPE = PynixGUICanvasView
    return _OBJC_GUI_CANVAS_TYPE


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
            self._backend._queue_resize(self._window)

        def controlActivated_(self, sender):
            self._backend._queue_control_activation(self._window, sender)

        def controlChanged_(self, sender):
            self._backend._queue_control_change(self._window, sender)

        def controlTextDidChange_(self, notification):
            self._backend._queue_text_change(self._window, notification.object())

        def textDidChange_(self, notification):
            self._backend._queue_text_change(self._window, notification.object())

        def textViewDidChangeSelection_(self, notification):
            self._backend._queue_editor_selection(self._window, notification.object())

        def tabPressed_(self, sender):
            self._backend._queue_tab_selection(self._window, sender)

        def menuItemActivated_(self, sender):
            self._backend._queue_menu_activation(self._window, sender)

        def dialogAction_(self, sender):
            self._backend._queue_dialog_action(self._window, sender)

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
        "_gui_menu_targets_by_window",
        "_gui_menu_bars_by_window",
        "_gui_dialogs_by_window",
        "_gui_dialog_buttons_by_window",
        "_gui_dialog_controls_by_window",
        "_gui_dialog_tab_buttons_by_window",
        "_gui_dialog_views_by_window",
        "_gui_resources_by_window",
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
        self._gui_menu_targets_by_window = {}
        self._gui_menu_bars_by_window = {}
        self._gui_dialogs_by_window = {}
        self._gui_dialog_buttons_by_window = {}
        self._gui_dialog_controls_by_window = {}
        self._gui_dialog_tab_buttons_by_window = {}
        self._gui_dialog_views_by_window = {}
        self._gui_resources_by_window = {}

    def _navigation_button(self, appkit, window, title, bridge):
        if self.platform_name == "darwin" and self._appkit_override is None:
            button_type = _objc_gui_navigation_button_type()
            button = (
                button_type.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            button.setTitle_(title)
            button.setTarget_(bridge)
            button.setAction_("controlChanged:")
            button._pynix_backend = self
            button._pynix_window = window
        else:
            button = appkit.NSButton.buttonWithTitle_target_action_(
                title,
                bridge,
                "controlChanged:",
            )

        if hasattr(button, "setRefusesFirstResponder_"):
            try:
                button.setRefusesFirstResponder_(False)
            except Exception:
                pass
        return button

    def _new_canvas_scene_view(self, appkit, window, scene, theme):
        if self.platform_name == "darwin" and self._appkit_override is None:
            canvas_type = _objc_gui_canvas_type()
            native = (
                canvas_type.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            native._pynix_backend = self
            native._pynix_window = window
            native._pynix_scene = scene
            native._pynix_theme = theme
            if hasattr(native, "setWantsLayer_"):
                native.setWantsLayer_(True)
            return native

        return self._new_container(appkit)

    def _new_canvas_view(self, appkit, window, view, theme):
        return self._new_canvas_scene_view(
            appkit,
            window,
            view.canvas_scene,
            theme,
        )

    @staticmethod
    def _canvas_scale(scene, width, height):
        scale, _offset_x, _offset_y = canvas_viewport(scene, width, height)
        return (scale, scale)

    @staticmethod
    def _canvas_point_in_rect(x, y, values):
        rx, ry, rw, rh = values[:4]
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def _canvas_hit_target(self, scene, x, y, width, height):
        return hit_test_scene(scene, x, y, width, height)

    def _draw_canvas_native(self, native):
        appkit = self._load_appkit()
        if appkit is None:
            return

        scene = native._pynix_scene
        theme = native._pynix_theme
        bounds = native.bounds()
        width = float(bounds.size.width)
        height = float(bounds.size.height)
        scale, offset_x, offset_y = canvas_viewport(scene, width, height)

        appkit.NSGraphicsContext.saveGraphicsState()
        try:
            transform = appkit.NSAffineTransform.transform()
            transform.translateXBy_yBy_(offset_x, offset_y)
            transform.scaleXBy_yBy_(scale, scale)
            transform.concat()
            self._draw_canvas_commands(
                appkit,
                scene.commands,
                theme,
                native._pynix_window,
            )
        finally:
            appkit.NSGraphicsContext.restoreGraphicsState()

    def _draw_canvas_commands(self, appkit, commands, theme, window):
        for command in commands:
            if command.kind == "transform":
                dx, dy, sx, sy, rotation = command.values
                appkit.NSGraphicsContext.saveGraphicsState()
                try:
                    transform = appkit.NSAffineTransform.transform()
                    transform.translateXBy_yBy_(dx, dy)
                    transform.scaleXBy_yBy_(sx, sy)
                    if rotation:
                        transform.rotateByDegrees_(rotation)
                    transform.concat()
                    self._draw_canvas_commands(
                        appkit,
                        command.children,
                        theme,
                        window,
                    )
                finally:
                    appkit.NSGraphicsContext.restoreGraphicsState()
                continue

            if command.kind == "clip":
                x, y, width, height = command.values
                appkit.NSGraphicsContext.saveGraphicsState()
                try:
                    clip_path = appkit.NSBezierPath.bezierPathWithRect_(
                        appkit.NSMakeRect(x, y, width, height)
                    )
                    clip_path.addClip()
                    self._draw_canvas_commands(
                        appkit,
                        command.children,
                        theme,
                        window,
                    )
                finally:
                    appkit.NSGraphicsContext.restoreGraphicsState()
                continue

            stroke = (
                None
                if command.stroke_role is None
                else self._native_color(appkit, command.stroke_role, theme)
            )
            fill = (
                None
                if command.fill_role is None
                else self._native_color(appkit, command.fill_role, theme)
            )

            path = None
            if command.kind == "line":
                x1, y1, x2, y2 = command.values
                path = appkit.NSBezierPath.bezierPath()
                path.moveToPoint_(appkit.NSMakePoint(x1, y1))
                path.lineToPoint_(appkit.NSMakePoint(x2, y2))
            elif command.kind == "rect":
                x, y, width, height = command.values
                path = appkit.NSBezierPath.bezierPathWithRect_(
                    appkit.NSMakeRect(x, y, width, height)
                )
            elif command.kind == "ellipse":
                x, y, width, height = command.values
                path = appkit.NSBezierPath.bezierPathWithOvalInRect_(
                    appkit.NSMakeRect(x, y, width, height)
                )
            elif command.kind == "path":
                closed = bool(command.values[0])
                values = command.values[1:]
                path = appkit.NSBezierPath.bezierPath()
                path.moveToPoint_(appkit.NSMakePoint(values[0], values[1]))
                for index in range(2, len(values), 2):
                    path.lineToPoint_(
                        appkit.NSMakePoint(values[index], values[index + 1])
                    )
                if closed:
                    path.closePath()

            if path is not None:
                path.setLineWidth_(float(command.line_width))
                if fill is not None:
                    fill.setFill()
                    path.fill()
                if stroke is not None:
                    stroke.setStroke()
                    path.stroke()
                continue

            if command.kind == "text":
                x, y, value = command.values[:3]
                color = (
                    fill
                    if fill is not None
                    else self._native_color(appkit, "textPrimary", theme)
                )
                font = self._font_for_role(appkit, command.text_role or "body")
                attributes = {
                    appkit.NSForegroundColorAttributeName: color,
                    appkit.NSFontAttributeName: font,
                }
                string = appkit.NSString.stringWithString_(value)
                if len(command.values) == 5:
                    box_width, box_height = command.values[3:]
                    measured = string.sizeWithAttributes_(attributes)
                    if command.text_align == "center":
                        x += (box_width - float(measured.width)) / 2
                    elif command.text_align == "end":
                        x += box_width - float(measured.width)
                    if command.text_valign == "center":
                        y += (box_height - float(measured.height)) / 2
                    elif command.text_valign == "bottom":
                        y += box_height - float(measured.height)
                string.drawAtPoint_withAttributes_(
                    appkit.NSMakePoint(x, y),
                    attributes,
                )
                continue

            if command.kind == "image":
                x, y, width, height = command.values
                logical_path = self._resolve_image_resource(
                    window,
                    command.resource,
                )
                resource_path = (
                    logical_path
                    if logical_path is not None
                    else command.resource
                )
                image = appkit.NSImage.alloc().initWithContentsOfFile_(
                    resource_path
                )
                if image is not None:
                    image.drawInRect_(
                        appkit.NSMakeRect(x, y, width, height)
                    )

    def _new_drag_source_view(self, appkit, window, view):
        if self.platform_name == "darwin" and self._appkit_override is None:
            source_type = _objc_gui_drag_source_type()
            native = (
                source_type.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            native._pynix_payload = view.drag_payload
            native._pynix_source_id = view.drag_source_id
            return native

        return self._new_container(appkit)

    def _new_drop_target_view(self, appkit, window, view):
        if self.platform_name == "darwin" and self._appkit_override is None:
            target_type = _objc_gui_drop_target_type()
            native = (
                target_type.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            native._pynix_backend = self
            native._pynix_window = window
            native._pynix_target_id = view.drop_target_id
            native._pynix_accepted_kinds = tuple(view.accepted_kinds)
            native._pynix_accepted_operations = tuple(
                view.accepted_operations
            )
            native._pynix_dock_region = view.dock_region
            native.registerForDraggedTypes_([_DRAG_PASTEBOARD_TYPE])
            return native

        return self._new_container(appkit)

    @staticmethod
    def _decode_drag_info(info):
        try:
            pasteboard = info.draggingPasteboard()
            raw = pasteboard.stringForType_(_DRAG_PASTEBOARD_TYPE)
            if raw is None:
                return None
            decoded = json.loads(str(raw))
        except Exception:
            return None

        if not isinstance(decoded, dict):
            return None
        required = {"source_id", "kind", "value", "operations"}
        if set(decoded) != required:
            return None
        if any(
            type(decoded[name]) is not str or decoded[name] == ""
            for name in ("source_id", "kind", "value")
        ):
            return None
        if (
            type(decoded["operations"]) is not list
            or not decoded["operations"]
            or any(
                operation not in {"copy", "move"}
                for operation in decoded["operations"]
            )
        ):
            return None
        return decoded

    def _drop_operation_for_info(self, native, info):
        appkit = self._load_appkit()
        if appkit is None:
            return 0

        decoded = self._decode_drag_info(info)
        if decoded is None:
            return getattr(appkit, "NSDragOperationNone", 0)

        if decoded["kind"] not in native._pynix_accepted_kinds:
            return getattr(appkit, "NSDragOperationNone", 0)

        source_operations = tuple(decoded["operations"])
        accepted = native._pynix_accepted_operations

        if "move" in source_operations and "move" in accepted:
            return getattr(appkit, "NSDragOperationMove", 16)
        if "copy" in source_operations and "copy" in accepted:
            return getattr(appkit, "NSDragOperationCopy", 1)
        return getattr(appkit, "NSDragOperationNone", 0)

    def _queue_drop_from_info(self, window, native, info):
        appkit = self._load_appkit()
        decoded = self._decode_drag_info(info)
        if decoded is None or appkit is None:
            return False

        operation_mask = self._drop_operation_for_info(native, info)
        if operation_mask == getattr(appkit, "NSDragOperationNone", 0):
            return False

        operation = (
            "move"
            if operation_mask == getattr(appkit, "NSDragOperationMove", 16)
            else "copy"
        )
        if (
            getattr(native, "_pynix_dock_region", None) is not None
            and decoded["kind"] == "pynix/dock-panel"
            and operation == "move"
        ):
            self._event_queue(window).append(
                GUIEvent(
                    "DOCK",
                    target=native._pynix_target_id,
                    item_id=decoded["value"],
                    region=native._pynix_dock_region,
                )
            )
        else:
            self._event_queue(window).append(
                GUIEvent(
                    "DROP",
                    target=native._pynix_target_id,
                    source_id=decoded["source_id"],
                    payload_kind=decoded["kind"],
                    payload_value=decoded["value"],
                    operation=operation,
                )
            )
        return True

    def set_resources(self, window, catalog):
        from ..resources import GUIResourceCatalog

        if not isinstance(catalog, GUIResourceCatalog):
            raise TypeError("catalog must be GUIResourceCatalog")
        self._gui_resources_by_window[window] = catalog

    def _resource_catalog(self, window):
        return self._gui_resources_by_window.get(window)

    def _resolve_image_resource(self, window, name):
        catalog = self._resource_catalog(window)
        if catalog is None:
            return None
        return catalog.image_path(name)

    def _resolve_vector_resource(self, window, name):
        catalog = self._resource_catalog(window)
        if catalog is None:
            return None
        return catalog.vector_scene(name)

    def _resolve_vector_svg(self, window, name):
        catalog = self._resource_catalog(window)
        if catalog is None:
            return None
        return catalog.vector_svg_path(name)

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

    @staticmethod
    def _shortcut_mask(appkit, shortcut):
        if shortcut is None:
            return 0

        flags = 0
        mapping = {
            "primary": getattr(appkit, "NSEventModifierFlagCommand", 1 << 20),
            "shift": getattr(appkit, "NSEventModifierFlagShift", 1 << 17),
            "alt": getattr(appkit, "NSEventModifierFlagOption", 1 << 19),
            "control": getattr(appkit, "NSEventModifierFlagControl", 1 << 18),
        }
        for modifier in shortcut.modifiers:
            flags |= mapping[modifier]
        return flags

    def _build_native_menu(self, appkit, window, menu_value, bridge):
        native_menu = appkit.NSMenu.alloc().initWithTitle_(menu_value.title)

        for item in menu_value.items:
            if item.kind == "separator":
                native_item = appkit.NSMenuItem.separatorItem()
                native_menu.addItem_(native_item)
                continue

            if item.kind == "submenu":
                native_item = (
                    appkit.NSMenuItem.alloc()
                    .initWithTitle_action_keyEquivalent_(item.label, None, "")
                )
                native_item.setEnabled_(item.enabled)
                child = self._build_native_menu(
                    appkit,
                    window,
                    item.submenu,
                    bridge,
                )
                native_item.setSubmenu_(child)
                native_menu.addItem_(native_item)
                continue

            key = "" if item.shortcut is None else item.shortcut.key.lower()
            native_item = (
                appkit.NSMenuItem.alloc()
                .initWithTitle_action_keyEquivalent_(
                    item.label,
                    "menuItemActivated:",
                    key,
                )
            )
            native_item.setTarget_(bridge)
            native_item.setEnabled_(item.enabled)

            if hasattr(native_item, "setState_"):
                native_item.setState_(
                    getattr(appkit, "NSControlStateValueOn", 1)
                    if item.checked
                    else getattr(appkit, "NSControlStateValueOff", 0)
                )

            if item.shortcut is not None and hasattr(
                native_item,
                "setKeyEquivalentModifierMask_",
            ):
                native_item.setKeyEquivalentModifierMask_(
                    self._shortcut_mask(appkit, item.shortcut)
                )

            self._gui_menu_targets_by_window.setdefault(window, {})[
                native_item
            ] = item.target
            native_menu.addItem_(native_item)

        return native_menu

    def set_menu_bar(self, window, menu_bar):
        if not isinstance(menu_bar, GUIMenuBar):
            raise TypeError("menu_bar must be GUIMenuBar")

        appkit = self._load_appkit()
        if appkit is None:
            raise OSError("Cocoa GUI backend is unavailable.")

        bridge = self._bridge_for_window(window)
        self._gui_menu_targets_by_window[window] = {}

        root = appkit.NSMenu.alloc().initWithTitle_("")

        # macOS applications conventionally own an application menu. It is a
        # backend responsibility rather than public PYNIX command ceremony.
        try:
            import Foundation
            app_name = str(
                Foundation.NSProcessInfo.processInfo().processName()
            )
        except Exception:
            app_name = "PYNIX"

        app_item = (
            appkit.NSMenuItem.alloc()
            .initWithTitle_action_keyEquivalent_(app_name, None, "")
        )
        app_menu = appkit.NSMenu.alloc().initWithTitle_(app_name)

        about_item = (
            appkit.NSMenuItem.alloc()
            .initWithTitle_action_keyEquivalent_(
                f"About {app_name}",
                "orderFrontStandardAboutPanel:",
                "",
            )
        )
        app_menu.addItem_(about_item)
        app_menu.addItem_(appkit.NSMenuItem.separatorItem())

        services_item = (
            appkit.NSMenuItem.alloc()
            .initWithTitle_action_keyEquivalent_("Services", None, "")
        )
        services_menu = appkit.NSMenu.alloc().initWithTitle_("Services")
        services_item.setSubmenu_(services_menu)
        app_menu.addItem_(services_item)
        try:
            appkit.NSApplication.sharedApplication().setServicesMenu_(
                services_menu
            )
        except Exception:
            pass

        app_menu.addItem_(appkit.NSMenuItem.separatorItem())

        hide_item = (
            appkit.NSMenuItem.alloc()
            .initWithTitle_action_keyEquivalent_(
                f"Hide {app_name}",
                "hide:",
                "h",
            )
        )
        app_menu.addItem_(hide_item)

        hide_others = (
            appkit.NSMenuItem.alloc()
            .initWithTitle_action_keyEquivalent_(
                "Hide Others",
                "hideOtherApplications:",
                "h",
            )
        )
        if hasattr(hide_others, "setKeyEquivalentModifierMask_"):
            hide_others.setKeyEquivalentModifierMask_(
                getattr(appkit, "NSEventModifierFlagCommand", 1 << 20)
                | getattr(appkit, "NSEventModifierFlagOption", 1 << 19)
            )
        app_menu.addItem_(hide_others)

        show_all = (
            appkit.NSMenuItem.alloc()
            .initWithTitle_action_keyEquivalent_(
                "Show All",
                "unhideAllApplications:",
                "",
            )
        )
        app_menu.addItem_(show_all)
        app_menu.addItem_(appkit.NSMenuItem.separatorItem())

        quit_item = (
            appkit.NSMenuItem.alloc()
            .initWithTitle_action_keyEquivalent_(
                f"Quit {app_name}",
                "terminate:",
                "q",
            )
        )
        app_menu.addItem_(quit_item)

        app_item.setSubmenu_(app_menu)
        root.addItem_(app_item)

        for menu_value in menu_bar.menus:
            top = (
                appkit.NSMenuItem.alloc()
                .initWithTitle_action_keyEquivalent_(
                    menu_value.title,
                    None,
                    "",
                )
            )
            submenu_native = self._build_native_menu(
                appkit,
                window,
                menu_value,
                bridge,
            )
            top.setSubmenu_(submenu_native)
            root.addItem_(top)

        application = appkit.NSApplication.sharedApplication()
        application.setMainMenu_(root)
        self._gui_menu_bars_by_window[window] = root
        return None

    def clear_menu_bar(self, window):
        appkit = self._load_appkit()
        if appkit is None:
            raise OSError("Cocoa GUI backend is unavailable.")

        application = appkit.NSApplication.sharedApplication()
        if hasattr(application, "setMainMenu_"):
            application.setMainMenu_(None)

        self._gui_menu_bars_by_window.pop(window, None)
        self._gui_menu_targets_by_window.pop(window, None)
        return None

    def _merge_dialog_event_maps(self, window):
        control_meta = self._gui_control_meta_by_window.setdefault(window, {})
        tab_buttons = self._gui_tab_buttons_by_window.setdefault(window, {})

        for mapping in self._gui_dialog_controls_by_window.get(window, {}).values():
            control_meta.update(mapping)
        for mapping in self._gui_dialog_tab_buttons_by_window.get(window, {}).values():
            tab_buttons.update(mapping)

    def present_dialog(self, window, dialog):
        if not isinstance(dialog, GUIDialog):
            raise TypeError("dialog must be GUIDialog")

        appkit = self._load_appkit()
        if appkit is None:
            raise OSError("Cocoa GUI backend is unavailable.")

        dialogs = self._gui_dialogs_by_window.setdefault(window, {})
        if dialog.dialog_id in dialogs:
            raise ValueError(f"GUI dialog '{dialog.dialog_id}' is already active.")

        preferred = measure(dialog.content).preferred
        width = max(420.0, min(760.0, preferred.width + 40.0))
        content_height = max(120.0, min(520.0, preferred.height))
        height = content_height + 100.0

        style = getattr(appkit, "NSWindowStyleMaskTitled", 1)
        panel_type = getattr(appkit, "NSPanel", appkit.NSWindow)
        panel = (
            panel_type.alloc()
            .initWithContentRect_styleMask_backing_defer_(
                appkit.NSMakeRect(0, 0, width, height),
                style,
                appkit.NSBackingStoreBuffered,
                False,
            )
        )
        if panel is None:
            raise OSError("Cocoa failed to create a GUI dialog.")

        panel.setTitle_(dialog.title)

        host = self._new_container(appkit)
        host.setFrame_(appkit.NSMakeRect(0, 0, width, height))

        content_holder = self._new_container(appkit)
        content_holder.setFrame_(
            appkit.NSMakeRect(
                20.0,
                70.0,
                width - 40.0,
                content_height,
            )
        )
        host.addSubview_(content_holder)

        bridge = self._bridge_for_window(window)
        native_nodes = {}
        split_views = {}
        tab_labels = {}
        controls = {}
        control_meta = {}
        tab_buttons = {}
        native_content = self._build_native_tree(
            appkit,
            dialog.content,
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
        content_holder.addSubview_(native_content)

        self._gui_dialog_controls_by_window.setdefault(window, {})[
            dialog.dialog_id
        ] = control_meta
        self._gui_dialog_tab_buttons_by_window.setdefault(window, {})[
            dialog.dialog_id
        ] = tab_buttons
        self._gui_dialog_views_by_window.setdefault(window, {})[
            dialog.dialog_id
        ] = dialog.content
        self._merge_dialog_event_maps(window)

        if self.platform_name == "darwin" and self._appkit_override is None:
            from ..text_layout import native_text_layout
            calculated = native_text_layout(
                dialog.content, width - 40.0, content_height,
                measure_text=self.text_metrics_snapshot,
                wrap_measure=self.measure_wrapped_text,
            ).root
        else:
            calculated = layout(dialog.content, width - 40.0, content_height)
        self._apply_layout(
            window,
            calculated,
            native_nodes,
            tab_labels,
            parent_rect=None,
            root_height=content_height,
            path=(),
        )

        buttons = self._gui_dialog_buttons_by_window.setdefault(window, {})
        button_width = 110.0
        button_height = 32.0
        gap = 8.0
        total_width = (
            button_width * len(dialog.actions)
            + gap * max(0, len(dialog.actions) - 1)
        )
        x = max(20.0, width - 20.0 - total_width)

        for action in dialog.actions:
            button = appkit.NSButton.buttonWithTitle_target_action_(
                action.label,
                bridge,
                "dialogAction:",
            )
            button.setFrame_(
                appkit.NSMakeRect(
                    x,
                    20.0,
                    button_width,
                    button_height,
                )
            )
            if hasattr(button, "setEnabled_"):
                button.setEnabled_(action.enabled)
            if action.default and hasattr(button, "setKeyEquivalent_"):
                button.setKeyEquivalent_("\r")
            host.addSubview_(button)
            buttons[button] = (
                dialog.dialog_id,
                action.target,
                panel,
            )
            x += button_width + gap

        panel.setContentView_(host)
        dialogs[dialog.dialog_id] = panel

        if hasattr(window, "beginSheet_completionHandler_"):
            window.beginSheet_completionHandler_(panel, None)
        elif hasattr(panel, "makeKeyAndOrderFront_"):
            panel.makeKeyAndOrderFront_(None)

        return None

    def dismiss_dialog(self, window, dialog_id):
        dialogs = self._gui_dialogs_by_window.get(window, {})
        panel = dialogs.pop(dialog_id, None)
        if panel is None:
            return None

        if hasattr(window, "endSheet_"):
            try:
                window.endSheet_(panel)
            except Exception:
                pass
        if hasattr(panel, "orderOut_"):
            try:
                panel.orderOut_(None)
            except Exception:
                pass
        elif hasattr(panel, "close"):
            try:
                panel.close()
            except Exception:
                pass

        buttons = self._gui_dialog_buttons_by_window.get(window, {})
        for button, meta in tuple(buttons.items()):
            if meta[0] == dialog_id:
                buttons.pop(button, None)

        local_controls = self._gui_dialog_controls_by_window.get(window, {}).pop(
            dialog_id,
            {},
        )
        global_controls = self._gui_control_meta_by_window.get(window, {})
        for native in local_controls:
            global_controls.pop(native, None)

        local_tabs = self._gui_dialog_tab_buttons_by_window.get(window, {}).pop(
            dialog_id,
            {},
        )
        global_tabs = self._gui_tab_buttons_by_window.get(window, {})
        for native in local_tabs:
            global_tabs.pop(native, None)

        self._gui_dialog_views_by_window.get(window, {}).pop(dialog_id, None)
        return None

    def render(self, window, view):
        appkit = self._load_appkit()
        if appkit is None:
            raise OSError("Cocoa GUI backend is unavailable.")

        previous_focus = self._capture_focus(window)
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
        self._merge_dialog_event_maps(window)

        window.setContentView_(native_root)
        self._relayout(window)
        self._apply_control_state(window, view)
        self._restore_focus(window, view, previous_focus)
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

    def measure_wrapped_text(self, role, value, width):
        """AppKit-backed exact candidate widths for height-for-width planning."""
        from ..wrap_engine import wrap_text

        appkit = self._load_appkit()
        font = self._font_for_role(appkit, role)
        attributes = {appkit.NSFontAttributeName: font}

        def measure_width(candidate):
            return float(
                appkit.NSString.stringWithString_(candidate)
                .sizeWithAttributes_(attributes).width
            )

        line_height = float(
            appkit.NSString.stringWithString_("Ag")
            .sizeWithAttributes_(attributes).height
        )
        return wrap_text(
            value, width,
            measure_width=measure_width,
            line_height=line_height,
        )

    def text_metrics_snapshot(self, view):
        """Measure immutable GUI text leaves with AppKit on the GUI thread."""
        from ..text_metrics import snapshot_text_metrics

        appkit = self._load_appkit()
        if appkit is None:
            raise RuntimeError("AppKit is unavailable for native text measurement")

        def measure(role, value):
            font = self._font_for_role(appkit, role)
            attributes = {appkit.NSFontAttributeName: font}
            size = appkit.NSString.stringWithString_(value).sizeWithAttributes_(
                attributes
            )
            return float(size.width), float(size.height)

        return snapshot_text_metrics(view, measure)

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
            border_role = "separator"
            if view.role == "hero":
                border_role = "accentMuted"
            elif view.role == "successSurface":
                border_role = "success"
            elif view.role == "warningSurface":
                border_role = "warning"
            elif view.role == "dangerSurface":
                border_role = "error"
            elif view.role == "infoSurface":
                border_role = "info"

            border = self._native_color(appkit, border_role, theme)
            if border is not None:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        layer.setBorderColor_(border.CGColor())
                    layer.setBorderWidth_(1.0)
                except Exception:
                    pass

            radius = (
                RADII["radius3"]
                if view.role in {"card", "hero", "overlay"}
                else RADII["radius2"]
            )
            try:
                layer.setCornerRadius_(float(radius))
            except Exception:
                pass

            if view.role in {"card", "overlay"}:
                try:
                    if hasattr(layer, "setMasksToBounds_"):
                        layer.setMasksToBounds_(False)
                    if hasattr(layer, "setShadowOpacity_"):
                        layer.setShadowOpacity_(0.14 if theme != "dark" else 0.28)
                    if hasattr(layer, "setShadowRadius_"):
                        layer.setShadowRadius_(8.0)
                    if hasattr(layer, "setShadowOffset_"):
                        layer.setShadowOffset_(appkit.NSMakeSize(0.0, -2.0))
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
            if view.overflow == "wrap":
                cell = native.cell()
                cell.setWraps_(True)
                cell.setScrollable_(False)
                cell.setLineBreakMode_(appkit.NSLineBreakByWordWrapping)
            if view.overflow in ("ellipsis", "clip"):
                cell = native.cell()
                cell.setWraps_(False)
                cell.setScrollable_(False)
                cell.setLineBreakMode_(
                    appkit.NSLineBreakByTruncatingTail
                    if view.overflow == "ellipsis"
                    else appkit.NSLineBreakByClipping
                )
            if hasattr(native, "setFont_"):
                native.setFont_(self._font_for_role(appkit, view.role))
            if hasattr(native, "setTextColor_"):
                text_color_role = {
                    "caption": "textMuted",
                    "overline": "accent",
                    "body": "textSecondary",
                }.get(view.role, "textPrimary")
                native.setTextColor_(
                    self._native_color(appkit, text_color_role, theme)
                )

        elif view.kind == "button":
            native = appkit.NSButton.buttonWithTitle_target_action_(
                view.text,
                bridge,
                "controlActivated:",
            )
            if hasattr(native, "setAccessibilityLabel_"):
                native.setAccessibilityLabel_(view.text)
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
            if hasattr(text_view, "setDelegate_"):
                text_view.setDelegate_(bridge)

            native.setDocumentView_(text_view)
            if hasattr(native, "setHasVerticalScroller_"):
                native.setHasVerticalScroller_(True)
            controls[view.target] = text_view
            control_meta[text_view] = ("textArea", view.target)

        elif view.kind == "richEditor":
            native = (
                appkit.NSScrollView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            text_view = (
                appkit.NSTextView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            text_view.setString_(view.value)
            if hasattr(text_view, "setEditable_"):
                text_view.setEditable_(not view.read_only)
            if hasattr(text_view, "setRichText_"):
                text_view.setRichText_(False)
            if hasattr(text_view, "setUsesFindPanel_"):
                text_view.setUsesFindPanel_(True)
            if hasattr(text_view, "setAllowsUndo_"):
                text_view.setAllowsUndo_(True)
            if hasattr(text_view, "setBackgroundColor_"):
                text_view.setBackgroundColor_(
                    self._native_color(appkit, "surfaceSunken", theme)
                )
            if hasattr(text_view, "setTextColor_"):
                text_view.setTextColor_(
                    self._native_color(appkit, "textPrimary", theme)
                )
            if hasattr(text_view, "setFont_"):
                text_view.setFont_(self._font_for_role(appkit, "code"))

            storage = text_view.textStorage() if hasattr(text_view, "textStorage") else None
            if storage is not None:
                full_range = appkit.NSMakeRange(0, len(view.value))
                base_attributes = {
                    appkit.NSForegroundColorAttributeName: self._native_color(
                        appkit,
                        "textPrimary",
                        theme,
                    ),
                    appkit.NSFontAttributeName: self._font_for_role(
                        appkit,
                        "code",
                    ),
                }
                try:
                    storage.setAttributes_range_(base_attributes, full_range)
                except Exception:
                    pass

                editor_colors = {
                    "plain": "textPrimary",
                    "keyword": "accent",
                    "type": "info",
                    "string": "success",
                    "number": "warning",
                    "comment": "textMuted",
                    "function": "accent",
                    "property": "textSecondary",
                    "constant": "warning",
                    "warning": "warning",
                    "error": "error",
                    "muted": "textMuted",
                    "strong": "textPrimary",
                }
                for span in view.spans:
                    attrs = {
                        appkit.NSForegroundColorAttributeName: self._native_color(
                            appkit,
                            editor_colors[span.role],
                            theme,
                        )
                    }
                    if span.role == "strong":
                        attrs[appkit.NSFontAttributeName] = self._font_for_role(
                            appkit,
                            "bodyStrong",
                        )
                    try:
                        storage.addAttributes_range_(
                            attrs,
                            appkit.NSMakeRange(
                                span.start,
                                span.end - span.start,
                            ),
                        )
                    except Exception:
                        pass

            if hasattr(text_view, "setSelectedRange_"):
                try:
                    text_view.setSelectedRange_(
                        appkit.NSMakeRange(
                            view.selection_start,
                            view.selection_end - view.selection_start,
                        )
                    )
                except Exception:
                    pass

            if hasattr(text_view, "setDelegate_"):
                text_view.setDelegate_(bridge)

            native.setDocumentView_(text_view)
            if hasattr(native, "setHasVerticalScroller_"):
                native.setHasVerticalScroller_(True)
            if hasattr(native, "setHasHorizontalScroller_"):
                native.setHasHorizontalScroller_(True)
            if hasattr(native, "setAutohidesScrollers_"):
                native.setAutohidesScrollers_(True)

            controls[view.target] = text_view
            control_meta[text_view] = ("richEditor", view.target)

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

        elif view.kind == "tree":
            native = (
                appkit.NSScrollView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            document = self._new_container(appkit)
            expanded = set(view.expanded_ids)
            visible = []

            def append_visible(nodes, depth=0):
                for node_value in nodes:
                    visible.append((node_value, depth))
                    if node_value.node_id in expanded:
                        append_visible(node_value.children, depth + 1)

            append_visible(view.data)
            row_height = 30.0
            document.setFrame_(
                appkit.NSMakeRect(
                    0,
                    0,
                    0,
                    max(row_height, row_height * len(visible)),
                )
            )

            for node_value, depth in visible:
                row = self._new_container(appkit)
                disclosure = appkit.NSButton.buttonWithTitle_target_action_(
                    (
                        "⌄"
                        if node_value.children and node_value.node_id in expanded
                        else "›"
                        if node_value.children
                        else ""
                    ),
                    bridge,
                    "controlChanged:",
                )
                if hasattr(disclosure, "setBordered_"):
                    disclosure.setBordered_(False)
                if node_value.children and hasattr(disclosure, "setFont_"):
                    from ..tree_visuals import (
                        tree_disclosure_size, tree_disclosure_baseline_offset,
                    )
                    font_size = tree_disclosure_size(row_height, 13.0)
                    disclosure.setFont_(appkit.NSFont.systemFontOfSize_(font_size))
                    # Unicode chevrons are not centered within their line box:
                    # the downward glyph in particular sits below the folder.
                    # Move the glyph baseline, not its clickable button frame.
                    if hasattr(disclosure, "setAttributedTitle_"):
                        try:
                            attributes = {
                                appkit.NSFontAttributeName:
                                    appkit.NSFont.systemFontOfSize_(font_size),
                                appkit.NSBaselineOffsetAttributeName:
                                    tree_disclosure_baseline_offset(
                                        row_height,
                                        node_value.node_id in expanded,
                                    ),
                            }
                            title = disclosure.title()
                            attributed = appkit.NSAttributedString.alloc(
                            ).initWithString_attributes_(title, attributes)
                            disclosure.setAttributedTitle_(attributed)
                        except (AttributeError, TypeError):
                            pass
                if hasattr(disclosure, "setTag_"):
                    disclosure.setTag_(depth)
                row.addSubview_(disclosure)

                label = self._navigation_button(
                    appkit,
                    bridge._window,
                    node_value.label,
                    bridge,
                )
                if hasattr(label, "setBordered_"):
                    label.setBordered_(node_value.node_id == view.selected_id)
                if node_value.node_id == view.selected_id and hasattr(
                    label,
                    "setBezelColor_",
                ):
                    try:
                        label.setBezelColor_(
                            self._native_color(
                                appkit,
                                "surfaceSelected",
                                theme,
                            )
                        )
                    except Exception:
                        pass
                if hasattr(label, "setAlignment_"):
                    label.setAlignment_(getattr(appkit, "NSTextAlignmentLeft", 0))
                # A compact, icon-bearing explorer item rather than a
                # full-width text button. Keep selection and event metadata.
                from ..tree_visuals import (
                    tree_file_icon_kind, tree_node_kind, tree_icon_size, pnx_icon_path,
                )
                kind = tree_file_icon_kind(
                    node_value.label, tree_node_kind(node_value) == "folder"
                )
                icon_image = None
                try:
                    if kind == "pnx":
                        icon_image = appkit.NSImage.alloc().initWithContentsOfFile_(
                            str(pnx_icon_path())
                        )
                    elif kind == "folder":
                        icon_image = appkit.NSImage.imageNamed_(
                            getattr(appkit, "NSImageNameFolder", "NSFolder")
                        )
                    else:
                        # NSWorkspace resolves the file type to a real document
                        # icon; unlike undocumented NSImage names it won't
                        # silently leave the label iconless.
                        workspace = appkit.NSWorkspace.sharedWorkspace()
                        icon_image = workspace.iconForFileType_(
                            "txt"
                        )
                    if icon_image is not None:
                        font = label.font() if hasattr(label, "font") else None
                        font_points = (
                            float(font.pointSize()) if font is not None else 13.0
                        )
                        points = tree_icon_size(row_height, font_points)
                        sized_icon = icon_image.copy()
                        sized_icon.setSize_(appkit.NSMakeSize(points, points))
                        label.setImage_(sized_icon)
                        label.setImageScaling_(
                            getattr(appkit, "NSImageScaleProportionallyDown", 0)
                        )
                        label.setImagePosition_(
                            getattr(appkit, "NSImageLeft", 2)
                        )
                except (AttributeError, TypeError):
                    pass
                row.addSubview_(label)

                control_meta[label] = (
                    "treeRow",
                    view.target,
                    node_value.node_id,
                )
                if node_value.children:
                    control_meta[disclosure] = (
                        "treeDisclosure",
                        view.target,
                        node_value.node_id,
                        node_value.node_id in expanded,
                    )
                document.addSubview_(row)

            if hasattr(native, "setDocumentView_"):
                native.setDocumentView_(document)
            else:
                native.addSubview_(document)
            if hasattr(native, "setHasVerticalScroller_"):
                native.setHasVerticalScroller_(True)
            if hasattr(native, "setAutohidesScrollers_"):
                native.setAutohidesScrollers_(True)

            controls[view.target] = native
            control_meta[native] = ("tree", view.target)

        elif view.kind == "canvas":
            native = self._new_canvas_view(
                appkit,
                bridge._window,
                view,
                theme,
            )
            controls[view.target] = native

        elif view.kind == "table":
            native = (
                appkit.NSScrollView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            document = self._new_container(appkit)
            columns, rows = view.data
            row_height = 30.0
            header_height = 32.0
            document.setFrame_(
                appkit.NSMakeRect(
                    0,
                    0,
                    0,
                    header_height + row_height * len(rows),
                )
            )

            header = self._new_container(appkit)
            for column_value in columns:
                label = appkit.NSTextField.labelWithString_(column_value.title)
                if hasattr(label, "setFont_"):
                    label.setFont_(self._font_for_role(appkit, "label"))
                if hasattr(label, "setTextColor_"):
                    label.setTextColor_(
                        self._native_color(appkit, "textSecondary", theme)
                    )
                header.addSubview_(label)
            document.addSubview_(header)

            alignment_values = {
                "start": getattr(appkit, "NSTextAlignmentLeft", 0),
                "center": getattr(appkit, "NSTextAlignmentCenter", 2),
                "end": getattr(appkit, "NSTextAlignmentRight", 1),
            }

            for row_value in rows:
                row = self._new_container(appkit)
                for column_index, (column_value, cell) in enumerate(
                    zip(columns, row_value.cells)
                ):
                    is_file_manager_name = (
                        view.target == "files-table" and column_index == 0
                    )
                    is_directory = (
                        is_file_manager_name and len(row_value.cells) > 1
                        and row_value.cells[1] == "Folder"
                    )
                    display_cell = (
                        ("›  " if is_directory else "") + cell
                        if is_file_manager_name else cell
                    )
                    cell_button = self._navigation_button(
                        appkit,
                        bridge._window,
                        display_cell,
                        bridge,
                    )
                    if is_file_manager_name:
                        from ..tree_visuals import (
                            tree_file_icon_kind, tree_icon_size, pnx_icon_path,
                        )
                        kind = tree_file_icon_kind(cell, is_directory)
                        try:
                            if kind == "pnx":
                                picture = appkit.NSImage.alloc().initWithContentsOfFile_(
                                    str(pnx_icon_path())
                                )
                            elif kind == "folder":
                                picture = appkit.NSImage.imageNamed_(
                                    getattr(appkit, "NSImageNameFolder", "NSFolder")
                                )
                            else:
                                picture = appkit.NSWorkspace.sharedWorkspace(
                                ).iconForFileType_("txt")
                            if picture is not None:
                                picture = picture.copy()
                                side = tree_icon_size(row_height, 13.0)
                                picture.setSize_(appkit.NSMakeSize(side, side))
                                cell_button.setImage_(picture)
                                cell_button.setImagePosition_(
                                    getattr(appkit, "NSImageLeft", 2)
                                )
                                cell_button.setImageScaling_(
                                    getattr(appkit, "NSImageScaleProportionallyDown", 0)
                                )
                        except (AttributeError, TypeError):
                            pass
                    if hasattr(cell_button, "setBordered_"):
                        cell_button.setBordered_(
                            row_value.row_id == view.selected_id
                        )
                    if row_value.row_id == view.selected_id and hasattr(
                        cell_button,
                        "setBezelColor_",
                    ):
                        try:
                            cell_button.setBezelColor_(
                                self._native_color(
                                    appkit,
                                    "surfaceSelected",
                                    theme,
                                )
                            )
                        except Exception:
                            pass
                    if hasattr(cell_button, "setAlignment_"):
                        cell_button.setAlignment_(
                            alignment_values[column_value.alignment]
                        )
                    row.addSubview_(cell_button)
                    control_meta[cell_button] = (
                        "tableRow",
                        view.target,
                        row_value.row_id,
                    )
                document.addSubview_(row)

            if hasattr(native, "setDocumentView_"):
                native.setDocumentView_(document)
            else:
                native.addSubview_(document)
            if hasattr(native, "setHasVerticalScroller_"):
                native.setHasVerticalScroller_(True)
            if hasattr(native, "setHasHorizontalScroller_"):
                native.setHasHorizontalScroller_(True)
            if hasattr(native, "setAutohidesScrollers_"):
                native.setAutohidesScrollers_(True)

            controls[view.target] = native
            control_meta[native] = ("table", view.target)

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

        elif view.kind == "vectorIcon":
            scene = self._resolve_vector_resource(
                bridge._window,
                view.resource,
            )
            svg_path = self._resolve_vector_svg(
                bridge._window,
                view.resource,
            )
            if scene is not None:
                native = self._new_canvas_scene_view(
                    appkit,
                    bridge._window,
                    scene,
                    theme,
                )
            else:
                native = (
                    appkit.NSImageView.alloc()
                    .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
                )
                if svg_path is not None:
                    try:
                        svg_image = (
                            appkit.NSImage.alloc()
                            .initWithContentsOfFile_(svg_path)
                        )
                        if svg_image is not None:
                            native.setImage_(svg_image)
                    except Exception:
                        pass
                if hasattr(native, "setImageScaling_"):
                    native.setImageScaling_(
                        getattr(
                            appkit,
                            "NSImageScaleProportionallyUpOrDown",
                            3,
                        )
                    )

        elif view.kind in {"icon", "image"}:
            native = (
                appkit.NSImageView.alloc()
                .initWithFrame_(appkit.NSMakeRect(0, 0, 0, 0))
            )
            image = None
            if view.kind == "icon":
                symbol = getattr(
                    appkit.NSImage,
                    "imageWithSystemSymbolName_accessibilityDescription_",
                    None,
                )
                if symbol is not None:
                    try:
                        image = symbol(view.resource, view.resource)
                    except Exception:
                        image = None
                if image is None and hasattr(appkit.NSImage, "imageNamed_"):
                    image = appkit.NSImage.imageNamed_(view.resource)
            else:
                logical_path = self._resolve_image_resource(
                    bridge._window,
                    view.resource,
                )
                resource_path = (
                    logical_path
                    if logical_path is not None
                    else view.resource
                )
                if logical_path is None and hasattr(appkit.NSImage, "imageNamed_"):
                    image = appkit.NSImage.imageNamed_(view.resource)
                if image is None:
                    try:
                        image = (
                            appkit.NSImage.alloc()
                            .initWithContentsOfFile_(resource_path)
                        )
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
                native.setImageScaling_(
                    getattr(
                        appkit,
                        "NSImageScaleProportionallyUpOrDown",
                        3,
                    )
                )

        elif view.kind == "contextMenu":
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
            context = self._build_native_menu(
                appkit,
                bridge._window,
                view.menu,
                bridge,
            )
            target_native = child if hasattr(child, "setMenu_") else native
            if hasattr(target_native, "setMenu_"):
                target_native.setMenu_(context)

        elif view.kind == "tooltip":
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
            target_native = child if hasattr(child, "setToolTip_") else native
            if hasattr(target_native, "setToolTip_"):
                target_native.setToolTip_(view.tooltip_text)

        elif view.kind == "collapsible":
            native = self._new_container(appkit)
            header = appkit.NSButton.buttonWithTitle_target_action_(
                view.text,
                bridge,
                "controlChanged:",
            )
            if hasattr(header, "setButtonType_"):
                header.setButtonType_(
                    getattr(appkit, "NSButtonTypeOnOff", 6)
                )
            if hasattr(header, "setState_"):
                header.setState_(
                    getattr(appkit, "NSControlStateValueOn", 1)
                    if view.checked
                    else getattr(appkit, "NSControlStateValueOff", 0)
                )
            if hasattr(header, "setBordered_"):
                header.setBordered_(False)
            if hasattr(header, "setAlignment_"):
                header.setAlignment_(getattr(appkit, "NSTextAlignmentLeft", 0))
            if hasattr(header, "setFont_"):
                header.setFont_(self._font_for_role(appkit, "label"))
            native.addSubview_(header)
            controls[view.target] = header
            control_meta[header] = ("collapsible", view.target)

            if view.checked:
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

        elif view.kind == "draggable":
            native = self._new_drag_source_view(
                appkit,
                bridge._window,
                view,
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
            native.addSubview_(child)

        elif view.kind in {"dropTarget", "dockTarget"}:
            native = self._new_drop_target_view(
                appkit,
                bridge._window,
                view,
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
            native.addSubview_(child)

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
        elif kind == "collapsible":
            event = GUIEvent(
                "CHANGE",
                target=target,
                checked=bool(sender.state()),
            )
        elif kind == "treeRow":
            if hasattr(window, "makeFirstResponder_"):
                try:
                    window.makeFirstResponder_(sender)
                except Exception:
                    pass
            event = GUIEvent(
                "SELECTION",
                target=target,
                item_id=meta[2],
            )
        elif kind == "treeDisclosure":
            event = GUIEvent(
                "EXPANSION",
                target=target,
                item_id=meta[2],
                checked=not bool(meta[3]),
            )
        elif kind == "tableRow":
            if hasattr(window, "makeFirstResponder_"):
                try:
                    window.makeFirstResponder_(sender)
                except Exception:
                    pass
            double_click = False
            if target == "files-table":
                try:
                    native_event = self._load_appkit().NSApplication.sharedApplication().currentEvent()
                    double_click = int(native_event.clickCount()) >= 2
                except (AttributeError, TypeError, ValueError):
                    pass
            event = GUIEvent(
                "OPEN" if double_click else "SELECTION",
                target=target,
                item_id=meta[2],
            )
        else:
            return

        self._event_queue(window).append(event)

    def _structured_view(self, window, target, kind):
        root = self._gui_views_by_window.get(window)

        def visit(node):
            if node.kind == kind and node.target == target:
                return node
            for child in node.children:
                found = visit(child)
                if found is not None:
                    return found
            return None

        found = None if root is None else visit(root)
        if found is not None:
            return found

        for dialog_view in self._gui_dialog_views_by_window.get(window, {}).values():
            found = visit(dialog_view)
            if found is not None:
                return found
        return None

    @staticmethod
    def _visible_tree(nodes, expanded_ids):
        expanded = set(expanded_ids)
        result = []
        parents = {}

        def visit(values, parent=None):
            for node in values:
                result.append(node.node_id)
                parents[node.node_id] = parent
                if node.node_id in expanded:
                    visit(node.children, node.node_id)

        visit(nodes)
        return tuple(result), parents

    @staticmethod
    def _tree_node_by_id(nodes, node_id):
        for node in nodes:
            if node.node_id == node_id:
                return node
            found = MacOSGUIBackend._tree_node_by_id(node.children, node_id)
            if found is not None:
                return found
        return None

    def _queue_structured_key(self, window, sender, key):
        meta = self._control_meta(window, sender)
        if meta is None:
            return

        kind, target = meta[:2]

        if kind == "treeRow":
            current_id = meta[2]
            view = self._structured_view(window, target, "tree")
            if view is None:
                return

            visible, parents = self._visible_tree(
                view.data,
                view.expanded_ids,
            )
            if current_id not in visible:
                return

            index = visible.index(current_id)

            if key == "up" and index > 0:
                self._event_queue(window).append(
                    GUIEvent(
                        "SELECTION",
                        target=target,
                        item_id=visible[index - 1],
                    )
                )
                return

            if key == "down" and index + 1 < len(visible):
                self._event_queue(window).append(
                    GUIEvent(
                        "SELECTION",
                        target=target,
                        item_id=visible[index + 1],
                    )
                )
                return

            node = self._tree_node_by_id(view.data, current_id)
            if node is None:
                return

            expanded = current_id in set(view.expanded_ids)

            if key == "left":
                if node.children and expanded:
                    self._event_queue(window).append(
                        GUIEvent(
                            "EXPANSION",
                            target=target,
                            item_id=current_id,
                            checked=False,
                        )
                    )
                    return

                parent_id = parents.get(current_id)
                if parent_id is not None:
                    self._event_queue(window).append(
                        GUIEvent(
                            "SELECTION",
                            target=target,
                            item_id=parent_id,
                        )
                    )
                return

            if key == "right":
                if node.children and not expanded:
                    self._event_queue(window).append(
                        GUIEvent(
                            "EXPANSION",
                            target=target,
                            item_id=current_id,
                            checked=True,
                        )
                    )
                    return

                if node.children and expanded:
                    self._event_queue(window).append(
                        GUIEvent(
                            "SELECTION",
                            target=target,
                            item_id=node.children[0].node_id,
                        )
                    )
                return

        if kind == "tableRow":
            current_id = meta[2]
            view = self._structured_view(window, target, "table")
            if view is None:
                return

            _columns, rows = view.data
            identities = tuple(row.row_id for row in rows)
            if current_id not in identities:
                return

            if target == "files-table":
                if key == "enter":
                    self._event_queue(window).append(
                        GUIEvent("OPEN", target=target, item_id=current_id)
                    )
                    return
                if key == "backspace":
                    self._event_queue(window).append(
                        GUIEvent("ACTIVATE", target="files-up")
                    )
                    return
            index = identities.index(current_id)
            if key == "up" and index > 0:
                next_id = identities[index - 1]
            elif key == "down" and index + 1 < len(identities):
                next_id = identities[index + 1]
            else:
                return

            self._event_queue(window).append(
                GUIEvent(
                    "SELECTION",
                    target=target,
                    item_id=next_id,
                )
            )

    def _queue_text_change(self, window, sender):
        meta = self._control_meta(window, sender)
        if meta is None:
            return
        kind, target = meta
        if kind == "textField":
            value = str(sender.stringValue())
        elif kind in {"textArea", "richEditor"}:
            value = str(sender.string()).replace("\r\n", "\n").replace("\r", "\n")
        else:
            return

        if kind == "richEditor":
            try:
                selected = sender.selectedRange()
                start = int(selected.location)
                end = start + int(selected.length)
                self._event_queue(window).append(
                    GUIEvent(
                        "EDITOR_SELECTION",
                        target=target,
                        selection_start=start,
                        selection_end=end,
                    )
                )
            except Exception:
                pass

        self._event_queue(window).append(
            GUIEvent("CHANGE", target=target, text=value)
        )

    def _queue_editor_selection(self, window, sender):
        meta = self._control_meta(window, sender)
        if meta is None or meta[0] != "richEditor":
            return

        try:
            selected = sender.selectedRange()
            start = int(selected.location)
            end = start + int(selected.length)
        except Exception:
            return

        self._event_queue(window).append(
            GUIEvent(
                "EDITOR_SELECTION",
                target=meta[1],
                selection_start=start,
                selection_end=end,
            )
        )

    def _queue_tab_selection(self, window, sender):
        meta = self._gui_tab_buttons_by_window.get(window, {}).get(sender)
        if meta is None:
            return
        target, index = meta
        self._event_queue(window).append(
            GUIEvent("SELECTION", target=target, index=index)
        )

    def _queue_menu_activation(self, window, sender):
        target = self._gui_menu_targets_by_window.get(window, {}).get(sender)
        if target is None:
            return
        self._event_queue(window).append(
            GUIEvent("ACTIVATE", target=target)
        )

    def _queue_dialog_action(self, window, sender):
        meta = self._gui_dialog_buttons_by_window.get(window, {}).get(sender)
        if meta is None:
            return
        dialog_id, target, _panel = meta
        self.dismiss_dialog(window, dialog_id)
        self._event_queue(window).append(
            GUIEvent("ACTIVATE", target=target)
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

    def _capture_focus(self, window):
        try:
            responder = window.firstResponder()
        except Exception:
            responder = None

        meta = self._gui_control_meta_by_window.get(window, {}).get(responder)
        if meta is None:
            return None

        kind = meta[0]
        if kind in {"treeRow", "tableRow"}:
            return (kind, meta[1], meta[2])
        if kind == "treeDisclosure":
            return ("treeRow", meta[1], meta[2])
        if kind in {"textField", "textArea", "richEditor"}:
            return ("control", meta[1], None)
        return None

    def _capture_structured_focus(self, window):
        """Backward-compatible ADV-02 helper for structured-control focus."""
        previous = self._capture_focus(window)
        if previous is None or previous[0] not in {"treeRow", "tableRow"}:
            return None
        return previous

    def _restore_structured_focus(self, window, view, previous):
        """Backward-compatible ADV-02 helper for structured-control focus."""
        if previous is None:
            return
        self._restore_focus(window, view, previous)

    def _restore_focus(self, window, view, previous):
        if previous is None:
            return

        previous_kind, target, _previous_item_id = previous
        if previous_kind == "control":
            control = self._gui_controls_by_window.get(window, {}).get(target)
            if control is None:
                return
            try:
                window.makeFirstResponder_(control)
            except Exception:
                pass
            return

        desired_kind = "treeRow" if previous_kind == "treeRow" else "tableRow"

        structured_view = self._structured_view(
            window,
            target,
            "tree" if desired_kind == "treeRow" else "table",
        )
        if structured_view is None:
            return

        selected_id = structured_view.selected_id
        if selected_id is None:
            return

        control_meta = self._gui_control_meta_by_window.get(window, {})
        for native, meta in control_meta.items():
            if (
                len(meta) >= 3
                and meta[0] == desired_kind
                and meta[1] == target
                and meta[2] == selected_id
            ):
                try:
                    window.makeFirstResponder_(native)
                except Exception:
                    pass
                return

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

    def _queue_resize(self, window):
        width, height = self._content_extent(window)
        queue = self._event_queue(window)
        # Ignore intermediate drag sizes: application state needs only the
        # latest effective viewport, never a flood of stale rerenders.
        if queue and queue[-1].kind == "RESIZE":
            queue.pop()
        queue.append(GUIEvent("RESIZE", width=float(width), height=float(height)))

    def _relayout(self, window):
        view = self._gui_views_by_window.get(window)
        root = self._gui_native_roots_by_window.get(window)

        if view is None or root is None:
            return

        self._capture_split_positions(window)

        width, height = self._content_extent(window)
        positions = self._gui_split_positions_by_window.setdefault(window, {})
        self._seed_split_positions(view, positions)
        try:
            if self.platform_name == "darwin" and self._appkit_override is None:
                from ..text_layout import native_text_layout
                calculated = native_text_layout(
                    view, width, height,
                    measure_text=self.text_metrics_snapshot,
                    wrap_measure=self.measure_wrapped_text,
                    split_positions=positions,
                ).root
            else:
                calculated = layout(
                    view, width, height, split_positions=positions,
                )
        except ValueError as error:
            # A window can temporarily be smaller than its content's strict
            # intrinsic minimum while the user drags a resize handle. Keep
            # the previous valid layout instead of aborting the native event
            # loop. Recompute normally as soon as the window grows again.
            if (
                "available GUI rectangle" not in str(error)
                and "available GUI extent" not in str(error)
                and "available GUI grid extent" not in str(error)
            ):
                raise
            return

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
        parent_horizontal_inset=0.0,
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

        # Text inside a padding wrapper has real horizontal breathing room.
        # The logical estimator is font-agnostic; use AppKit's actual glyph
        # width within that reserved space instead of clipping the NSTextField.
        native_width = max(0.0, rect.width)
        if node.view.kind == "text" and parent_horizontal_inset > 0:
            try:
                measured_width = float(native.intrinsicContentSize().width)
                # Native cell insets and Retina rounding can clip glyph ink.
                # Consume only the room already reserved by padding.
                native_width = min(
                    max(native_width, measured_width + 8.0),
                    native_width + 2.0 * parent_horizontal_inset,
                )
            except (AttributeError, TypeError, ValueError):
                pass

        native.setFrame_(
            appkit.NSMakeRect(
                x,
                y,
                native_width,
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

        if node.view.kind == "collapsible":
            try:
                subviews = tuple(native.subviews())
            except Exception:
                subviews = ()
            if subviews:
                header = subviews[0]
                header.setFrame_(
                    appkit.NSMakeRect(
                        0.0,
                        max(0.0, rect.height - 32.0),
                        rect.width,
                        32.0,
                    )
                )

        if node.view.kind == "richEditor":
            try:
                text_view = native.documentView()
            except Exception:
                text_view = None

            if text_view is not None:
                content_width = max(0.0, rect.width - 14.0)
                content_height = max(0.0, rect.height)
                try:
                    layout_manager = text_view.layoutManager()
                    text_container = text_view.textContainer()
                    if text_container is not None:
                        text_container.setContainerSize_(
                            appkit.NSMakeSize(
                                max(content_width, 1.0),
                                1.0e7,
                            )
                        )
                        if hasattr(text_container, "setWidthTracksTextView_"):
                            text_container.setWidthTracksTextView_(True)

                    if hasattr(text_view, "setHorizontallyResizable_"):
                        text_view.setHorizontallyResizable_(False)
                    if hasattr(text_view, "setVerticallyResizable_"):
                        text_view.setVerticallyResizable_(True)
                    if hasattr(text_view, "setMinSize_"):
                        text_view.setMinSize_(
                            appkit.NSMakeSize(content_width, content_height)
                        )
                    if hasattr(text_view, "setMaxSize_"):
                        text_view.setMaxSize_(
                            appkit.NSMakeSize(content_width, 1.0e7)
                        )

                    used_height = content_height
                    if layout_manager is not None and text_container is not None:
                        try:
                            layout_manager.ensureLayoutForTextContainer_(
                                text_container
                            )
                            used = layout_manager.usedRectForTextContainer_(
                                text_container
                            )
                            used_height = max(
                                content_height,
                                float(used.size.height) + 16.0,
                            )
                        except Exception:
                            pass

                    text_view.setFrame_(
                        appkit.NSMakeRect(
                            0,
                            0,
                            content_width,
                            used_height,
                        )
                    )
                except Exception:
                    text_view.setFrame_(
                        appkit.NSMakeRect(
                            0,
                            0,
                            content_width,
                            content_height,
                        )
                    )

        if node.view.kind == "tree":
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
                    appkit.NSMakeRect(0, 0, content_width, content_height)
                )
                for index, row in enumerate(rows):
                    row_y = content_height - (index + 1) * row_height
                    row.setFrame_(
                        appkit.NSMakeRect(
                            0,
                            row_y,
                            content_width,
                            row_height,
                        )
                    )
                    try:
                        children = tuple(row.subviews())
                    except Exception:
                        children = ()
                    if len(children) >= 2:
                        disclosure, label = children[:2]
                        try:
                            depth = int(disclosure.tag())
                        except Exception:
                            depth = 0
                        indent = 12.0 + depth * 18.0
                        from ..tree_visuals import (
                            compact_tree_label_width,
                            tree_disclosure_column_width,
                        )
                        disclosure_width = tree_disclosure_column_width(
                            row_height
                        )
                        disclosure.setFrame_(
                            appkit.NSMakeRect(
                                indent, 0, disclosure_width, row_height,
                            )
                        )
                        available = max(
                            0.0, content_width - indent - disclosure_width
                        )
                        label_width = compact_tree_label_width(
                            str(label.title()), available
                        )
                        label.setFrame_(
                            appkit.NSMakeRect(
                                indent + disclosure_width, 0, label_width, row_height,
                            )
                        )

        if node.view.kind == "table":
            try:
                document = native.documentView()
                rows = tuple(document.subviews())
            except Exception:
                document = None
                rows = ()

            if document is not None:
                columns, table_rows = node.view.data
                header_height = 32.0
                row_height = 30.0
                available_width = max(0.0, rect.width - 14.0)
                specified = [
                    float(column.width)
                    if column.width is not None
                    else None
                    for column in columns
                ]
                fixed = sum(value for value in specified if value is not None)
                flexible_count = sum(value is None for value in specified)
                flexible_width = (
                    max(120.0, (available_width - fixed) / flexible_count)
                    if flexible_count
                    else 0.0
                )
                widths = [
                    flexible_width if value is None else value
                    for value in specified
                ]
                content_width = max(available_width, sum(widths))
                content_height = max(
                    rect.height,
                    header_height + row_height * len(table_rows),
                )
                document.setFrame_(
                    appkit.NSMakeRect(0, 0, content_width, content_height)
                )

                if rows:
                    header = rows[0]
                    header.setFrame_(
                        appkit.NSMakeRect(
                            0,
                            content_height - header_height,
                            content_width,
                            header_height,
                        )
                    )
                    try:
                        header_cells = tuple(header.subviews())
                    except Exception:
                        header_cells = ()
                    cursor = 0.0
                    for cell, width in zip(header_cells, widths):
                        cell.setFrame_(
                            appkit.NSMakeRect(cursor + 8.0, 0, max(0.0, width - 16.0), header_height)
                        )
                        cursor += width

                for row_index, row in enumerate(rows[1:]):
                    row_y = (
                        content_height
                        - header_height
                        - (row_index + 1) * row_height
                    )
                    row.setFrame_(
                        appkit.NSMakeRect(
                            0,
                            row_y,
                            content_width,
                            row_height,
                        )
                    )
                    try:
                        cells = tuple(row.subviews())
                    except Exception:
                        cells = ()
                    cursor = 0.0
                    for cell, width in zip(cells, widths):
                        # Match header cell insets; avoid text and selected
                        # cell borders touching the table's left edge.
                        inset = 8.0
                        cell.setFrame_(
                            appkit.NSMakeRect(
                                cursor + inset,
                                0,
                                max(0.0, width - inset * 2),
                                row_height,
                            )
                        )
                        cursor += width

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
                parent_horizontal_inset=(
                    float(node.view.horizontal)
                    if node.view.kind == "padding"
                    else 0.0
                ),
            )

    def close(self, window):
        for dialog_id in tuple(
            self._gui_dialogs_by_window.get(window, {})
        ):
            self.dismiss_dialog(window, dialog_id)

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
        self._gui_menu_targets_by_window.pop(window, None)
        self._gui_menu_bars_by_window.pop(window, None)
        self._gui_dialogs_by_window.pop(window, None)
        self._gui_dialog_buttons_by_window.pop(window, None)
        self._gui_dialog_controls_by_window.pop(window, None)
        self._gui_dialog_tab_buttons_by_window.pop(window, None)
        self._gui_dialog_views_by_window.pop(window, None)
        self._gui_resources_by_window.pop(window, None)
        return result

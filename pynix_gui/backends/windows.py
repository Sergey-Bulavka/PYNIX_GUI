# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Windows realization of PYNIX GUI using a private Qt/PySide6 host boundary."""

from __future__ import annotations

from collections import deque
import math
import sys
import time

from ..core import GUIEvent
from ..design import DARK, LIGHT, TYPOGRAPHY
from ..layout import layout


class WindowsGUIBackend:
    """Windows desktop backend preserving the backend-neutral PYNIX GUI contract."""

    def __init__(self, *, platform_name=None, qt=None):
        self.platform_name = sys.platform if platform_name is None else platform_name
        self._qt_override = qt
        self._application = None
        self._event_queues = {}
        self._views = {}
        self._native_roots = {}
        self._native_nodes = {}
        self._controls = {}
        self._resources = {}
        self._dialogs = {}
        self._menu_bars = {}

    def _load_qt(self):
        if self._qt_override is not None:
            return self._qt_override
        if self.platform_name != "win32":
            return None
        try:
            from PySide6 import QtCore, QtGui, QtWidgets
        except Exception:
            return None
        return type(
            "QtBundle",
            (),
            {"QtCore": QtCore, "QtGui": QtGui, "QtWidgets": QtWidgets},
        )

    def is_available(self):
        return self.platform_name == "win32" and self._load_qt() is not None

    def _app(self):
        qt = self._load_qt()
        if qt is None:
            raise OSError("Windows GUI backend is unavailable.")
        if self._application is None:
            self._application = (
                qt.QtWidgets.QApplication.instance()
                or qt.QtWidgets.QApplication([])
            )
        return qt, self._application

    def _queue(self, window):
        return self._event_queues.setdefault(window, deque())

    def open(self, title, width, height):
        qt, app = self._app()
        backend = self

        class PynixMainWindow(qt.QtWidgets.QMainWindow):
            def __init__(self):
                super().__init__()
                self._pynix_allow_close = False

            def closeEvent(self, event):
                if self._pynix_allow_close:
                    event.accept()
                    return
                backend._queue(self).append(GUIEvent("CLOSE"))
                event.ignore()

        window = PynixMainWindow()
        window.setWindowTitle(title)
        window.resize(width, height)
        window.show()
        self._event_queues[window] = deque()
        app.processEvents()
        return window

    def next_event(self, window):
        qt, app = self._app()
        queue = self._queue(window)
        while not queue:
            app.processEvents(qt.QtCore.QEventLoop.AllEvents, 50)
            time.sleep(0.005)
        return queue.popleft()

    def close(self, window):
        window._pynix_allow_close = True
        for dialog in tuple(self._dialogs.get(window, {}).values()):
            dialog.close()
        window.close()
        self._event_queues.pop(window, None)
        self._views.pop(window, None)
        self._native_roots.pop(window, None)
        self._native_nodes.pop(window, None)
        self._controls.pop(window, None)
        self._resources.pop(window, None)
        self._dialogs.pop(window, None)
        self._menu_bars.pop(window, None)

    def set_resources(self, window, catalog):
        self._resources[window] = catalog

    @staticmethod
    def _palette_for(theme):
        return DARK if theme == "dark" else LIGHT

    def _stylesheet(self, theme):
        p = self._palette_for(theme)
        return f"""
            QWidget {{
                color: {p["textPrimary"]};
                background: {p["background"]};
            }}
            QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QTreeWidget, QTableWidget {{
                background: {p["surfaceSunken"]};
                border: 1px solid {p["border"]};
                selection-background-color: {p["surfaceSelected"]};
                selection-color: {p["textPrimary"]};
            }}
            QPushButton {{
                background: {p["surfaceRaised"]};
                border: 1px solid {p["borderStrong"]};
                padding: 4px 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{ background: {p["surfaceHover"]}; }}
            QToolTip {{
                color: {p["textPrimary"]};
                background: {p["surfaceRaised"]};
                border: 1px solid {p["border"]};
            }}
        """

    @staticmethod
    def _theme_of(view, inherited="light"):
        if view.kind == "theme":
            return "dark" if view.theme == "dark" else "light"
        return inherited

    def render(self, window, view):
        qt, app = self._app()
        old = window.centralWidget()
        if old is not None:
            old.setParent(None)
            old.deleteLater()

        nodes = {}
        controls = {}
        root = self._build(qt, window, view, None, nodes, controls, "light", ())
        window.setCentralWidget(root)

        self._views[window] = view
        self._native_roots[window] = root
        self._native_nodes[window] = nodes
        self._controls[window] = controls

        calculated = layout(
            view,
            max(1, window.centralWidget().width()),
            max(1, window.centralWidget().height()),
        )
        self._apply_geometry(calculated, nodes, None, ())
        root.show()
        app.processEvents()

    def _font(self, qt, role):
        size, weight = TYPOGRAPHY.get(role, TYPOGRAPHY["body"])
        font = qt.QtGui.QFont()
        font.setPointSizeF(size)
        if weight == "monospace":
            font.setFamilies(["Cascadia Mono", "Consolas", "Courier New"])
            font.setStyleHint(qt.QtGui.QFont.Monospace)
        elif weight in {"semibold", "bold"}:
            font.setWeight(
                qt.QtGui.QFont.Bold
                if weight == "bold"
                else qt.QtGui.QFont.DemiBold
            )
        elif weight == "medium":
            font.setWeight(qt.QtGui.QFont.Medium)
        return font

    def _generic(self, qt, parent):
        return qt.QtWidgets.QWidget(parent)

    def _build(self, qt, window, view, parent, nodes, controls, theme, path):
        theme = self._theme_of(view, theme)
        kind = view.kind
        W = qt.QtWidgets

        if kind == "text":
            native = W.QLabel(view.text, parent)
            native.setFont(self._font(qt, view.role))
        elif kind == "button":
            native = W.QPushButton(view.text, parent)
            native.clicked.connect(
                lambda _checked=False, target=view.target:
                    self._queue(window).append(GUIEvent("ACTIVATE", target=target))
            )
            controls[view.target] = native
        elif kind == "textField":
            native = W.QLineEdit(parent)
            native.setText(view.value)
            native.setPlaceholderText(view.placeholder)
            native.editingFinished.connect(
                lambda target=view.target, widget=native:
                    self._queue(window).append(
                        GUIEvent("CHANGE", target=target, text=widget.text())
                    )
            )
            controls[view.target] = native
        elif kind == "textArea":
            native = W.QTextEdit(parent)
            native.setPlainText(view.value)
            native.textChanged.connect(
                lambda target=view.target, widget=native:
                    self._queue_rich_editor_change(window, target, widget)
            )
            controls[view.target] = native
        elif kind == "richEditor":
            native = W.QPlainTextEdit(parent)
            native.setPlainText(view.value)
            native.setReadOnly(view.read_only)
            native.setFont(self._font(qt, "code"))
            cursor = native.textCursor()
            cursor.setPosition(view.selection_start)
            cursor.setPosition(
                view.selection_end,
                qt.QtGui.QTextCursor.KeepAnchor,
            )
            native.setTextCursor(cursor)
            native.textChanged.connect(
                lambda target=view.target, widget=native:
                    self._queue(window).append(
                        GUIEvent("CHANGE", target=target, text=widget.toPlainText())
                    )
            )
            native.selectionChanged.connect(
                lambda target=view.target, widget=native:
                    self._queue_editor_selection(window, target, widget)
            )
            self._apply_editor_spans(qt, native, view, theme)
            controls[view.target] = native
        elif kind in {"checkBox", "radioButton"}:
            native = (
                W.QCheckBox(view.text, parent)
                if kind == "checkBox"
                else W.QRadioButton(view.text, parent)
            )
            native.setChecked(bool(view.checked))
            native.toggled.connect(
                lambda checked, target=view.target, k=kind:
                    self._queue(window).append(
                        GUIEvent(
                            "CHANGE" if k == "checkBox" else "SELECTION",
                            target=target,
                            checked=checked if k == "checkBox" else None,
                            index=None if k == "checkBox" else 0,
                        )
                    )
            )
            controls[view.target] = native
        elif kind == "comboBox":
            native = W.QComboBox(parent)
            native.addItems(list(view.items))
            native.setCurrentIndex(view.selected)
            native.currentIndexChanged.connect(
                lambda index, target=view.target:
                    self._queue(window).append(
                        GUIEvent("SELECTION", target=target, index=int(index))
                    )
            )
            controls[view.target] = native
        elif kind == "slider":
            native = W.QSlider(qt.QtCore.Qt.Horizontal, parent)
            native.setMinimum(int(round(view.minimum_number * 1000)))
            native.setMaximum(int(round(view.maximum_number * 1000)))
            native.setValue(int(round(view.number * 1000)))
            native.sliderReleased.connect(
                lambda target=view.target, widget=native:
                    self._queue(window).append(
                        GUIEvent("CHANGE", target=target, number=float(widget.value()) / 1000.0)
                    )
            )
            controls[view.target] = native
        elif kind == "progressBar":
            native = W.QProgressBar(parent)
            native.setMinimum(0)
            native.setMaximum(1000)
            ratio = (
                (view.number - view.minimum_number)
                / (view.maximum_number - view.minimum_number)
            )
            native.setValue(int(max(0.0, min(1.0, ratio)) * 1000))
        elif kind == "list":
            native = W.QListWidget(parent)
            native.addItems(list(view.items))
            if view.selected >= 0:
                native.setCurrentRow(view.selected)
            native.currentRowChanged.connect(
                lambda index, target=view.target:
                    self._queue(window).append(
                        GUIEvent("SELECTION", target=target, index=int(index))
                    )
            )
            controls[view.target] = native
        elif kind == "tree":
            native = W.QTreeWidget(parent)
            native.setHeaderHidden(True)
            by_id = {}
            def add_tree(nodes_values, parent_item=None):
                for node in nodes_values:
                    item = W.QTreeWidgetItem([node.label])
                    item.setData(0, qt.QtCore.Qt.UserRole, node.node_id)
                    by_id[node.node_id] = item
                    if parent_item is None:
                        native.addTopLevelItem(item)
                    else:
                        parent_item.addChild(item)
                    add_tree(node.children, item)
            add_tree(view.data)
            for item_id in view.expanded_ids:
                if item_id in by_id:
                    by_id[item_id].setExpanded(True)
            if view.selected_id in by_id:
                native.setCurrentItem(by_id[view.selected_id])
            native.currentItemChanged.connect(
                lambda current, previous, target=view.target:
                    self._tree_selected(window, target, current, qt)
            )
            native.itemExpanded.connect(
                lambda item, target=view.target:
                    self._tree_expanded(window, target, item, True, qt)
            )
            native.itemCollapsed.connect(
                lambda item, target=view.target:
                    self._tree_expanded(window, target, item, False, qt)
            )
            controls[view.target] = native
        elif kind == "table":
            columns, rows = view.data
            native = W.QTableWidget(len(rows), len(columns), parent)
            native.setHorizontalHeaderLabels([column.title for column in columns])
            for column_index, column in enumerate(columns):
                if column.width is not None:
                    native.setColumnWidth(column_index, column.width)
            for row_index, row in enumerate(rows):
                for column_index, cell in enumerate(row.cells):
                    item = W.QTableWidgetItem(cell)
                    item.setData(qt.QtCore.Qt.UserRole, row.row_id)
                    alignment = {
                        "start": qt.QtCore.Qt.AlignLeft,
                        "center": qt.QtCore.Qt.AlignHCenter,
                        "end": qt.QtCore.Qt.AlignRight,
                    }[columns[column_index].alignment]
                    item.setTextAlignment(alignment | qt.QtCore.Qt.AlignVCenter)
                    native.setItem(row_index, column_index, item)
                if row.row_id == view.selected_id:
                    native.selectRow(row_index)
            native.setSelectionBehavior(W.QAbstractItemView.SelectRows)
            native.setSelectionMode(W.QAbstractItemView.SingleSelection)
            native.itemSelectionChanged.connect(
                lambda target=view.target, widget=native:
                    self._table_selected(window, target, widget, qt)
            )
            controls[view.target] = native
        elif kind == "canvas":
            native = self._canvas_widget(qt, window, view.canvas_scene, theme, parent)
            controls[view.target] = native
        elif kind == "vectorIcon":
            catalog = self._resources.get(window)
            scene = None if catalog is None else catalog.vector_scene(view.resource)
            native = (
                self._canvas_widget(qt, window, scene, theme, parent)
                if scene is not None
                else W.QLabel(parent)
            )
        elif kind in {"icon", "image"}:
            native = W.QLabel(parent)
            native.setAlignment(qt.QtCore.Qt.AlignCenter)
            path_value = view.resource
            if kind == "image":
                catalog = self._resources.get(window)
                logical = None if catalog is None else catalog.image_path(view.resource)
                if logical is not None:
                    path_value = logical
            pixmap = qt.QtGui.QPixmap(path_value)
            if not pixmap.isNull():
                native.setPixmap(pixmap)
                native.setScaledContents(True)
        elif kind == "collapsible":
            native = self._generic(qt, parent)
            header = W.QToolButton(native)
            header.setText(view.text)
            header.setCheckable(True)
            header.setChecked(bool(view.checked))
            header.setToolButtonStyle(qt.QtCore.Qt.ToolButtonTextBesideIcon)
            header.setArrowType(
                qt.QtCore.Qt.DownArrow if view.checked else qt.QtCore.Qt.RightArrow
            )
            header.clicked.connect(
                lambda checked, target=view.target:
                    self._queue(window).append(
                        GUIEvent("CHANGE", target=target, checked=bool(checked))
                    )
            )
            header.setGeometry(0, 0, 240, 32)
            if view.checked:
                child = self._build(
                    qt, window, view.children[0], native, nodes, controls,
                    theme, path + (0,),
                )
                child.show()
            controls[view.target] = header
        elif kind == "tabs":
            native = W.QTabWidget(parent)
            for index, child_view in enumerate(view.children):
                page = self._build(
                    qt, window, child_view, None, nodes, controls,
                    theme, path + (index,),
                )
                native.addTab(page, view.labels[index])
            native.setCurrentIndex(view.selected)
            native.currentChanged.connect(
                lambda index, target=view.container_id:
                    self._queue(window).append(
                        GUIEvent("SELECTION", target=target, index=int(index))
                    )
            )
        elif kind == "tooltip":
            native = self._generic(qt, parent)
            child = self._build(
                qt, window, view.children[0], native, nodes, controls,
                theme, path + (0,),
            )
            native.setToolTip(view.tooltip_text)
            child.setToolTip(view.tooltip_text)
        elif kind == "draggable":
            native = self._drag_widget(qt, window, view, parent)
            self._build(
                qt, window, view.children[0], native, nodes, controls,
                theme, path + (0,),
            )
        elif kind in {"dropTarget", "dockTarget"}:
            native = self._drop_widget(qt, window, view, parent)
            self._build(
                qt, window, view.children[0], native, nodes, controls,
                theme, path + (0,),
            )
        elif kind in {
            "empty", "spacer", "separator", "row", "column", "grid", "stack",
            "fill", "minSize", "preferredSize", "maxSize", "align", "padding",
            "scroll", "panel", "group", "toolbar", "statusBar", "enabled",
            "focused", "theme", "contextMenu", "dockWorkspace",
            "horizontalSplit", "verticalSplit",
        }:
            native = self._generic(qt, parent)
            for index, child_view in enumerate(view.children):
                self._build(
                    qt, window, child_view, native, nodes, controls,
                    theme, path + (index,),
                )
            if kind == "enabled":
                native.setEnabled(bool(view.enabled))
            if kind in {"panel", "group", "toolbar", "statusBar"}:
                native.setAutoFillBackground(True)
        else:
            native = self._generic(qt, parent)

        nodes[path] = native
        native.setStyleSheet(self._stylesheet(theme))
        return native

    def _apply_geometry(self, node, nodes, parent_rect, path):
        native = nodes[path]
        rect = node.rect
        if parent_rect is None:
            x, y = 0, 0
        else:
            x = int(round(rect.x - parent_rect.x))
            y = int(round(rect.y - parent_rect.y))
        native.setGeometry(
            x,
            y,
            max(0, int(round(rect.width))),
            max(0, int(round(rect.height))),
        )
        for index, child in enumerate(node.children):
            self._apply_geometry(
                child,
                nodes,
                rect,
                path + (index,),
            )

    def _queue_rich_editor_change(self, window, target, widget):
        cursor = widget.textCursor()
        start = min(cursor.anchor(), cursor.position())
        end = max(cursor.anchor(), cursor.position())
        self._queue(window).append(
            GUIEvent(
                "EDITOR_SELECTION",
                target=target,
                selection_start=int(start),
                selection_end=int(end),
            )
        )
        self._queue(window).append(
            GUIEvent(
                "CHANGE",
                target=target,
                text=widget.toPlainText(),
            )
        )

    def _queue_editor_selection(self, window, target, widget):
        cursor = widget.textCursor()
        start = min(cursor.anchor(), cursor.position())
        end = max(cursor.anchor(), cursor.position())
        self._queue(window).append(
            GUIEvent(
                "EDITOR_SELECTION",
                target=target,
                selection_start=int(start),
                selection_end=int(end),
            )
        )

    def _apply_editor_spans(self, qt, widget, view, theme):
        palette = self._palette_for(theme)
        color_roles = {
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
        selections = []
        document = widget.document()
        for span in view.spans:
            selection = qt.QtWidgets.QTextEdit.ExtraSelection()
            cursor = qt.QtGui.QTextCursor(document)
            cursor.setPosition(span.start)
            cursor.setPosition(span.end, qt.QtGui.QTextCursor.KeepAnchor)
            selection.cursor = cursor
            selection.format.setForeground(
                qt.QtGui.QColor(palette[color_roles[span.role]])
            )
            if span.role == "strong":
                selection.format.setFontWeight(qt.QtGui.QFont.Bold)
            selections.append(selection)
        widget.setExtraSelections(selections)

    def _tree_selected(self, window, target, item, qt):
        if item is None:
            return
        item_id = item.data(0, qt.QtCore.Qt.UserRole)
        if item_id:
            self._queue(window).append(
                GUIEvent("SELECTION", target=target, item_id=str(item_id))
            )

    def _tree_expanded(self, window, target, item, checked, qt):
        item_id = item.data(0, qt.QtCore.Qt.UserRole)
        if item_id:
            self._queue(window).append(
                GUIEvent(
                    "EXPANSION",
                    target=target,
                    item_id=str(item_id),
                    checked=bool(checked),
                )
            )

    def _table_selected(self, window, target, widget, qt):
        row = widget.currentRow()
        if row < 0:
            return
        item = widget.item(row, 0)
        if item is None:
            return
        item_id = item.data(qt.QtCore.Qt.UserRole)
        if item_id:
            self._queue(window).append(
                GUIEvent("SELECTION", target=target, item_id=str(item_id))
            )

    def _canvas_widget(self, qt, window, scene, theme, parent):
        backend = self

        class CanvasWidget(qt.QtWidgets.QWidget):
            def paintEvent(self, event):
                if scene is None:
                    return
                painter = qt.QtGui.QPainter(self)
                try:
                    painter.setRenderHint(qt.QtGui.QPainter.Antialiasing, True)
                    sx = self.width() / scene.width
                    sy = self.height() / scene.height
                    painter.scale(sx, sy)
                    backend._paint_canvas_qt(qt, painter, scene.commands, theme)
                finally:
                    painter.end()

            def mousePressEvent(self, event):
                if scene is None:
                    return
                target = backend._canvas_hit_qt(
                    scene,
                    float(event.position().x()),
                    float(event.position().y()),
                    float(self.width()),
                    float(self.height()),
                )
                if target is not None:
                    backend._queue(window).append(
                        GUIEvent("ACTIVATE", target=target)
                    )

        return CanvasWidget(parent)

    def _paint_canvas_qt(self, qt, painter, commands, theme):
        palette = self._palette_for(theme)
        for command in commands:
            if command.kind == "transform":
                painter.save()
                dx, dy, sx, sy, rotation = command.values
                painter.translate(dx, dy)
                painter.scale(sx, sy)
                painter.rotate(rotation)
                self._paint_canvas_qt(qt, painter, command.children, theme)
                painter.restore()
                continue
            if command.kind == "clip":
                painter.save()
                x, y, width, height = command.values
                painter.setClipRect(qt.QtCore.QRectF(x, y, width, height))
                self._paint_canvas_qt(qt, painter, command.children, theme)
                painter.restore()
                continue

            pen = qt.QtCore.Qt.NoPen
            if command.stroke_role is not None:
                pen = qt.QtGui.QPen(
                    qt.QtGui.QColor(palette.get(command.stroke_role, palette["textPrimary"]))
                )
                pen.setWidthF(float(command.line_width))
            brush = qt.QtCore.Qt.NoBrush
            if command.fill_role is not None:
                brush = qt.QtGui.QBrush(
                    qt.QtGui.QColor(palette.get(command.fill_role, palette["surface"]))
                )
            painter.setPen(pen)
            painter.setBrush(brush)

            if command.kind == "line":
                painter.drawLine(qt.QtCore.QLineF(*command.values))
            elif command.kind == "rect":
                painter.drawRect(qt.QtCore.QRectF(*command.values))
            elif command.kind == "ellipse":
                painter.drawEllipse(qt.QtCore.QRectF(*command.values))
            elif command.kind == "path":
                closed = command.values[0]
                values = command.values[1:]
                path = qt.QtGui.QPainterPath()
                path.moveTo(values[0], values[1])
                for i in range(2, len(values), 2):
                    path.lineTo(values[i], values[i + 1])
                if closed:
                    path.closeSubpath()
                painter.drawPath(path)
            elif command.kind == "text":
                x, y, value = command.values
                painter.setPen(
                    qt.QtGui.QColor(
                        palette.get(command.fill_role or "textPrimary", palette["textPrimary"])
                    )
                )
                painter.setFont(self._font(qt, command.text_role or "body"))
                painter.drawText(qt.QtCore.QPointF(x, y), value)
            elif command.kind == "image":
                x, y, width, height = command.values
                pixmap = qt.QtGui.QPixmap(command.resource)
                painter.drawPixmap(qt.QtCore.QRectF(x, y, width, height), pixmap, pixmap.rect())

    @staticmethod
    def _canvas_hit_qt(scene, x, y, width, height):
        if width <= 0 or height <= 0:
            return None
        lx = x * scene.width / width
        ly = y * scene.height / height
        for command in reversed(scene.commands):
            if command.hit_target is None:
                continue
            if command.kind in {"rect", "ellipse", "image"}:
                rx, ry, rw, rh = command.values[:4]
                if rx <= lx <= rx + rw and ry <= ly <= ry + rh:
                    return command.hit_target
        return None

    def _drag_widget(self, qt, window, view, parent):
        backend = self

        class DragWidget(qt.QtWidgets.QWidget):
            def mouseMoveEvent(self, event):
                if not (event.buttons() & qt.QtCore.Qt.LeftButton):
                    return
                drag = qt.QtGui.QDrag(self)
                mime = qt.QtCore.QMimeData()
                payload = view.drag_payload
                mime.setData(
                    "application/x-pynix-gui",
                    (
                        f"{view.drag_source_id}\n{payload.kind}\n{payload.value}\n"
                        + ",".join(payload.operations)
                    ).encode("utf-8"),
                )
                drag.setMimeData(mime)
                allowed = qt.QtCore.Qt.IgnoreAction
                if "copy" in payload.operations:
                    allowed |= qt.QtCore.Qt.CopyAction
                if "move" in payload.operations:
                    allowed |= qt.QtCore.Qt.MoveAction
                drag.exec(allowed)

        return DragWidget(parent)

    def _drop_widget(self, qt, window, view, parent):
        backend = self

        class DropWidget(qt.QtWidgets.QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setAcceptDrops(True)

            def _decode(self, event):
                mime = event.mimeData()
                if not mime.hasFormat("application/x-pynix-gui"):
                    return None
                try:
                    parts = bytes(mime.data("application/x-pynix-gui")).decode("utf-8").split("\n")
                    source_id, kind, value, operations = parts
                    operations = tuple(v for v in operations.split(",") if v)
                    return source_id, kind, value, operations
                except Exception:
                    return None

            def dragEnterEvent(self, event):
                decoded = self._decode(event)
                if decoded is None:
                    event.ignore()
                    return
                _source, kind, _value, operations = decoded
                if kind not in view.accepted_kinds:
                    event.ignore()
                    return
                if not set(operations).intersection(view.accepted_operations):
                    event.ignore()
                    return
                event.acceptProposedAction()

            def dropEvent(self, event):
                decoded = self._decode(event)
                if decoded is None:
                    event.ignore()
                    return
                source_id, kind, value, operations = decoded
                operation = (
                    "move"
                    if "move" in operations and "move" in view.accepted_operations
                    else "copy"
                )
                if view.kind == "dockTarget":
                    backend._queue(window).append(
                        GUIEvent(
                            "DOCK",
                            target=view.drop_target_id,
                            item_id=value,
                            region=view.dock_region,
                        )
                    )
                else:
                    backend._queue(window).append(
                        GUIEvent(
                            "DROP",
                            target=view.drop_target_id,
                            source_id=source_id,
                            payload_kind=kind,
                            payload_value=value,
                            operation=operation,
                        )
                    )
                event.acceptProposedAction()

        return DropWidget(parent)

    def set_menu_bar(self, window, menu_bar):
        qt, app = self._app()
        native = window.menuBar()
        native.clear()

        def add_menu(parent, menu_value):
            menu = parent.addMenu(menu_value.title)
            for item in menu_value.items:
                if item.kind == "separator":
                    menu.addSeparator()
                    continue
                if item.kind == "submenu":
                    add_menu(menu, item.submenu)
                    continue
                action = menu.addAction(item.label)
                action.setEnabled(item.enabled)
                action.setCheckable(item.checked)
                action.setChecked(item.checked)
                if item.shortcut is not None:
                    modifiers = {
                        "primary": "Ctrl",
                        "shift": "Shift",
                        "alt": "Alt",
                        "control": "Ctrl",
                    }
                    parts = [modifiers[v] for v in item.shortcut.modifiers]
                    parts.append(item.shortcut.key)
                    action.setShortcut(qt.QtGui.QKeySequence("+".join(parts)))
                action.triggered.connect(
                    lambda checked=False, target=item.target:
                        self._queue(window).append(
                            GUIEvent("ACTIVATE", target=target)
                        )
                )
            return menu

        for menu_value in menu_bar.menus:
            add_menu(native, menu_value)
        self._menu_bars[window] = native

    def clear_menu_bar(self, window):
        bar = window.menuBar()
        bar.clear()
        self._menu_bars.pop(window, None)

    def present_dialog(self, window, dialog):
        qt, app = self._app()
        native = qt.QtWidgets.QDialog(window)
        native.setWindowTitle(dialog.title)
        native.resize(560, 360)
        layout_box = qt.QtWidgets.QVBoxLayout(native)

        nodes = {}
        controls = {}
        content = self._build(
            qt, window, dialog.content, native, nodes, controls, "light", ()
        )
        layout_box.addWidget(content)

        buttons = qt.QtWidgets.QDialogButtonBox(native)
        for action in dialog.actions:
            role = (
                qt.QtWidgets.QDialogButtonBox.AcceptRole
                if action.role == "primary"
                else qt.QtWidgets.QDialogButtonBox.RejectRole
            )
            button = buttons.addButton(action.label, role)
            button.setEnabled(action.enabled)
            if action.default:
                button.setDefault(True)
            button.clicked.connect(
                lambda checked=False, target=action.target, dialog_id=dialog.dialog_id:
                    self._dialog_action(window, dialog_id, target)
            )
        layout_box.addWidget(buttons)

        self._dialogs.setdefault(window, {})[dialog.dialog_id] = native
        native.setModal(True)
        native.show()

    def _dialog_action(self, window, dialog_id, target):
        self.dismiss_dialog(window, dialog_id)
        self._queue(window).append(GUIEvent("ACTIVATE", target=target))

    def dismiss_dialog(self, window, dialog_id):
        native = self._dialogs.get(window, {}).pop(dialog_id, None)
        if native is not None:
            native.close()

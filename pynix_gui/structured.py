# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Platform-independent structured data models for Tree and Table."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from .core import GUIError


def _non_empty(value, label: str) -> str:
    if type(value) is not str or value == "":
        raise GUIError("PYNIX-GUI-009", f"{label} must be a non-empty String.")
    return value


def _sequence(value, label: str) -> tuple:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise GUIError("PYNIX-GUI-009", f"{label} must be a sequence.")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class GUITreeNode:
    node_id: str
    label: str
    children: tuple["GUITreeNode", ...] = ()
    kind: str = "auto"

    def __post_init__(self):
        _non_empty(self.node_id, "GUI tree node id")
        if self.kind not in {"auto", "folder", "file"}:
            raise GUIError("PYNIX-GUI-009", "GUI tree node kind must be auto, folder or file.")
        if type(self.label) is not str:
            raise GUIError("PYNIX-GUI-009", "GUI tree node label must be String.")
        if type(self.children) is not tuple or any(
            not isinstance(child, GUITreeNode) for child in self.children
        ):
            raise GUIError("PYNIX-GUI-009", "GUI tree node children are invalid.")


@dataclass(frozen=True, slots=True)
class GUITableColumn:
    column_id: str
    title: str
    width: int | None = None
    alignment: str = "start"

    def __post_init__(self):
        _non_empty(self.column_id, "GUI table column id")
        if type(self.title) is not str:
            raise GUIError("PYNIX-GUI-009", "GUI table column title must be String.")
        if self.width is not None and (
            type(self.width) is not int or self.width <= 0
        ):
            raise GUIError("PYNIX-GUI-009", "GUI table column width must be a positive Int.")
        if self.alignment not in {"start", "center", "end"}:
            raise GUIError("PYNIX-GUI-009", "GUI table column alignment is invalid.")


@dataclass(frozen=True, slots=True)
class GUITableRow:
    row_id: str
    cells: tuple[str, ...]

    def __post_init__(self):
        _non_empty(self.row_id, "GUI table row id")
        if type(self.cells) is not tuple or any(
            type(cell) is not str for cell in self.cells
        ):
            raise GUIError("PYNIX-GUI-009", "GUI table row cells must be Strings.")


def tree_node(node_id: str, label: str, children=(), *, kind="auto") -> GUITreeNode:
    child_values = _sequence(children, "GUI tree node children")
    return GUITreeNode(node_id, label, child_values, kind)


def table_column(
    column_id: str,
    title: str,
    width: int | None = None,
    alignment="start",
) -> GUITableColumn:
    return GUITableColumn(column_id, title, width, alignment)


def table_row(row_id: str, cells) -> GUITableRow:
    return GUITableRow(row_id, _sequence(cells, "GUI table row cells"))


def flatten_tree(nodes) -> tuple[GUITreeNode, ...]:
    values = _sequence(nodes, "GUI tree nodes")
    if any(not isinstance(node, GUITreeNode) for node in values):
        raise GUIError("PYNIX-GUI-009", "GUI tree nodes are invalid.")

    result = []
    seen = set()

    def visit(node):
        if node.node_id in seen:
            raise GUIError("PYNIX-GUI-009", "GUI tree node ids must be unique.")
        seen.add(node.node_id)
        result.append(node)
        for child in node.children:
            visit(child)

    for node in values:
        visit(node)

    return tuple(result)


def validate_tree_state(nodes, expanded_ids=(), selected_id=None):
    flat = flatten_tree(nodes)
    identities = {node.node_id for node in flat}

    expanded = _sequence(expanded_ids, "GUI tree expanded ids")
    if any(type(value) is not str or value == "" for value in expanded):
        raise GUIError("PYNIX-GUI-009", "GUI tree expanded ids must be non-empty Strings.")
    if len(set(expanded)) != len(expanded):
        raise GUIError("PYNIX-GUI-009", "GUI tree expanded ids must be unique.")
    if any(value not in identities for value in expanded):
        raise GUIError("PYNIX-GUI-009", "GUI tree expanded id does not exist.")

    if selected_id is not None:
        _non_empty(selected_id, "GUI tree selected id")
        if selected_id not in identities:
            raise GUIError("PYNIX-GUI-009", "GUI tree selected id does not exist.")

    return tuple(nodes), tuple(expanded), selected_id


def validate_table_state(columns, rows, selected_id=None):
    column_values = _sequence(columns, "GUI table columns")
    row_values = _sequence(rows, "GUI table rows")

    if not column_values:
        raise GUIError("PYNIX-GUI-009", "GUI table requires at least one column.")
    if any(not isinstance(column, GUITableColumn) for column in column_values):
        raise GUIError("PYNIX-GUI-009", "GUI table columns are invalid.")
    if any(not isinstance(row, GUITableRow) for row in row_values):
        raise GUIError("PYNIX-GUI-009", "GUI table rows are invalid.")

    column_ids = [column.column_id for column in column_values]
    if len(set(column_ids)) != len(column_ids):
        raise GUIError("PYNIX-GUI-009", "GUI table column ids must be unique.")

    row_ids = [row.row_id for row in row_values]
    if len(set(row_ids)) != len(row_ids):
        raise GUIError("PYNIX-GUI-009", "GUI table row ids must be unique.")

    for row in row_values:
        if len(row.cells) != len(column_values):
            raise GUIError(
                "PYNIX-GUI-009",
                "GUI table row cell count must equal column count.",
            )

    if selected_id is not None:
        _non_empty(selected_id, "GUI table selected id")
        if selected_id not in set(row_ids):
            raise GUIError("PYNIX-GUI-009", "GUI table selected id does not exist.")

    return tuple(column_values), tuple(row_values), selected_id

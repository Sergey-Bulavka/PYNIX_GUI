# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import (
    GUIError,
    GUIEvent,
    table,
    table_column,
    table_row,
    tree,
    tree_node,
    validate_view,
)
from pynix_gui.backends import MacOSGUIBackend
from pynix_gui.layout import measure


def sample_tree():
    return [
        tree_node(
            "src",
            "src",
            [
                tree_node("main", "main.pnx"),
                tree_node(
                    "ui",
                    "ui",
                    [
                        tree_node("window", "window.pnx"),
                    ],
                ),
            ],
        ),
        tree_node("readme", "README.md"),
    ]


def sample_columns():
    return [
        table_column("name", "Name", 220),
        table_column("kind", "Kind", 120),
        table_column("size", "Size", 90, "end"),
    ]


def sample_rows():
    return [
        table_row("r1", ["main.pnx", "PYNIX", "4 KB"]),
        table_row("r2", ["window.pnx", "PYNIX", "9 KB"]),
    ]


def test_adv02_tree_nodes_require_globally_unique_identity():
    duplicate = [
        tree_node("same", "A"),
        tree_node("root", "Root", [tree_node("same", "B")]),
    ]

    with pytest.raises(GUIError) as failure:
        tree("project", duplicate)

    assert failure.value.code == "PYNIX-GUI-009"


def test_adv02_tree_controlled_expansion_and_selection_validate_identity():
    view = tree(
        "project",
        sample_tree(),
        expanded_ids=["src", "ui"],
        selected_id="window",
    )

    assert view.expanded_ids == ("src", "ui")
    assert view.selected_id == "window"
    validate_view(view)

    with pytest.raises(GUIError):
        tree("project", sample_tree(), expanded_ids=["missing"])


def test_adv02_tree_selection_event_uses_stable_item_id():
    event = GUIEvent("SELECTION", target="project", item_id="window")

    assert event.item_id == "window"
    assert event.index is None


def test_adv02_tree_expansion_event_carries_identity_and_state():
    event = GUIEvent(
        "EXPANSION",
        target="project",
        item_id="src",
        checked=False,
    )

    assert event.item_id == "src"
    assert event.checked is False


def test_adv02_table_requires_unique_columns_rows_and_complete_cells():
    with pytest.raises(GUIError):
        table(
            "files",
            [
                table_column("name", "Name"),
                table_column("name", "Again"),
            ],
            sample_rows(),
        )

    with pytest.raises(GUIError):
        table(
            "files",
            sample_columns(),
            [table_row("bad", ["only one"])],
        )

    with pytest.raises(GUIError):
        table(
            "files",
            sample_columns(),
            [
                table_row("same", ["A", "B", "C"]),
                table_row("same", ["D", "E", "F"]),
            ],
        )


def test_adv02_table_controlled_selection_uses_row_identity():
    view = table(
        "files",
        sample_columns(),
        sample_rows(),
        selected_id="r2",
    )

    assert view.selected_id == "r2"
    assert view.data[1][1].row_id == "r2"
    validate_view(view)


def test_adv02_tree_and_table_have_professional_default_geometry():
    tree_size = measure(tree("project", sample_tree()))
    table_size = measure(table("files", sample_columns(), sample_rows()))

    assert tree_size.minimum.width == 180
    assert tree_size.preferred.height == 260
    assert table_size.minimum.width == 260
    assert table_size.preferred.width == 520
    assert table_size.preferred.height == 280


def test_adv02_existing_index_selection_event_remains_compatible():
    event = GUIEvent("SELECTION", target="legacy-list", index=2)

    assert event.index == 2
    assert event.item_id is None


def test_adv02_macos_backend_normalizes_tree_selection_and_expansion():
    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    window = object()
    select_sender = object()
    expand_sender = object()

    backend._gui_control_meta_by_window[window] = {
        select_sender: ("treeRow", "project", "main"),
        expand_sender: ("treeDisclosure", "project", "src", True),
    }

    backend._queue_control_change(window, select_sender)
    backend._queue_control_change(window, expand_sender)

    first = backend._event_queue(window).popleft()
    second = backend._event_queue(window).popleft()

    assert first == GUIEvent("SELECTION", target="project", item_id="main")
    assert second == GUIEvent(
        "EXPANSION",
        target="project",
        item_id="src",
        checked=False,
    )


def test_adv02_macos_backend_normalizes_table_row_selection():
    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    window = object()
    sender = object()

    backend._gui_control_meta_by_window[window] = {
        sender: ("tableRow", "files", "r2"),
    }

    backend._queue_control_change(window, sender)
    event = backend._event_queue(window).popleft()

    assert event == GUIEvent("SELECTION", target="files", item_id="r2")

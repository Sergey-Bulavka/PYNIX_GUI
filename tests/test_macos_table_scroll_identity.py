# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for stable semantic table identities during rerender."""

from pynix_gui import column, table, table_column, table_row
from pynix_gui.backends.macos import MacOSGUIBackend


def _screen(names):
    return column([
        table(
            "project-files",
            [table_column("name", "Name", 260)],
            [table_row(name, [name]) for name in names],
            selected_id=names[0] if names else None,
        ),
    ])


def test_table_identity_ignores_selection_but_not_listing():
    before = _screen(["a", "b"])
    after = _screen(["a", "b"])
    replaced = _screen(["c", "d"])
    ids = MacOSGUIBackend._table_id_sequences
    assert ids(before) == ids(after)
    assert ids(before) != ids(replaced)
    assert ids(before)["project-files"] == ("a", "b")


def test_table_identity_changes_when_rows_reorder():
    ids = MacOSGUIBackend._table_id_sequences
    assert ids(_screen(["a", "b"])) != ids(_screen(["b", "a"]))

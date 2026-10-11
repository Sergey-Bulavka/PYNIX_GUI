# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from pynix_gui.core import validate_view
from pynix_gui.ide_components import (
    METRICS, ide_command_bar, ide_editor_tab_strip,
    ide_tool_window_header, ide_status_strip,
)


def test_design_metrics_have_stable_reference_dimensions():
    assert METRICS.activity_width == 48
    assert METRICS.explorer_width == 256
    assert METRICS.editor_tabs_height == 36


def test_ide_compositions_validate_independently():
    for view in (
        ide_command_bar("PYNIX / workspace"),
        ide_editor_tab_strip(["main.pnx", "gui.pnx"], "main.pnx"),
        ide_tool_window_header("Terminal"),
        ide_status_strip("Ready", "main.pnx"),
    ):
        validate_view(view)


def test_ide_tab_strip_reflects_active_tab():
    first = ide_editor_tab_strip(["main.pnx", "gui.pnx"], "main.pnx")
    second = ide_editor_tab_strip(["main.pnx", "gui.pnx"], "gui.pnx")
    assert first != second

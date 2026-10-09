# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from dataclasses import replace

from pynix_gui import column, grid, padding, row, text
from pynix_gui.height_for_width import height_for_width
from pynix_gui.wrap_engine import wrap_text


def wrapped(value):
    # Internal preflight view; public overflow='wrap' remains gated until
    # the real layout pass uses the computed heights.
    return replace(text(value, overflow="ellipsis"), overflow="wrap")


def measure_lines(role, value, width):
    return wrap_text(
        value, width, measure_width=lambda v: len(v) * 10,
        line_height=20,
    )


def test_row_height_uses_allocated_child_width():
    tree = row([wrapped("ABCDEFGHIJKLMNOP"), text("OK")], 8)
    narrow = height_for_width(tree, 100, measure_wrapped=measure_lines)
    wide = height_for_width(tree, 300, measure_wrapped=measure_lines)
    assert narrow > wide
    assert narrow >= 40


def test_column_height_sums_wrapped_children():
    tree = column([wrapped("ABCDEFGHIJKLMNOP"), wrapped("ABCDEFGHIJKLMNOP")], 6)
    narrow = height_for_width(tree, 55, measure_wrapped=measure_lines)
    wide = height_for_width(tree, 400, measure_wrapped=measure_lines)
    assert narrow > wide
    assert wide == 46


def test_grid_uses_tallest_cell_per_row():
    tree = grid(2, [wrapped("ABCDEFGHIJKLMNO"), text("OK"),
                    text("OK"), wrapped("ABCDEFGHIJKLMNO")], 8, 8)
    height = height_for_width(tree, 180, measure_wrapped=measure_lines)
    assert height >= 48


def test_padding_reduces_text_width_before_reflow():
    raw = wrapped("ABCDEFGHIJKLMNOP")
    padded = padding(raw, 12, 4)
    assert height_for_width(padded, 100, measure_wrapped=measure_lines) > (
        height_for_width(raw, 100, measure_wrapped=measure_lines) + 8
    )

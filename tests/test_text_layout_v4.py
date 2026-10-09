# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import column, grid, padding, row, scroll, text
from pynix_gui.layout import layout
from pynix_gui.wrap_engine import wrap_text
from pynix_gui.text_layout import native_text_layout
from pynix_gui.text_metrics import GUITextExtent, GUITextMetrics


def line_measure(role, value, width):
    return wrap_text(
        value, width,
        measure_width=lambda candidate: len(candidate) * 10.0,
        line_height=20.0,
    )


def test_public_wrap_mode_is_explicit_and_preserves_source_text():
    leaf = text("Long text label", overflow="wrap")
    assert leaf.text == "Long text label"
    assert leaf.overflow == "wrap"


def test_row_rejects_height_less_than_real_wrapped_need():
    tree = row([text("ABCDEFGHIJKLMNOP", overflow="wrap"), text("OK")], 8)
    with pytest.raises(ValueError, match="wrapped text height"):
        layout(tree, 100, 25, wrap_measure=line_measure)
    result = layout(tree, 100, 100, wrap_measure=line_measure)
    assert result.children[0].rect.height == 100


def test_column_reflows_second_child_below_first():
    tree = column([text("ABCDEFGHIJKLMNOP", overflow="wrap"),
                   text("Bottom")], 6)
    result = layout(tree, 80, 140, wrap_measure=line_measure)
    first, second = result.children
    assert first.rect.height >= 40
    assert second.rect.y >= first.rect.y + first.rect.height + 6


def test_grid_row_tracks_expand_for_wrapped_text():
    tree = grid(2, [text("ABCDEFGHIJKLMNOP", overflow="wrap"),
                    text("Top"), text("Bottom"), text("End")], 8, 6)
    result = layout(tree, 200, 140, wrap_measure=line_measure)
    assert result.children[2].rect.y >= (
        result.children[0].rect.y + result.children[0].rect.height + 6
    )


def test_padded_wrap_does_not_exceed_outer_frame():
    tree = padding(text("ABCDEFGHIJKLMNOP", overflow="wrap"), 10, 5)
    result = layout(tree, 100, 120, wrap_measure=line_measure)
    assert result.children[0].rect.width == 80
    assert result.children[0].rect.height == 110


def test_native_fallback_not_allowed_to_hide_wrap_overflow():
    tree = text("ABCDEFGHIJKLMNOP", overflow="wrap")
    snap = GUITextMetrics({("body", tree.text): GUITextExtent(160, 20)})
    with pytest.raises(ValueError, match="wrapped text height"):
        native_text_layout(
            tree, 30, 20,
            measure_text=lambda view: snap,
            wrap_measure=line_measure,
        )


def test_scroll_viewport_keeps_fixed_height_while_wrap_content_grows():
    tree = scroll(column([
        text("ABCDEFGHIJKLMNOP", overflow="wrap"),
        text("Bottom"),
    ], 6))
    result = layout(tree, 80, 40, wrap_measure=line_measure)
    assert result.rect.height == 40
    assert result.children[0].rect.height > 40


def test_nonwrapped_tree_does_not_consult_wrap_measurer():
    tree = column([text("Plain"), text("Labels")], 4)
    def fail(*args):
        raise AssertionError("unexpected native wrap measurement")
    wrapped = layout(tree, 200, 100, wrap_measure=fail)
    baseline = layout(tree, 200, 100)
    assert wrapped == baseline


def test_wrapped_layout_requires_native_width_measurements():
    tree = text("Text should wrap", overflow="wrap")
    with pytest.raises(ValueError, match="requires width-dependent"):
        layout(tree, 100, 100)

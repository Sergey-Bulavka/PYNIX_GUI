# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from pynix_gui import column, preferred_size, scroll, text
from pynix_gui.layout import layout, measure


def test_scroll_content_uses_viewport_when_only_preferred_width_is_wider():
    # A preference is not a minimum. The scroll document must follow the
    # available viewport so responsive children can reflow.
    content = column([preferred_size(column([text("OK")]), 900, 36)])
    intrinsic = measure(content)
    assert intrinsic.preferred.width > intrinsic.minimum.width
    viewport = max(420, intrinsic.minimum.width + 1)
    tree = layout(scroll(content), viewport, 300)
    assert tree.rect.width == viewport
    assert tree.children[0].rect.width == viewport


def test_scroll_content_keeps_intrinsic_minimum_for_wide_fixed_widgets():
    content = column([text("Fixed minimum"), preferred_size(column([text("OK")]), 900, 36)])
    min_width = measure(content).minimum.width
    viewport = max(1, min_width - 5)
    tree = layout(scroll(content), viewport, 300)
    assert tree.children[0].rect.width >= min_width

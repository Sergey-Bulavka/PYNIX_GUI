# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import text, row
from pynix_gui.core import GUIError
from pynix_gui.layout import layout, measure
from pynix_gui.text_metrics import GUITextMetrics, GUITextExtent


def test_overflow_default_preserves_natural_text_constraints():
    natural = text("Commands", "bodyStrong")
    assert natural.overflow == "natural"
    assert measure(natural).minimum.width == measure(natural).preferred.width


@pytest.mark.parametrize("mode", ("ellipsis", "clip"))
def test_explicit_overflow_preserves_preferred_width_but_can_shrink(mode):
    natural = text("Commands", "bodyStrong")
    flexible = text("Commands", "bodyStrong", overflow=mode)
    assert measure(flexible).minimum.width == 0
    assert measure(flexible).preferred.width == measure(natural).preferred.width
    metrics = GUITextMetrics({
        ("bodyStrong", "Commands"): GUITextExtent(71.5, 19),
    })
    measured = measure(flexible, text_metrics=metrics)
    assert measured.minimum.width == 0
    assert measured.preferred.width == 73.5
    assert layout(flexible, 12, 24, text_metrics=metrics).rect.width == 12


def test_ellipsis_text_in_row_shrinks_without_pushing_neighbors_out():
    flexible = text("Very long content label", overflow="ellipsis")
    fixed = text("OK")
    children = row([flexible, fixed], 8)
    natural_min = measure(row([text("Very long content label"), fixed], 8)).minimum.width
    constrained = measure(children).minimum.width
    assert constrained < natural_min
    result = layout(children, constrained + 10, 24)
    assert result.children[0].rect.width <= 10 + 1e-6
    assert result.children[1].rect.x + result.children[1].rect.width <= result.rect.width + 1e-6


def test_invalid_overflow_is_rejected():
    with pytest.raises(GUIError, match="overflow"):
        text("Label", overflow="wrap")


def test_text_metrics_requests_do_not_change_with_overflow():
    from pynix_gui.text_metrics import collect_text_requests
    tree = row([text("Repeated", overflow="ellipsis"),
                text("Repeated", overflow="clip")], 0)
    assert collect_text_requests(tree) == (("body", "Repeated"),)

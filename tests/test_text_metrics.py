# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
import pytest

from pynix_gui import text, row
from pynix_gui.layout import layout, measure
from pynix_gui.text_metrics import (
    GUITextExtent, GUITextMetrics, collect_text_requests, snapshot_text_metrics,
)


def test_snapshot_deduplicates_ordered_text_requests():
    tree = row([text("Commands", "bodyStrong"), text("Commands", "bodyStrong"),
                text("ADV-04", "caption")], 6)
    assert collect_text_requests(tree) == (
        ("bodyStrong", "Commands"), ("caption", "ADV-04"))
    calls = []
    metrics = snapshot_text_metrics(tree, lambda role, value: (
        calls.append((role, value)) or 71.5, 19.0))
    assert len(metrics) == 2
    assert tuple(calls) == collect_text_requests(tree)
    assert metrics.get("bodyStrong", "Commands") == GUITextExtent(71.5, 19)


def test_measured_text_width_is_used_in_layout_without_global_mutation():
    item = text("Commands", "bodyStrong")
    baseline = measure(item)
    metrics = GUITextMetrics({("bodyStrong", "Commands"): GUITextExtent(71.5, 19)})
    improved = measure(item, text_metrics=metrics)
    assert improved.minimum.width == 73.5
    assert improved.minimum.height >= 19
    assert measure(item) == baseline
    root = row([item, text("OK", "body")], 8)
    normal = measure(root).minimum.width
    exact = measure(root, text_metrics=metrics).minimum.width
    assert exact > normal
    calculated = layout(root, exact, 24, text_metrics=metrics)
    assert calculated.children[0].rect.width >= 73.5


def test_snapshot_copies_input_and_rejects_invalid_metrics():
    values = {("body", "Text"): GUITextExtent(40, 18)}
    snapshot = GUITextMetrics(values)
    values.clear()
    assert snapshot.get("body", "Text") == GUITextExtent(40, 18)
    for width in (float("nan"), float("inf"), -1, "45"):
        with pytest.raises(ValueError):
            GUITextExtent(width, 18)
    with pytest.raises(ValueError):
        GUITextMetrics({("body", 3): GUITextExtent(40, 18)})


def test_missing_native_entry_keeps_previous_deterministic_fallback():
    item = text("No measurement", "body")
    snapshot = GUITextMetrics({("caption", "Other"): GUITextExtent(20, 14)})
    assert measure(item, text_metrics=snapshot) == measure(item)

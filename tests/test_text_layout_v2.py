# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import text, row, max_size
from pynix_gui.layout import layout, measure
from pynix_gui.text_layout import native_text_layout
from pynix_gui.text_metrics import GUITextMetrics, GUITextExtent


def test_native_text_pass_uses_measured_geometry():
    view = row([text("Commands", "bodyStrong"), text("OK", "body")], 8)
    calls = []
    def provide(tree):
        calls.append(tree)
        return GUITextMetrics({("bodyStrong", "Commands"): GUITextExtent(71.5, 19)})
    width = measure(view, text_metrics=provide(view)).minimum.width
    calls.clear()
    result = native_text_layout(view, width, 24, measure_text=provide)
    assert result.used_native_metrics
    assert result.reason is None
    assert len(calls) == 1
    assert result.root.children[0].rect.width >= 73.5


def test_fixed_maximum_uses_atomic_legacy_fallback():
    view = max_size(text("Long title", "body"), 95, 30)
    snapshot = GUITextMetrics({("body", "Long title"): GUITextExtent(120, 19)})
    value = native_text_layout(
        view, 95, 30, measure_text=lambda _: snapshot
    )
    assert not value.used_native_metrics
    assert value.reason is not None
    assert value.root == layout(view, 95, 30)


def test_invalid_legacy_geometry_is_not_hidden():
    view = max_size(text("Long title", "body"), 10, 30)
    with pytest.raises(ValueError):
        native_text_layout(
            view, 95, 30,
            measure_text=lambda _: GUITextMetrics({}),
        )


def test_native_measurement_failure_is_not_silently_ignored():
    view = text("label", "body")
    def fail(_):
        raise RuntimeError("font unavailable")
    with pytest.raises(RuntimeError, match="font unavailable"):
        native_text_layout(view, 100, 30, measure_text=fail)

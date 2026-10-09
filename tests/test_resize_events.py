# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import GUIEvent
from pynix_gui.core import GUIError


def test_resize_event_supports_logical_viewport_dimensions():
    event = GUIEvent("RESIZE", width=820.0, height=600.0)
    assert (event.kind, event.width, event.height) == ("RESIZE", 820.0, 600.0)


@pytest.mark.parametrize(
    "values",
    [
        {"width": -1.0, "height": 500.0},
        {"width": float("nan"), "height": 500.0},
        {"width": float("inf"), "height": 500.0},
        {"width": 820.0},
        {"width": "820", "height": 500.0},
    ],
)
def test_invalid_resize_event_is_rejected(values):
    with pytest.raises(GUIError):
        GUIEvent("RESIZE", **values)


def test_resize_dimensions_do_not_leak_into_other_event_kinds():
    with pytest.raises(GUIError):
        GUIEvent("ACTIVATE", target="button", width=820.0, height=500.0)

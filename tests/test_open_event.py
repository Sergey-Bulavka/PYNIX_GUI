# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import GUIEvent
from pynix_gui.core import GUIError


def test_open_event_contains_exact_structured_item():
    value = GUIEvent("OPEN", target="files-table", item_id="f-src")
    assert (value.kind, value.target, value.item_id) == (
        "OPEN", "files-table", "f-src"
    )


@pytest.mark.parametrize("kwargs", [
    {"target": "files-table"},
    {"target": "files-table", "item_id": ""},
    {"target": "files-table", "item_id": "f-src", "checked": True},
    {"target": "files-table", "item_id": "f-src", "index": 0},
])
def test_invalid_open_event_rejected(kwargs):
    with pytest.raises(GUIError):
        GUIEvent("OPEN", **kwargs)

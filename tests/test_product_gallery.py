# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import importlib.util
from pathlib import Path

from pynix_gui import validate_view


def _gallery_module():
    path = Path(__file__).resolve().parents[1] / "examples" / "showcase.py"
    spec = importlib.util.spec_from_file_location("pynix_product_gallery", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _state(module):
    return {
        "search": "",
        "name": "PYNIX Developer",
        "notes": "Commercial defaults.",
        "checked": True,
        "appearance": 0,
        "scale": 72.0,
        "tree_selected": "main",
        "table_selected": "editor",
        "source": module.SOURCE,
        "selection_start": 0,
        "selection_end": 0,
    }


def test_product_gallery_all_pages_are_valid_gui_trees():
    gallery = _gallery_module()
    state = _state(gallery)

    for page, _label in gallery.NAVIGATION:
        validate_view(gallery.build(page, state))


def test_product_gallery_contains_four_application_examples():
    gallery = _gallery_module()
    pages = {page for page, _label in gallery.NAVIGATION}

    assert {"dashboard", "ide", "settings", "files"} <= pages

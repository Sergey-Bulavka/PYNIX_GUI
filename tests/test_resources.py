# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import (
    GUIError,
    GUIResourceCatalog,
    GUIRuntime,
    canvas_rect,
    canvas_scene,
    image_resource,
    resource_catalog,
    svg_resource,
    vector_icon,
    vector_resource,
)
from pynix_gui.layout import measure


def test_resources_catalog_resolves_logical_image_names():
    catalog = resource_catalog([
        image_resource("app.logo", "/tmp/logo.png"),
    ])

    assert catalog.image_path("app.logo") == "/tmp/logo.png"
    assert catalog.contains("app.logo") is True
    assert catalog.contains("missing") is False


def test_resources_catalog_resolves_vector_scene():
    scene = canvas_scene(
        16,
        16,
        [canvas_rect(2, 2, 12, 12, fill="accent")],
    )
    catalog = resource_catalog([
        vector_resource("toolbar.save", scene),
    ])

    assert catalog.vector_scene("toolbar.save") is scene


def test_resources_names_are_globally_unique():
    scene = canvas_scene(
        16,
        16,
        [canvas_rect(2, 2, 12, 12, fill="accent")],
    )
    with pytest.raises(GUIError) as failure:
        resource_catalog([
            image_resource("same", "/tmp/a.png"),
            vector_resource("same", scene),
        ])

    assert failure.value.code == "PYNIX-GUI-013"


def test_vector_icon_uses_semantic_requested_size():
    view = vector_icon("toolbar.save", 24)
    constraints = measure(view)

    assert constraints.minimum.width == 24
    assert constraints.minimum.height == 24
    assert constraints.preferred.width == 24
    assert constraints.preferred.height == 24


def test_window_resource_catalog_delegates_to_backend():
    class Backend:
        def __init__(self):
            self.catalog = None

        def is_available(self):
            return True

        def open(self, title, width, height):
            return object()

        def set_resources(self, handle, catalog):
            self.catalog = catalog

        def close(self, handle):
            pass

    backend = Backend()
    window = GUIRuntime(backend).open("Resources", 400, 300)
    catalog = GUIResourceCatalog()

    window.set_resources(catalog)

    assert backend.catalog is catalog



def test_resources_catalog_resolves_svg_path():
    catalog = resource_catalog([
        svg_resource("toolbar.open", "assets/open.svg"),
    ])

    assert catalog.vector_scene("toolbar.open") is None
    assert catalog.vector_svg_path("toolbar.open") == "assets/open.svg"
    assert catalog.contains("toolbar.open") is True

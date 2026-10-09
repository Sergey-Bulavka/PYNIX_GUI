# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

from pynix_gui.layout import GUIRect, layout, measure


def view(kind, **kwargs):
    defaults = {
        "children": (),
        "spacing": 0,
        "horizontal": None,
        "vertical": None,
        "width": None,
        "height": None,
        "columns": None,
        "column_spacing": 0,
        "row_spacing": 0,
        "split_id": None,
        "split_position": None,
        "role": None,
        "orientation": None,
        "container_id": None,
        "labels": (),
        "selected": None,
        "target": None,
        "text": None,
        "value": None,
        "placeholder": None,
        "items": (),
        "number": None,
        "minimum_number": None,
        "maximum_number": None,
        "checked": None,
        "enabled": None,
        "focused": None,
        "resource": None,
        "icon_size": None,
        "theme": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(kind=kind, **defaults)


def test_empty_layout_is_independent_of_compiler_runtime():
    root = view("empty")
    constraints = measure(root)
    result = layout(root, 640, 480)

    assert constraints.minimum.width == 0
    assert constraints.minimum.height == 0
    assert result.rect == GUIRect(0, 0, 640, 480)


def test_theme_wrapper_is_geometry_neutral():
    content = view("button", text="Save", role="primary")
    light = view("theme", children=(content,), theme="light")
    dark = view("theme", children=(content,), theme="dark")

    assert measure(light) == measure(dark)
    assert layout(light, 320, 120).rect == layout(dark, 320, 120).rect


def test_row_fill_contract_survives_extraction():
    left = view("button", text="Left", role="secondary")
    filler = view("fill", children=(view("empty"),))
    right = view("button", text="Right", role="secondary")
    root = view("row", children=(left, filler, right), spacing=8)

    result = layout(root, 500, 60)

    assert len(result.children) == 3
    assert result.children[1].rect.width > 0
    assert result.children[2].rect.x > result.children[0].rect.x


def test_surface_geometry_uses_design_tokens():
    panel = view("panel", children=(view("empty"),), role="workspace")
    result = layout(panel, 300, 200)

    child = result.children[0]
    assert child.rect.x == 13
    assert child.rect.y == 13
    assert child.rect.width == 274
    assert child.rect.height == 174



def test_min_size_can_expand_fixed_intrinsic_dimension():
    content = view("text", text="Label", role="body")
    wrapped = view(
        "minSize",
        children=(content,),
        width=180,
        height=120,
    )

    constraints = measure(wrapped)

    assert constraints.minimum.width == 180
    assert constraints.minimum.height == 120
    assert constraints.preferred.width >= 180
    assert constraints.preferred.height >= 120
    assert constraints.maximum.width >= 180
    assert constraints.maximum.height >= 120

    result = layout(wrapped, 220, 140)
    assert result.rect == GUIRect(0, 0, 220, 140)

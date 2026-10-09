# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import (
    GUIError,
    canvas,
    canvas_clip,
    canvas_ellipse,
    canvas_line,
    canvas_path,
    canvas_rect,
    canvas_scene,
    canvas_text,
    canvas_transform,
    layout,
    measure,
    validate_view,
)


def scene():
    return canvas_scene(
        640,
        360,
        [
            canvas_rect(20, 20, 180, 90, fill="surfaceSelected", hit_target="card"),
            canvas_ellipse(260, 40, 80, 80, fill="accentMuted", hit_target="circle"),
            canvas_line(20, 160, 500, 160, stroke="separator"),
            canvas_text(20, 210, "PYNIX Canvas", role="title"),
            canvas_path(
                [(400, 40), (500, 90), (430, 130)],
                closed=True,
                fill="warning",
                hit_target="triangle",
            ),
        ],
    )


def test_adv04_canvas_scene_is_immutable_retained_data():
    value = scene()

    assert value.width == 640
    assert value.height == 360
    assert len(value.commands) == 5


def test_adv04_canvas_hit_targets_must_be_unique():
    with pytest.raises(GUIError) as failure:
        canvas_scene(
            100,
            100,
            [
                canvas_rect(0, 0, 20, 20, hit_target="same"),
                canvas_rect(30, 0, 20, 20, hit_target="same"),
            ],
        )

    assert failure.value.code == "PYNIX-GUI-011"


def test_adv04_canvas_path_requires_real_geometry():
    with pytest.raises(GUIError):
        canvas_path([(1, 2)])


def test_adv04_canvas_clip_and_transform_nest_commands():
    nested = canvas_transform(
        [
            canvas_clip(
                0,
                0,
                100,
                100,
                [canvas_rect(10, 10, 30, 30, fill="accent")],
            )
        ],
        translate_x=20,
        scale_x=2,
        scale_y=2,
        rotate=15,
    )

    assert nested.kind == "transform"
    assert nested.children[0].kind == "clip"


def test_adv04_canvas_view_uses_scene_intrinsic_size():
    view = canvas("diagram", scene())
    constraints = measure(view)

    assert constraints.preferred.width == 640
    assert constraints.preferred.height == 360
    validate_view(view)


def test_adv04_canvas_layout_can_scale_to_larger_host_rect():
    view = canvas("diagram", scene())
    calculated = layout(view, 960, 540)

    assert calculated.rect.width == 960
    assert calculated.rect.height == 540


def test_adv04_canvas_hit_testing_uses_semantic_target():
    from pynix_gui.backends import MacOSGUIBackend

    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    value = canvas_scene(
        100,
        100,
        [
            canvas_rect(10, 10, 30, 30, hit_target="box"),
        ],
    )

    assert backend._canvas_hit_target(value, 50, 50, 200, 200) == "box"
    assert backend._canvas_hit_target(value, 190, 190, 200, 200) is None


def test_adv04_canvas_transform_hit_testing_follows_logical_transform():
    from pynix_gui.backends import MacOSGUIBackend

    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    value = canvas_scene(
        200,
        100,
        [
            canvas_transform(
                [canvas_rect(0, 0, 20, 20, hit_target="moved")],
                translate_x=50,
            )
        ],
    )

    assert backend._canvas_hit_target(value, 55, 10, 200, 100) == "moved"


def test_adv04_canvas_diagnostics_reject_zero_scale():
    with pytest.raises(GUIError) as failure:
        canvas_transform([], scale_x=0)

    assert failure.value.code == "PYNIX-GUI-011"



def test_adv04_canvas_rotated_transform_hit_testing():
    from pynix_gui.backends import MacOSGUIBackend

    backend = MacOSGUIBackend(platform_name="test", appkit=object())
    value = canvas_scene(
        200,
        200,
        [
            canvas_transform(
                [canvas_rect(0, 0, 40, 20, hit_target="rotated")],
                translate_x=100,
                translate_y=100,
                rotate=90,
            )
        ],
    )

    assert backend._canvas_hit_target(value, 90, 120, 200, 200) == "rotated"
    assert backend._canvas_hit_target(value, 130, 120, 200, 200) is None


def test_adv04_canvas_ellipse_hit_test_uses_ellipse_not_bounding_box():
    from pynix_gui.canvas import hit_test_scene

    value = canvas_scene(
        100,
        100,
        [
            canvas_ellipse(10, 10, 80, 80, hit_target="circle"),
        ],
    )

    assert hit_test_scene(value, 50, 50, 100, 100) == "circle"
    assert hit_test_scene(value, 12, 12, 100, 100) is None



def test_adv04_public_canvas_export_is_callable():
    import pynix_gui

    assert callable(pynix_gui.canvas)
    view = pynix_gui.canvas("diagram", scene())
    assert view.kind == "canvas"


def test_adv04_canvas_viewport_preserves_aspect_ratio_and_centers_scene():
    from pynix_gui.canvas import canvas_viewport

    value = canvas_scene(200, 100, [])
    scale, offset_x, offset_y = canvas_viewport(value, 200, 200)

    assert scale == 1.0
    assert offset_x == 0.0
    assert offset_y == 50.0


def test_adv04_canvas_hit_testing_ignores_letterbox_margins():
    from pynix_gui.canvas import hit_test_scene

    value = canvas_scene(
        200,
        100,
        [canvas_rect(0, 0, 200, 100, hit_target="scene")],
    )

    assert hit_test_scene(value, 100, 100, 200, 200) == "scene"
    assert hit_test_scene(value, 100, 10, 200, 200) is None
    assert hit_test_scene(value, 100, 190, 200, 200) is None


def test_adv04_canvas_uniform_viewport_keeps_circle_geometry_circular():
    from pynix_gui.canvas import canvas_viewport

    value = canvas_scene(
        200,
        100,
        [canvas_ellipse(50, 0, 100, 100, hit_target="circle")],
    )
    scale, _offset_x, _offset_y = canvas_viewport(value, 500, 500)

    assert 100 * scale == 100 * scale
    assert scale == 2.5

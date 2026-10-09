# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from pynix_gui.design import (
    BUTTON_VISUALS,
    COLOR_ROLES,
    CONTROL_METRICS,
    DARK,
    ELEVATION,
    ICON_METRICS,
    LIGHT,
    LINES,
    RADII,
    SPACING,
    TEXT_ROLES,
    THEMES,
    TYPOGRAPHY,
    button_visual,
    palette,
    rgb,
    surface_color_role,
)


def test_design_palettes_have_complete_matching_roles():
    assert set(LIGHT) == set(DARK) == set(COLOR_ROLES)
    assert len(COLOR_ROLES) == 30
    assert THEMES == {"system", "light", "dark"}


def test_light_dark_are_valid_and_semantically_distinct():
    assert palette("light") is LIGHT
    assert palette("dark") is DARK
    assert rgb("#000000") == (0.0, 0.0, 0.0)
    assert rgb("#FFFFFF") == (1.0, 1.0, 1.0)

    identical = {
        role
        for role in COLOR_ROLES
        if LIGHT[role] == DARK[role]
    }
    assert identical == {"textOnAccent"}


def test_typography_and_metrics_are_canonical():
    assert TEXT_ROLES == frozenset(TYPOGRAPHY)
    assert TYPOGRAPHY["display"][0] > TYPOGRAPHY["titleLarge"][0] > TYPOGRAPHY["title"][0] > TYPOGRAPHY["body"][0]
    assert TYPOGRAPHY["metric"][1] == "bold"
    assert TYPOGRAPHY["overline"][1] == "semibold"
    assert TYPOGRAPHY["code"][1] == "monospace"

    assert SPACING["space2"] == 8
    assert RADII["radius2"] == 8
    assert RADII["radius4"] == 16
    assert ELEVATION["flat"] < ELEVATION["raised"] < ELEVATION["overlay"]
    assert LINES["focus"] >= 2
    assert CONTROL_METRICS["standardControl"] == 32
    assert ICON_METRICS["iconStandard"] == 16


def test_surface_and_button_roles_are_semantic():
    assert surface_color_role("sidebar") == "surfaceRaised"
    assert surface_color_role("workspace") == "background"
    assert surface_color_role("card") == "surfaceRaised"
    assert surface_color_role("hero") == "accentSubtle"
    assert surface_color_role("successSurface") == "successMuted"

    assert set(BUTTON_VISUALS) == {"primary", "secondary", "quiet", "danger"}
    assert button_visual("primary")["surface"] == "accent"
    assert button_visual("danger")["surface"] == "error"
    assert button_visual("quiet")["bordered"] is False

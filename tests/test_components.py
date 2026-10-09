# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui import (
    GUIError,
    alert,
    badge,
    button,
    button_group,
    card,
    empty_state,
    form_row,
    form_section,
    hero,
    metric_card,
    navigation_item,
    navigation_sidebar,
    property_row,
    search_field,
    section_header,
    text,
    validate_view,
)


def test_commercial_components_compose_valid_core_views():
    root = navigation_sidebar(
        "PYNIX GUI",
        [
            navigation_item("overview", "Overview", True),
            navigation_item("controls", "Controls"),
        ],
        footer=badge("0.1.6-dev", "accent"),
    )
    validate_view(root)

    dashboard = card(
        "Overview",
        metric_card(
            "Components",
            "30+",
            "Stable semantic building blocks",
            badge_view=badge("Ready", "success"),
        ),
        subtitle="Commercial composition layer",
        footer=button_group([
            button("docs", "Documentation"),
            button("build", "Build app", "primary"),
        ]),
    )
    validate_view(dashboard)


def test_forms_alerts_and_empty_state_are_backend_neutral():
    view = form_section(
        "Account",
        [
            form_row(
                "Search",
                search_field("search", "", "Search components"),
                "Controlled String value",
            ),
            property_row("Theme", "System", "Follows host appearance"),
            alert("Saved", "Settings are synchronized.", "success"),
            empty_state(
                "Nothing selected",
                "Choose a component from the navigation.",
                button("choose", "Choose component", "primary"),
            ),
        ],
        "A complete form assembled without native handles.",
    )
    validate_view(view)


def test_hero_and_section_header_build_product_hierarchy():
    view = card(
        "Content",
        hero(
            "Build polished desktop software",
            "Commercial defaults with a small declarative surface.",
            [button("start", "Get started", "primary")],
        ),
        footer=section_header(
            "Next",
            "Explore advanced controls",
            button("open", "Open"),
        ),
    )
    validate_view(view)


@pytest.mark.parametrize("tone", ["neutral", "accent", "success", "warning", "danger", "info"])
def test_badge_tones_are_semantic(tone):
    validate_view(badge("Status", tone))


def test_commercial_components_reject_invalid_values():
    with pytest.raises(GUIError) as failure:
        badge("Bad", "unknown")
    assert failure.value.code == "PYNIX-GUI-014"

    with pytest.raises(GUIError):
        navigation_item("x", "X", "yes")

    with pytest.raises(GUIError):
        form_section("Bad", [text("ok"), "not-a-view"])


def test_property_row_reserves_space_for_native_label_glyphs():
    from pynix_gui.layout import measure, layout
    item = property_row("Commands", "Menus · Dialogs · Shortcuts")
    left_column = item.children[0]
    assert left_column.children[0].kind == "padding"
    padded = left_column.children[0]
    caption = padded.children[0]
    assert caption.text == "Commands"
    assert measure(padded).minimum.width >= measure(caption).minimum.width + 12
    constraints = measure(item)
    result = layout(item, constraints.minimum.width, constraints.minimum.height)
    assert result.children[0].rect.width >= measure(left_column).minimum.width


def test_property_row_commands_reserves_measured_macos_glyph_width():
    # AppKit measured 71.5pt for "Commands" at 13pt semibold.
    # The property-row text allocation must leave at least that much
    # space inside its padded column at the default scale.
    from pynix_gui.layout import measure
    value = property_row("Commands", "Menus · Dialogs · Shortcuts")
    column = value.children[0]
    assert measure(column).minimum.width >= 71.5 + 2

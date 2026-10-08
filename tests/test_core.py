# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui.core import (
    GUIError,
    GUIEvent,
    button,
    check_box,
    column,
    combo_box,
    empty,
    enabled,
    focused,
    horizontal_split,
    list_view,
    panel,
    progress_bar,
    slider,
    tabs,
    text,
    text_area,
    text_field,
    theme,
    validate_view,
)


def test_core_events_are_strict_and_typed():
    assert GUIEvent("CLOSE").kind == "CLOSE"
    assert GUIEvent("ACTIVATE", target="save").target == "save"
    assert GUIEvent("CHANGE", target="name", text="PYNIX").text == "PYNIX"
    assert GUIEvent("CHANGE", target="zoom", number=0.5).number == 0.5
    assert GUIEvent("CHANGE", target="flag", checked=True).checked is True
    assert GUIEvent("SELECTION", target="files", index=1).index == 1

    with pytest.raises(GUIError) as failure:
        GUIEvent("CHANGE", target="x", text="a", checked=True)
    assert failure.value.code == "PYNIX-GUI-006"


def test_core_constructs_and_validates_complete_control_tree():
    root = theme(
        panel(
            column([
                text("PYNIX", "title"),
                focused(text_field("name", "PYNIX", "Name"), True),
                text_area("notes", "one\r\ntwo"),
                check_box("enabled", "Enabled", True),
                combo_box("theme", ["System", "Light", "Dark"], 0),
                slider("zoom", 50, 0, 100),
                progress_bar(20, 0, 100),
                list_view("files", ["one", "two"], 0),
                button("save", "Save", "primary"),
            ], 8),
            "workspace",
        ),
        "dark",
    )

    validate_view(root)
    assert root.theme == "dark"


def test_core_rejects_duplicate_control_targets():
    root = column([
        button("same", "One"),
        text_field("same", ""),
    ])

    with pytest.raises(GUIError) as failure:
        validate_view(root)
    assert failure.value.code == "PYNIX-GUI-006"


def test_core_focus_contract_allows_exactly_one_focusable_descendant():
    validate_view(focused(text_field("name", ""), True))

    ambiguous = focused(
        column([
            text_field("a", ""),
            button("b", "B"),
        ]),
        True,
    )
    with pytest.raises(GUIError) as failure:
        validate_view(ambiguous)
    assert failure.value.code == "PYNIX-GUI-006"


def test_core_tabs_and_split_identity_are_deterministic():
    root = horizontal_split(
        "main",
        tabs(
            "tabs",
            ["One", "Two"],
            0,
            [empty(), empty()],
        ),
        empty(),
        300,
    )
    validate_view(root)

    duplicate_tabs = column([
        tabs("same", ["A"], 0, [empty()]),
        tabs("same", ["B"], 0, [empty()]),
    ])
    with pytest.raises(GUIError) as failure:
        validate_view(duplicate_tabs)
    assert failure.value.code == "PYNIX-GUI-005"


def test_core_numeric_and_selection_controls_validate_at_construction():
    assert slider("volume", 0.5, 0.0, 1.0).number == 0.5
    assert list_view("empty-list", [], -1).selected == -1

    with pytest.raises(GUIError):
        slider("bad", 2, 0, 1)

    with pytest.raises(GUIError):
        combo_box("bad", [], 0)


def test_core_enabled_and_theme_wrappers_preserve_child_identity():
    child = button("run", "Run")
    wrapped = enabled(theme(child, "system"), False)

    assert wrapped.enabled is False
    assert wrapped.children[0].theme == "system"
    assert wrapped.children[0].children[0] is child
    validate_view(wrapped)


def test_core_textarea_normalizes_line_endings_without_compiler_runtime():
    area = text_area("notes", "one\r\ntwo\rthree")
    assert area.value == "one\ntwo\nthree"

# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

import pytest

from pynix_gui.wrap_engine import GUIWrappedText, wrap_text


def width(value):
    return len(value) * 10.0


def test_wrap_preserves_full_text_with_whitespace_breaks():
    result = wrap_text("Alpha Beta Gamma", 62, measure_width=width, line_height=20)
    assert result.lines == ("Alpha", "Beta", "Gamma")
    assert result.height == 60


def test_wrap_preserves_explicit_empty_paragraphs():
    result = wrap_text("First\n\nLast", 100, measure_width=width, line_height=18)
    assert result.lines == ("First", "", "Last")
    assert result.height == 54


def test_long_word_splits_by_character_when_necessary():
    result = wrap_text("ABCDEF", 25, measure_width=width, line_height=17)
    assert result.lines == ("AB", "CD", "EF")


def test_combining_codepoint_stays_with_base_glyph():
    result = wrap_text("e\u0301x", 11, measure_width=lambda v: len(v.replace("\u0301", "")) * 10,
                       line_height=16)
    assert result.lines == ("e\u0301", "x")


def test_zwj_emoji_sequence_is_not_split():
    sequence = "\U0001f469\u200d\U0001f4bb"
    result = wrap_text(sequence + "A", 10, measure_width=lambda v: 10 * (v.count("A") + (sequence in v)),
                       line_height=16)
    assert result.lines == (sequence, "A")


def test_same_inputs_produce_unchanged_immutable_result():
    first = wrap_text("A B C", 25, measure_width=width, line_height=18)
    second = wrap_text("A B C", 25, measure_width=width, line_height=18)
    assert isinstance(first, GUIWrappedText)
    assert first == second
    with pytest.raises(AttributeError):
        first.height = 80


@pytest.mark.parametrize("width_value", (0, -1, float("nan"), float("inf")))
def test_invalid_available_width_rejected(width_value):
    with pytest.raises(ValueError):
        wrap_text("Text", width_value, measure_width=width, line_height=18)


def test_invalid_native_measurement_rejected():
    with pytest.raises(ValueError):
        wrap_text("ABC", 25, measure_width=lambda _: float("nan"), line_height=18)

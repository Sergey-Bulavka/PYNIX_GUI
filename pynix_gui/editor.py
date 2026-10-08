# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Language-agnostic rich editor values."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from .core import GUIError


_EDITOR_ROLES = {
    "plain",
    "keyword",
    "type",
    "string",
    "number",
    "comment",
    "function",
    "property",
    "constant",
    "warning",
    "error",
    "muted",
    "strong",
}


@dataclass(frozen=True, slots=True)
class GUITextSpan:
    start: int
    end: int
    role: str

    def __post_init__(self):
        if type(self.start) is not int or type(self.end) is not int:
            raise GUIError("PYNIX-GUI-012", "GUI editor span offsets must be Int.")
        if self.start < 0 or self.end <= self.start:
            raise GUIError("PYNIX-GUI-012", "GUI editor span range is invalid.")
        if self.role not in _EDITOR_ROLES:
            raise GUIError("PYNIX-GUI-012", "GUI editor span role is invalid.")


def text_span(start: int, end: int, role: str) -> GUITextSpan:
    return GUITextSpan(start, end, role)


def validate_editor_state(
    text: str,
    selection_start: int,
    selection_end: int,
    spans,
):
    if type(text) is not str:
        raise GUIError("PYNIX-GUI-012", "GUI editor text must be String.")
    if type(selection_start) is not int or type(selection_end) is not int:
        raise GUIError("PYNIX-GUI-012", "GUI editor selection offsets must be Int.")
    if not 0 <= selection_start <= selection_end <= len(text):
        raise GUIError("PYNIX-GUI-012", "GUI editor selection is outside text bounds.")
    if isinstance(spans, (str, bytes)) or not isinstance(spans, Sequence):
        raise GUIError("PYNIX-GUI-012", "GUI editor spans must be a sequence.")

    span_values = tuple(spans)
    if any(not isinstance(span, GUITextSpan) for span in span_values):
        raise GUIError("PYNIX-GUI-012", "GUI editor spans are invalid.")
    if any(span.end > len(text) for span in span_values):
        raise GUIError("PYNIX-GUI-012", "GUI editor span exceeds text bounds.")

    ordered = sorted(span_values, key=lambda value: (value.start, value.end))
    for previous, current in zip(ordered, ordered[1:]):
        if current.start < previous.end:
            raise GUIError("PYNIX-GUI-012", "GUI editor spans must not overlap.")

    return text, selection_start, selection_end, span_values


EDITOR_ROLES = frozenset(_EDITOR_ROLES)

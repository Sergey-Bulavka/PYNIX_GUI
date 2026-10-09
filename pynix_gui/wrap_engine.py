# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Pure line-breaking primitives for a future height-for-width layout pass.

The caller supplies native font measurements. This module never imports GUI
frameworks, and does not mutate view objects or the layout tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
import math
import unicodedata


@dataclass(frozen=True, slots=True)
class GUIWrappedText:
    lines: tuple[str, ...]
    width: float
    height: float


def _graphemes(value: str) -> tuple[str, ...]:
    """Keep combining marks, variation selectors, and ZWJ sequences together.

    This is a conservative approximation, not full Unicode UAX #29 shaping.
    Platform text engines remain authoritative for glyph rendering.
    """
    groups = []
    join_next = False
    for char in value:
        modifier = (unicodedata.combining(char) != 0
                    or char in ("\ufe0e", "\ufe0f")
                    or 0x1F3FB <= ord(char) <= 0x1F3FF)
        if groups and (modifier or char == "\u200d" or join_next):
            groups[-1] += char
        else:
            groups.append(char)
        join_next = char == "\u200d"
    return tuple(groups)


def wrap_text(
    value: str,
    width: float,
    *,
    measure_width: Callable[[str], float],
    line_height: float,
) -> GUIWrappedText:
    """Wrap at whitespace when possible; break long words at grapheme edges.

    A newline always starts a new line. Each candidate is measured through
    the supplied native-font callback, including kerning and font fallback.
    The output is immutable and deterministic for the same callback results.
    """
    if not isinstance(value, str):
        raise TypeError("wrapped text must be a string")
    if not math.isfinite(width) or width <= 0:
        raise ValueError("wrap width must be finite and positive")
    if not math.isfinite(line_height) or line_height <= 0:
        raise ValueError("line height must be finite and positive")

    def fits(candidate):
        measured = float(measure_width(candidate))
        if not math.isfinite(measured) or measured < 0:
            raise ValueError("native text width must be finite and nonnegative")
        return measured <= width + 1e-7

    lines = []
    for paragraph in value.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        previous_break = -1
        for cluster in _graphemes(paragraph):
            candidate = current + cluster
            if current and not fits(candidate):
                if previous_break >= 0:
                    lines.append(current[:previous_break].rstrip())
                    current = current[previous_break:].lstrip() + cluster
                else:
                    lines.append(current)
                    current = cluster
                previous_break = -1
                for index, char in enumerate(current):
                    if char.isspace():
                        previous_break = index + 1
            else:
                current = candidate
                if cluster.isspace():
                    previous_break = len(current)
        lines.append(current.rstrip())
    return GUIWrappedText(tuple(lines), width, len(lines) * line_height)

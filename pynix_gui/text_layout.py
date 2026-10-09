# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Native-first text layout with deterministic legacy compatibility."""

from __future__ import annotations

from dataclasses import dataclass
from .layout import layout


@dataclass(frozen=True, slots=True)
class GUITextLayoutPass:
    root: object
    used_native_metrics: bool
    reason: str | None = None


def native_text_layout(view, width, height, *, measure_text, split_positions=None):
    """Calculate one atomic pass using a host-provided immutable text snapshot.

    If native measurements violate older fixed-size constraints, retry with
    the accepted legacy sizing. Do not suppress unrelated layout errors.
    """
    snapshot = measure_text(view)
    try:
        measured = layout(
            view, width, height, split_positions=split_positions,
            text_metrics=snapshot,
        )
    except ValueError as error:
        legacy = layout(view, width, height, split_positions=split_positions)
        return GUITextLayoutPass(legacy, False, str(error))
    return GUITextLayoutPass(measured, True)

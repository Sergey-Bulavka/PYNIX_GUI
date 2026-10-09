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


def native_text_layout(view, width, height, *, measure_text, split_positions=None, wrap_measure=None):
    """Calculate one atomic pass using a host-provided immutable text snapshot.

    If native measurements violate older fixed-size constraints, retry with
    the accepted legacy sizing. Do not suppress unrelated layout errors.
    """
    snapshot = measure_text(view)
    try:
        measured = layout(
            view, width, height, split_positions=split_positions,
            text_metrics=snapshot, wrap_measure=wrap_measure,
        )
    except ValueError as error:
        # Wrapping cannot fall back to a single-line geometry pass:
        # the native label would overdraw following controls.
        def contains_wrap(node):
            return (
                node.kind == "text" and getattr(node, "overflow", None) == "wrap"
            ) or any(contains_wrap(child) for child in node.children)
        if wrap_measure is not None and contains_wrap(view):
            raise
        legacy = layout(view, width, height, split_positions=split_positions)
        return GUITextLayoutPass(legacy, False, str(error))
    return GUITextLayoutPass(measured, True)

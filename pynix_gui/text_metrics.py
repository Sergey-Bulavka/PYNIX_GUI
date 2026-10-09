# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Immutable platform text-measurement snapshots for deterministic layout.

Layout does not import AppKit or Qt. A host measures text once and passes a
snapshot; the same snapshot always yields the same geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import math


@dataclass(frozen=True, slots=True)
class GUITextExtent:
    width: float
    height: float

    def __post_init__(self):
        for value in (self.width, self.height):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("text extents must be finite nonnegative numbers")


class GUITextMetrics:
    """Read-only, copy-on-construction mapping of (role, text) to extents."""

    def __init__(self, entries: Mapping[tuple[str, str], GUITextExtent]):
        snapshot = {}
        for key, value in entries.items():
            if (not isinstance(key, tuple) or len(key) != 2
                    or any(type(part) is not str for part in key)):
                raise ValueError("text measurement keys must be (role, text) strings")
            if not isinstance(value, GUITextExtent):
                raise ValueError("text measurements must be GUITextExtent")
            snapshot[key] = value
        self._values = MappingProxyType(snapshot)

    def get(self, role: str, text: str) -> GUITextExtent | None:
        return self._values.get((role, text))

    def __len__(self) -> int:
        return len(self._values)


def collect_text_requests(view) -> tuple[tuple[str, str], ...]:
    """Collect each text/font-role pair once in stable source-tree order."""
    seen = set()
    ordered = []

    def visit(node):
        if node.kind == "text":
            pair = (node.role, node.text)
            if pair not in seen:
                seen.add(pair)
                ordered.append(pair)
        for child in node.children:
            visit(child)

    visit(view)
    return tuple(ordered)


def snapshot_text_metrics(view, measure):
    """Measure every text leaf using a callable (role, text) -> (width, height).

    Hosts must call this on their GUI thread. No global font cache or state
    leaks into the cross-platform layout model.
    """
    result = {}
    for role, text in collect_text_requests(view):
        width, height = measure(role, text)
        result[(role, text)] = GUITextExtent(width, height)
    return GUITextMetrics(result)

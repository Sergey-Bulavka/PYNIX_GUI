# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""PYNIX-owned fallback SVGs where the licensed JetBrains collection lacks a glyph.

These are original vectors, not representations of unavailable JetBrains files.
The New UI tool window profile remains the sole renderer for these controls.
"""
from __future__ import annotations


def native_tool_icon(label: str, *, dark: bool = True) -> str | None:
    ink = "#CED0D6" if dark else "#6C707E"
    paths = {
        "Pull Requests": (
            '<circle cx="5" cy="4.5" r="2" stroke="currentColor" stroke-width="1.5"/>'
            '<circle cx="5" cy="15.5" r="2" stroke="currentColor" stroke-width="1.5"/>'
            '<circle cx="15" cy="15.5" r="2" stroke="currentColor" stroke-width="1.5"/>'
            '<path d="M5 6.5v7M9 4.5h2a4 4 0 0 1 4 4v5" '
            'stroke="currentColor" stroke-width="1.5" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            '<path d="m9.75 2.7-2 1.8 2 1.8" stroke="currentColor" '
            'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>'
        ),
        "Terminal": (
            '<rect x="2.25" y="2.75" width="15.5" height="14.5" rx="2" '
            'stroke="currentColor" stroke-width="1.5"/>'
            '<path d="m5.6 6.7 3.3 3.3-3.3 3.3M10.7 13.25h3.65" '
            'stroke="currentColor" stroke-width="1.5" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
        ),
        "AI Assistant": (
            '<path d="M4.25 3.25h9.5a3 3 0 0 1 3 3v5a3 3 0 0 1-3 3H8.5l-3.75 2.5v-2.5h-.5a2 2 0 0 1-2-2v-6a3 3 0 0 1 2-3Z" '
            'stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>'
            '<path d="M6.4 7.5h7M6.4 10.4h4.5" stroke="currentColor" '
            'stroke-width="1.5" stroke-linecap="round"/>'
        ),
    }
    shape = paths.get(label)
    if shape is None:
        return None
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" '
        'viewBox="0 0 20 20" fill="none" color="' + ink + '">'
        + shape + '</svg>'
    )

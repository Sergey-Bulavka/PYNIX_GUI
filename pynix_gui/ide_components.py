# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Reusable IDE-focused compositions built from public PYNIX GUI primitives.

This module is intentionally independent of compiler, filesystem and IDE state.
Native backend styling and editor-specific decoration are separate acceptance gates.
"""

from dataclasses import dataclass
from pynix_gui import button, column, fill, row, text, separator, toolbar, status_bar


@dataclass(frozen=True)
class IDEChromeMetrics:
    activity_width: int = 48
    explorer_width: int = 256
    editor_tabs_height: int = 36
    bottom_height: int = 190
    status_height: int = 26
    editor_font_size: int = 13


METRICS = IDEChromeMetrics()


def ide_command_bar(project: str, *, run_target="shell-run"):
    return toolbar(row([
        text("PYNIX", "titleSmall"),
        text("IDE", "caption"),
        fill(text(project, "caption")),
        button("shell-project", "Open", "quiet"),
        button("shell-toggle-inspector", "Inspector", "quiet"),
        button(run_target, "▶ Run", "primary"),
    ], 10))


def ide_editor_tab_strip(tab_names, active, *, target_prefix="shell-file-"):
    """A controlled tab-like strip. Native Chrome tabs are future backend work."""
    controls = [
        button(target_prefix + name,
               name,
               "primary" if name == active else "quiet")
        for name in tab_names
    ]
    controls.append(button("shell-close-tab", "×", "quiet"))
    return column([row(controls + [fill(text("", "caption"))], 4),
                   separator("horizontal")], 2)


def ide_tool_window_header(active, labels=("Problems", "Output", "Terminal", "Debug Console")):
    controls = [
        button("shell-tool-" + title.lower().replace(" ", "-"),
               title, "primary" if title == active else "quiet")
        for title in labels
    ]
    controls.extend([fill(text("", "caption")),
                     button("shell-toggle-bottom", "×", "quiet")])
    return column([separator("horizontal"), row(controls, 4)], 2)


def ide_status_strip(message: str, filename: str):
    return status_bar(row([
        text("● " + message, "caption"),
        fill(text("PYNIX  ·  " + filename, "caption")),
        text("UTF-8  ·  Spaces: 4  ·  Ln 1, Col 1", "caption"),
    ], 8))

# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Platform-neutral checks for the macOS-native visual acceptance shell."""

import ast
from pathlib import Path

from examples import ide_native_visual_shell as scene


def test_native_visual_shell_source_parses():
    source = Path(scene.__file__).read_text(encoding="utf-8")
    ast.parse(source)


def test_native_visual_palette_and_project_tree():
    assert {"canvas", "editor", "sidebar", "toolbar", "status", "accent"} <= scene.PALETTE.keys()
    assert len(scene.PROJECT_TREE) >= 8
    assert any(row[1] == "main.pnx" and row[3] for row in scene.PROJECT_TREE)


def test_native_shell_contains_colored_pynix_sample():
    assert len(scene.SAMPLE_LINES) >= 8
    assert any(role == "keyword" for line in scene.SAMPLE_LINES for role, _ in line)
    assert any(role == "green" for line in scene.SAMPLE_LINES for role, _ in line)


def test_native_visual_preview_has_no_appkit_import_at_module_load():
    # Linux CI can parse/import this module without AppKit.
    import sys
    if sys.platform != "darwin":
        assert "AppKit" not in sys.modules


def test_native_visual_shell_uses_real_vector_shapes_for_terminal_and_documents():
    source = Path(scene.__file__).read_text(encoding="utf-8")
    from pynix_gui.ide_iconography import ICONS
    assert "terminal" in ICONS
    assert "pnx" in ICONS
    assert any(command[0] == "poly" for command in ICONS["terminal"])
    assert 'self._icon(content_x+177' in source
    assert 'self._rule(content_x+158' in source


def test_native_shell_no_unbounded_tree_index_lookup():
    source = Path(scene.__file__).read_text(encoding="utf-8")
    assert "PROJECT_TREE.index(" not in source


def test_native_preview_terminates_after_last_window_closes():
    source = Path(scene.__file__).read_text(encoding="utf-8")
    assert "applicationShouldTerminateAfterLastWindowClosed_" in source
    assert "app.setDelegate_(delegate)" in source

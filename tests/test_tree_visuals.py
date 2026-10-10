# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from pynix_gui import tree_node
from pynix_gui.tree_visuals import tree_node_kind, compact_tree_label_width, tree_icon_size, tree_disclosure_size, tree_file_icon_kind, tree_disclosure_column_width, pnx_icon_path


def test_folder_and_document_visually_distinguishable():
    model = tree_node("folder", "src", [tree_node("file", "main.pnx")])
    assert tree_node_kind(model) == "folder"
    assert tree_node_kind(model.children[0]) == "file"


def test_compact_tree_labels_never_stretch_to_fill_wide_row():
    assert compact_tree_label_width("src", 650) < 120
    assert compact_tree_label_width("main.pnx", 650) < 180
    assert compact_tree_label_width("a very long document filename", 105) == 105
    assert compact_tree_label_width("document", -2) == 0


def test_tree_icons_follow_text_and_row_geometry():
    assert 14 <= tree_icon_size(30, 13) <= 19.2
    assert tree_icon_size(24, 13) <= 24 * 0.64
    assert tree_icon_size(36, 16) > tree_icon_size(30, 12)
    assert tree_icon_size(0, 13) == 0
    assert tree_icon_size(30, 0) == 0


def test_disclosure_chevron_scales_with_tree_row_and_font():
    assert 18 <= tree_disclosure_size(30, 13) <= 23
    assert tree_disclosure_size(36, 16) > tree_disclosure_size(30, 12)
    assert tree_disclosure_size(24, 13) <= 24 * 0.76
    assert tree_disclosure_size(0, 13) == 0


def test_file_icons_choose_pnx_and_fallback_consistently():
    assert tree_file_icon_kind("main.pnx", False) == "pnx"
    assert tree_file_icon_kind("MAIN.PNX", False) == "pnx"
    assert tree_file_icon_kind("notes.txt", False) == "file"
    assert tree_file_icon_kind("src", True) == "folder"
    assert pnx_icon_path().is_file()
    assert pnx_icon_path().read_bytes().startswith(bytes.fromhex("89504e47"))


def test_disclosure_width_and_size_match_readable_project_tree():
    assert tree_disclosure_size(30, 13) >= 18
    assert tree_disclosure_column_width(30) >= 24


def test_empty_directories_are_explicitly_supported():
    empty_dir = tree_node("assets", "assets", kind="folder")
    assert tree_node_kind(empty_dir) == "folder"
    assert tree_node_kind(tree_node("plain", "notes.txt")) == "file"

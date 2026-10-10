# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Filesystem contract tests; no native GUI backend required."""

from pathlib import Path
import pytest

from examples.project_explorer import ProjectExplorer, ProjectExplorerError


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src" / "ui").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "main.pnx").write_text("print(1)\n", encoding="utf-8")
    (tmp_path / "src" / "ui" / "view.pnx").write_text("print(2)\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Example", encoding="utf-8")
    return ProjectExplorer(tmp_path)


def test_directory_first_sort_and_direct_children_only(project):
    assert [entry.name for entry in project.entries()] == ["src", "tests", "README.md"]
    assert [entry.name for entry in project.entries("src")] == ["ui", "main.pnx"]


def test_single_selection_does_not_navigate(project):
    assert project.select("src")
    assert project.folder == ""
    assert project.open() is None
    assert project.folder == "src"
    assert project.selected is None


def test_folder_navigation_and_open_source_file(project):
    project.open("src")
    assert project.select("src/main.pnx")
    assert project.folder == "src"
    assert project.open() == "src/main.pnx"
    assert project.folder == "src"
    assert project.last_opened == "src/main.pnx"
    assert project.read_pnx("src/main.pnx") == "print(1)\n"
    assert project.up()
    assert project.folder == ""
    assert not project.up()


def test_missing_or_stale_selection_cannot_open(project):
    assert not project.select("src/main.pnx")
    assert project.open("src/main.pnx") is None
    assert project.last_opened is None
    assert project.folder == ""


def test_recursive_tree_is_bounded(project):
    shallow = ProjectExplorer(project.root, max_depth=1)
    tree = shallow.tree()
    assert len(tree) == 3
    src = next(children for entry, children in tree if entry.name == "src")
    assert src == []
    deep = project.tree()
    src = next(children for entry, children in deep if entry.name == "src")
    assert [entry.name for entry, _ in src] == ["ui", "main.pnx"]


def test_symlinks_are_hidden_and_cannot_escape(project, tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside.pnx")
    outside.write_text("secret", encoding="utf-8")
    (project.root / "outside.pnx").symlink_to(outside)
    (project.root / "loop").symlink_to(project.root, target_is_directory=True)
    assert "outside.pnx" not in [entry.name for entry in project.entries()]
    assert "loop" not in [entry.name for entry in project.entries()]
    with pytest.raises(ProjectExplorerError):
        project.read_pnx("outside.pnx")
    with pytest.raises(ProjectExplorerError):
        project.entries("../")


def test_read_pnx_validations(project):
    with pytest.raises(ProjectExplorerError):
        project.read_pnx("README.md")
    with pytest.raises(ProjectExplorerError):
        project.read_pnx("src/main.pnx", max_bytes=2)
    (project.root / "src" / "invalid.pnx").write_bytes(b"\\xff\\xfe")
    with pytest.raises(ProjectExplorerError):
        project.read_pnx("src/invalid.pnx")


def test_missing_project_is_controlled(tmp_path):
    with pytest.raises(ProjectExplorerError):
        ProjectExplorer(tmp_path / "missing")
    with pytest.raises(ProjectExplorerError):
        ProjectExplorer(tmp_path / "other.pnx")


def test_invalid_depth(tmp_path):
    with pytest.raises(ValueError):
        ProjectExplorer(tmp_path, max_depth=0)

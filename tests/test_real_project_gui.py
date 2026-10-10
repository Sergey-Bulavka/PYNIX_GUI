# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Pure GUI contract checks for the real project example."""

from pynix_gui import GUIEvent, validate_view
from examples.project_explorer import ProjectExplorer
from examples.real_project_app import build, dispatch


def _setup(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.pnx").write_text("print(12)\n", encoding="utf-8")
    explorer = ProjectExplorer(tmp_path)
    state = {"expanded": ["__project_root__"], "preview": "", "message": "Ready"}
    return explorer, state


def test_real_project_view_is_valid(tmp_path):
    explorer, state = _setup(tmp_path)
    validate_view(build(explorer, state))
    assert dispatch(explorer, state, GUIEvent("OPEN", target="real-project-files", item_id="src"))
    assert explorer.folder == "src"
    validate_view(build(explorer, state))


def test_real_project_preview_is_read_only(tmp_path):
    explorer, state = _setup(tmp_path)
    dispatch(explorer, state, GUIEvent("OPEN", target="real-project-files", item_id="src"))
    dispatch(explorer, state, GUIEvent("OPEN", target="real-project-files", item_id="src/main.pnx"))
    assert state["preview"] == "print(12)\n"
    assert explorer.folder == "src"
    view = build(explorer, state)
    validate_view(view)

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    editor = next(item for item in walk(view) if item.kind == "richEditor")
    assert editor.read_only is True


def test_gui_up_and_refresh_keep_valid_model(tmp_path):
    explorer, state = _setup(tmp_path)
    dispatch(explorer, state, GUIEvent("OPEN", target="real-project-files", item_id="src"))
    dispatch(explorer, state, GUIEvent("ACTIVATE", target="real-project-up"))
    dispatch(explorer, state, GUIEvent("ACTIVATE", target="real-project-refresh"))
    assert explorer.folder == ""
    validate_view(build(explorer, state))


def test_tree_does_not_render_source_files_or_stale_expansion(tmp_path):
    explorer, state = _setup(tmp_path)
    state["expanded"] = ["__project_root__", "deleted-folder"]
    view = build(explorer, state)
    validate_view(view)
    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)
    tree_view = next(item for item in walk(view) if item.kind == "tree")
    assert "deleted-folder" not in tree_view.expanded_ids
    def ids(nodes):
        for node in nodes:
            yield node.node_id
            yield from ids(node.children)
    assert "src/main.pnx" not in set(ids(tree_view.data))


def test_refresh_updates_real_files(tmp_path):
    explorer, state = _setup(tmp_path)
    (tmp_path / "new.pnx").write_text("new", encoding="utf-8")
    dispatch(explorer, state, GUIEvent("ACTIVATE", target="real-project-refresh"))
    view = build(explorer, state)
    validate_view(view)
    assert any(entry.path == "new.pnx" for entry in explorer.entries())


def test_hidden_directories_are_opt_in(tmp_path):
    explorer, state = _setup(tmp_path)
    (tmp_path / ".git").mkdir()
    view = build(explorer, state)
    validate_view(view)
    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)
    t = next(node for node in walk(view) if node.kind == "tree")
    assert all(child.label != ".git" for child in t.data[0].children)
    dispatch(explorer, state, GUIEvent("ACTIVATE", target="real-project-hidden"))
    assert state["show_hidden"] is True
    view = build(explorer, state)
    validate_view(view)
    t = next(node for node in walk(view) if node.kind == "tree")
    assert any(child.label == ".git" for child in t.data[0].children)


def test_explorer_sidebar_is_present_in_workspace_layout(tmp_path):
    explorer, state = _setup(tmp_path)
    view = build(explorer, state)
    validate_view(view)

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    # Regression: the sidebar must remain a sibling of the main content,
    # not disappear behind a native nested split view.
    tree_nodes = [node for node in walk(view) if node.kind == "tree"]
    assert len(tree_nodes) == 1
    assert any(node.kind == "row" and len(node.children) == 2 for node in walk(view))
    assert any(node.kind == "table" for node in walk(view))

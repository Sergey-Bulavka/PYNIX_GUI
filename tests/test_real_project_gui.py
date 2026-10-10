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

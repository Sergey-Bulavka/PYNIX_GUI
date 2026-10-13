"""Executable, disk-safe compiler-backed multi-file rename plan tests."""
from pathlib import Path

import pytest

from pynix_gui.ide_semantic_rename import RenamePlanError, plan_semantic_rename


def _project(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (tmp_path / "pynix.toml").write_text("[project]\nname='example'\n", encoding="utf-8")
    main = src / "main.pnx"
    util = src / "util.pnx"
    main.write_text(
        'import util\nfunction main()\n    let value = util.helper()\n', encoding="utf-8")
    util.write_text(
        'public function helper()\n    return 7\nfunction other()\n    helper()\n',
        encoding="utf-8")
    return main, util


def test_semantic_rename_updates_only_compiler_verified_cross_file_spans(tmp_path, monkeypatch):
    main, util = _project(tmp_path)
    first = main.read_text(encoding="utf-8")
    second = util.read_text(encoding="utf-8")
    main_start = first.index("util.helper")
    util_start = second.rindex("helper")
    payload = {
        "protocol": "pynix-tooling", "version": 1, "kind": "references",
        "definition": {
            "name": "helper", "kind": "function", "source": str(util),
            "start": {"line": 1, "column": 1, "offset": 0},
        },
        "references": [
            {"source": str(main),
             "start": {"offset": main_start},
             "end": {"offset": main_start + len("util.helper")}},
            {"source": str(util),
             "start": {"offset": util_start},
             "end": {"offset": util_start + len("helper")}},
        ],
    }
    monkeypatch.setattr(
        "pynix_gui.ide_semantic_rename.query_navigation",
        lambda *args: payload,
    )
    plan = plan_semantic_rename(tmp_path, tmp_path / "python", "src/main.pnx", 3, 22, "renamed")
    assert plan["symbol"] == "helper"
    assert plan["occurrences"] == 3
    edits = {entry["source"]: entry for entry in plan["files"]}
    assert set(edits) == {"src/main.pnx", "src/util.pnx"}
    assert "util.renamed()" in edits["src/main.pnx"]["after"]
    assert "public function renamed()" in edits["src/util.pnx"]["after"]
    assert "    renamed()" in edits["src/util.pnx"]["after"]
    assert main.read_text(encoding="utf-8") == first
    assert util.read_text(encoding="utf-8") == second


def test_semantic_rename_fails_closed_on_incorrect_compiler_offset(tmp_path, monkeypatch):
    main, util = _project(tmp_path)
    monkeypatch.setattr(
        "pynix_gui.ide_semantic_rename.query_navigation", lambda *args: {
            "protocol": "pynix-tooling", "version": 1, "kind": "references",
            "definition": {"name": "helper", "source": str(util),
                           "start": {"line": 1}},
            "references": [{"source": str(main),
                            "start": {"offset": 0}, "end": {"offset": 5}}],
        })
    with pytest.raises(RenamePlanError, match="differs from target"):
        plan_semantic_rename(tmp_path, tmp_path / "python", "src/main.pnx", 3, 22, "renamed")


def test_semantic_rename_rejects_keyword_and_outside_project(tmp_path, monkeypatch):
    _, util = _project(tmp_path)
    with pytest.raises(RenamePlanError, match="non-keyword"):
        plan_semantic_rename(tmp_path, tmp_path / "python", "src/main.pnx", 1, 1, "return")
    outside = tmp_path.parent / "outside.pnx"
    outside.write_text("function external()\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(
        "pynix_gui.ide_semantic_rename.query_navigation", lambda *args: {
            "protocol": "pynix-tooling", "version": 1, "kind": "references",
            "definition": {"name": "external", "source": str(outside),
                           "start": {"line": 1}},
            "references": [],
        })
    with pytest.raises(RenamePlanError, match="outside indexed"):
        plan_semantic_rename(tmp_path, tmp_path / "python", "src/main.pnx", 1, 1, "renamed")

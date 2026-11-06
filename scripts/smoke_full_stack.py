#!/usr/bin/env python3
# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Live compiler + GUI controller + official IDE Core acceptance in an isolated project.

This does not drive WKWebView or claim visual acceptance of the native window.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

from pynix_gui.ide_core_persistent import PersistentCoreReader
from pynix_gui.ide_project_runner import ProjectRunner
from pynix_gui.ide_workspace_session import WorkspaceSession


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ide-core", type=Path, required=True)
    parser.add_argument("--compiler-python", type=Path, required=True)
    args = parser.parse_args()

    compiler_python = args.compiler_python.expanduser().absolute()
    ide_core = args.ide_core.expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="zunyite-full-stack-") as temp:
        project = Path(temp)
        (project / "src").mkdir()
        (project / "zunyite.toml").write_text(
            '[project]\nname = "acceptance"\nsource = "src"\nentry = "main.uny"\n',
            encoding="utf-8",
        )
        original = 'function main()\n    print("ZUNYITE_RUN_OK")\n'
        source = project / "src" / "main.uny"
        source.write_text(original, encoding="utf-8")
        legacy = project / "src" / "legacy.pnx"
        legacy.write_text('function helper()\n    pass\n', encoding="utf-8")

        session = WorkspaceSession(project)
        assert session.open("src/main.uny").text == original
        assert session.open("src/legacy.pnx").text == legacy.read_text(encoding="utf-8")
        session.create_file("src/new_file.uny", content="function hello()\n    pass\n")
        assert (project / "src" / "new_file.uny").is_file()
        print("PASS: isolated .uny create + .pnx compatibility", flush=True)

        core = PersistentCoreReader(ide_core, project, compiler_python)
        try:
            snapshot = core.start()
            assert isinstance(snapshot, dict)
            core.open_source("src/main.uny")
            first = core.read_source("src/main.uny")
            assert first["content"] == original, first
            edited = 'function main()\n    print("UNSAVED_BUFFER")\n'
            revision = first["revision"] + 1
            core.update_source("src/main.uny", edited, revision)
            state = core.read_source("src/main.uny")
            assert state["content"] == edited and state["dirty"], state
            assert source.read_text(encoding="utf-8") == original
            print("PASS: Core mirrors unsaved .uny edits without disk writes", flush=True)

            restored = core.restart_with_buffers([
                {"source": "src/main.uny", "content": edited, "revision": revision},
            ])
            assert restored["restored"] == 1, restored
            state = core.read_source("src/main.uny")
            assert state["content"] == edited and state["dirty"], state
            assert source.read_text(encoding="utf-8") == original
            print("PASS: Core restart restores unsaved editor buffer", flush=True)

            core.discard_source("src/main.uny")
            assert core.read_source("src/main.uny")["content"] == original
            assert not core.read_source("src/main.uny")["dirty"]
            assert core.close_source("src/main.uny")
            core.open_source("src/legacy.pnx")
            assert core.read_source("src/legacy.pnx")["content"] == legacy.read_text(encoding="utf-8")
            print("PASS: Core discard, close and legacy .pnx read", flush=True)
        finally:
            core.close()

        runner = ProjectRunner(project, compiler_python)
        try:
            runner.start(source="src/main.uny")
            result = runner.collect(timeout=30)
            assert result["exitCode"] == 0 and "ZUNYITE_RUN_OK" in result["output"], result
            print("PASS: real .uny Run Current File", flush=True)
        finally:
            runner.close()

    print("PASS: live Zunyite GUI + compiler + IDE Core gate", flush=True)


if __name__ == "__main__":
    main()

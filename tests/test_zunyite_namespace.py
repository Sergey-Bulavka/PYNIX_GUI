# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""New canonical GUI Python imports preserve the existing runtime API."""

from pathlib import Path
import tomllib

import pynix_gui
import zunyite_gui
from pynix_gui.backends import default_backend as legacy_backend
from zunyite_gui.backends import default_backend
from pynix_gui.layout import GUIRect as LegacyGUIRect
from zunyite_gui.layout import GUIRect


def test_zunyite_namespace_exports_same_public_runtime():
    assert zunyite_gui.__version__ == pynix_gui.__version__
    assert zunyite_gui.GUIRuntime is pynix_gui.GUIRuntime
    assert zunyite_gui.GUIWindow is pynix_gui.GUIWindow
    assert zunyite_gui.__all__ == pynix_gui.__all__
    assert default_backend is legacy_backend
    assert GUIRect is LegacyGUIRect


def test_zunyite_distribution_declares_both_namespaces():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    metadata = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert metadata["project"]["name"] == "zunyite-gui"
    include = metadata["tool"]["setuptools"]["packages"]["find"]["include"]
    assert "pynix_gui*" in include
    assert "zunyite_gui*" in include
    assert Path(zunyite_gui.__file__).with_name("py.typed").is_file()


def test_zunyite_owns_pure_text_implementation_without_class_duplication():
    import pynix_gui.text_metrics as legacy_metrics
    import zunyite_gui.text_metrics as canonical_metrics
    import pynix_gui.wrap_engine as legacy_wrap
    import zunyite_gui.wrap_engine as canonical_wrap

    assert canonical_metrics.GUITextExtent is legacy_metrics.GUITextExtent
    assert canonical_metrics.GUITextMetrics is legacy_metrics.GUITextMetrics
    assert canonical_metrics.snapshot_text_metrics is legacy_metrics.snapshot_text_metrics
    assert canonical_metrics.GUITextExtent.__module__ == "zunyite_gui.text_metrics"
    assert canonical_wrap.GUIWrappedText is legacy_wrap.GUIWrappedText
    assert canonical_wrap.wrap_text is legacy_wrap.wrap_text
    assert canonical_wrap.GUIWrappedText.__module__ == "zunyite_gui.wrap_engine"

    # Legacy class/function identity is important for isinstance, pickling,
    # platform backend imports, and compatibility with existing applications.
    wrapped = legacy_wrap.wrap_text(
        "Zunyite GUI", 90,
        measure_width=lambda value: len(value) * 5.0,
        line_height=14,
    )
    assert isinstance(wrapped, canonical_wrap.GUIWrappedText)
    assert wrapped.lines == ("Zunyite GUI",)


def test_canonical_ide_bridges_reuse_existing_service_types_and_functions():
    from zunyite_gui.ide_workspace_session import WorkspaceSession as CanonicalSession
    from pynix_gui.ide_workspace_session import WorkspaceSession as LegacySession
    from zunyite_gui.ide_core_persistent import PersistentCoreReader as CanonicalCore
    from pynix_gui.ide_core_persistent import PersistentCoreReader as LegacyCore
    from zunyite_gui.ide_project_runner import ProjectRunner as CanonicalRunner
    from pynix_gui.ide_project_runner import ProjectRunner as LegacyRunner
    from zunyite_gui.ide_debug_process_client import DebugProcessClient as CanonicalDebug
    from pynix_gui.ide_debug_process_client import DebugProcessClient as LegacyDebug
    from zunyite_gui.ide_workspace_preview import attach_workspace as canonical_attach
    from pynix_gui.ide_workspace_preview import attach_workspace as legacy_attach

    assert CanonicalSession is LegacySession
    assert CanonicalCore is LegacyCore
    assert CanonicalRunner is LegacyRunner
    assert CanonicalDebug is LegacyDebug
    assert canonical_attach is legacy_attach


def test_first_party_public_examples_use_canonical_gui_imports():
    examples = Path(__file__).resolve().parents[1] / "examples"
    for filename in (
        "adv_01_commands_smoke.py",
        "adv_02_tree_table_smoke.py",
        "adv_03_drag_dock_smoke.py",
        "adv_04_canvas_smoke.py",
        "adv_05_editor_smoke.py",
        "macos_smoke.py",
        "resources_smoke.py",
        "text_wrap_smoke.py",
        "showcase.py",
        "real_project_app.py",
    ):
        code = (examples / filename).read_text(encoding="utf-8")
        assert "from zunyite_gui import" in code, filename
        assert "from pynix_gui import" not in code, filename


def test_native_workspace_entrypoint_routes_core_run_debug_through_canonical_paths():
    root = Path(__file__).resolve().parents[1]
    source = (root / "examples" / "ide_native_v4.py").read_text(encoding="utf-8")
    for name in (
        "ide_workspace_session", "ide_workspace_preview", "ide_core_persistent",
        "ide_core_read_bridge", "ide_project_runner", "ide_debug_process_client",
        "ide_tooling_navigation", "ide_tooling_diagnostics", "ide_tooling_symbols",
    ):
        assert f"from zunyite_gui.{name} import" in source, name
        assert f"from pynix_gui.{name} import" not in source, name

# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import tomllib

import pynix_gui
from pynix_gui import GUIRuntime
from pynix_gui.backends import default_backend


def test_package_version_matches_pyproject_component_version():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    package_version = pynix_gui.__version__.replace("-dev", ".dev0")
    assert package_version == data["project"]["version"]


def test_typed_package_marker_is_present():
    marker = Path(pynix_gui.__file__).with_name("py.typed")
    assert marker.is_file()


def test_default_runtime_uses_platform_backend_selector(monkeypatch):
    import pynix_gui.backends

    sentinel = object()
    monkeypatch.setattr(pynix_gui.backends, "default_backend", lambda: sentinel)

    runtime = GUIRuntime.default()

    assert runtime.backend is sentinel


def test_unknown_platform_has_no_native_default_backend():
    assert default_backend(platform_name="unknown") is None

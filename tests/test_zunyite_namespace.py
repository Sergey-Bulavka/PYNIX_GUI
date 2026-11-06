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

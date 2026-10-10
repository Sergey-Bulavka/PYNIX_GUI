# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Verify release artifacts without requiring a GUI display server."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REQUIRED = {"pynix_gui/__init__.py", "pynix_gui/core.py",
            "pynix_gui/runtime.py", "pynix_gui/py.typed"}


def main():
    wheels = list(DIST.glob("pynix_gui-*.whl"))
    sdists = list(DIST.glob("pynix_gui-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("Expected exactly one PYNIX GUI wheel and one sdist")
    with zipfile.ZipFile(wheels[0]) as archive:
        missing = REQUIRED - set(archive.namelist())
        if missing:
            raise SystemExit(f"Wheel missing: {sorted(missing)}")
    with tarfile.open(sdists[0], "r:gz") as archive:
        names = archive.getnames()
        for name in REQUIRED:
            if not any(path.endswith("/" + name) for path in names):
                raise SystemExit(f"sdist missing: {name}")
    with tempfile.TemporaryDirectory() as folder:
        # System site-packages allows CI's already-installed platform backend
        # dependencies to remain available without downloading them twice.
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(folder)
        python = pathlib.Path(folder) / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
            check=True, stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [str(python), "-c",
             "import pynix_gui; from pynix_gui import GUIRuntime, GUIEvent; "
             "assert pynix_gui.__version__"],
            check=True,
        )
    print("Distribution structure and wheel import: PASS")


if __name__ == "__main__":
    main()

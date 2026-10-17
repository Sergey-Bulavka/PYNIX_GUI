# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Locate original Endpoints vectors in a locally installed JetBrains IDE.

The Endpoints tool-window art is shipped by some JetBrains IDE distributions,
but is not part of our redistributable Apache-licensed New UI icon catalog.
Do not imitate or redistribute that vector. Instead, load the original
SVG from the user's own local PyCharm installation at native IDE startup.

No network requests, generated paths, modified SVGs or third-party icons.
"""
from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import sys
from typing import Iterable
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


# Original JetBrains resource names documented by JetBrains icon-map
# replacement path references in existing IntelliJ platform themes.
# Prefer the canonical tool-window glyph over action/gutter variants.
_ENDPOINT_PATHS = (
    "icons/expui/toolwindows/endpoints.svg",
    "icons/expui/endpoints.svg",
    "icons/newui/endpoints.svg",
    "icons/expui/rails/endpoints.svg",
    "icons/rails/endpoints.svg",
    "icons/toolWindowEndpoints.svg",
    "icons/endpoints.svg",
)


def _sibling_variant(name: str, dark: bool) -> str:
    if not dark:
        return name
    return name.removesuffix(".svg") + "_dark.svg"


def _local_ide_roots() -> tuple[Path, ...]:
    home = Path.home()
    roots: list[Path] = []
    override = os.environ.get("PYNIX_JETBRAINS_APP_PATH", "").strip()
    if override:
        # This is a filesystem path, never an URL.
        roots.append(Path(override).expanduser())
    if sys.platform == "darwin":
        roots.extend((
            Path("/Applications"),
            home / "Applications",
            home / "Library/Application Support/JetBrains/Toolbox/apps",
            home / "Library/Application Support/JetBrains/Toolbox/apps/pycharm",
            home / "Library/Application Support/JetBrains/Toolbox/apps/pycharm-professional",
        ))
    return tuple(dict.fromkeys(roots))


def _official_ide_bundles(roots: Iterable[Path]) -> tuple[Path, ...]:
    bundles: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            # A directly supplied .jar is useful for explicit installations.
            if root.suffix.lower() == ".jar":
                bundles.append(root)
            continue
        if root.suffix.lower() == ".app":
            bundles.append(root)
            continue
        # Avoid walking every application or arbitrary user folder; only
        # JetBrains IDE bundles, also supporting JetBrains Toolbox versions.
        for pattern in (
            "PyCharm*.app",
            "IntelliJ IDEA*.app",
            "*/PyCharm*.app",
            "*/IntelliJ IDEA*.app",
            "*/*/PyCharm*.app",
            "*/*/IntelliJ IDEA*.app",
            "*/*/*/PyCharm*.app",
        ):
            bundles.extend(root.glob(pattern))
    return tuple(dict.fromkeys(bundles))


def _validate_svg(data: bytes) -> str | None:
    if len(data) > 65536 or len(data) < 40:
        return None
    lowered = data.lower()
    if any(bad in lowered for bad in (
        b"<!doctype", b"<!entity", b"<script", b"<foreignobject",
        b"javascript:", b"http://", b"https://",
    )):
        # SVG namespace declarations are allowed.
        lowered_without_namespace = lowered.replace(
            b'xmlns="http://www.w3.org/2000/svg"', b""
        )
        if any(bad in lowered_without_namespace for bad in (
            b"<!doctype", b"<!entity", b"<script", b"<foreignobject",
            b"javascript:", b"http://", b"https://",
        )):
            return None
    try:
        root = ElementTree.fromstring(data)
        if root.tag not in ("svg", "{http://www.w3.org/2000/svg}svg"):
            return None
        return data.decode("utf-8")
    except (UnicodeDecodeError, ElementTree.ParseError):
        return None


def _read_original_svg(archive: Path, *, dark: bool) -> str | None:
    try:
        with ZipFile(archive) as jar:
            paths = set(jar.namelist())
            # Some IDE variants use a light icon for both themes. Prefer
            # the exact dark variant when present; fall back to the unmodified
            # official light vector, never a synthesized dark SVG.
            candidates = (
                [_sibling_variant(n, True) for n in _ENDPOINT_PATHS]
                + list(_ENDPOINT_PATHS)
            ) if dark else list(_ENDPOINT_PATHS)
            for name in candidates:
                if name not in paths:
                    continue
                return _validate_svg(jar.read(name))
    except (OSError, BadZipFile, RuntimeError, ValueError):
        return None
    return None


@lru_cache(maxsize=8)
def _locate_endpoints_icon(dark: bool, roots: tuple[Path, ...]) -> str | None:
    for bundle in _official_ide_bundles(roots):
        archives = (bundle,) if bundle.is_file() else tuple(
            sorted((bundle / "Contents/plugins").rglob("*.jar"))
        ) + tuple(sorted((bundle / "Contents/lib").rglob("*.jar")))
        for archive in archives:
            svg = _read_original_svg(archive, dark=dark)
            if svg is not None:
                return svg
    return None


def original_endpoints_svg(
    *, dark: bool = True, roots: Iterable[Path] | None = None,
) -> str | None:
    """The *unmodified* Endpoints SVG from an installed JetBrains IDE, if any."""
    search_roots = _local_ide_roots() if roots is None else tuple(roots)
    return _locate_endpoints_icon(dark, search_roots)

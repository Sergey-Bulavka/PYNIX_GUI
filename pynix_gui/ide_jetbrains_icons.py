# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Licensed JetBrains New UI SVG catalog for PYNIX IDE.

The catalog deliberately does not assume that every PyCharm/IntelliJ asset is
freely reusable. Only files with their own Apache-2.0 notices are importable.
Product logos/trademarks are never imported.

Icons are indexed by their original category/path, rather than hard-coding a
small toolbar subset. For example, "actions/run" and "toolwindows/project".
The importer copies approved SVGs and writes a manifest with provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET

SOURCE_REPOSITORY = "https://github.com/JetBrains/intellij-community"
LICENSE_URL = "https://www.apache.org/licenses/LICENSE-2.0"
MANIFEST_VERSION = 1
MAX_SVG_SIZE = 256_000
APACHE_NOTICE = re.compile(r"Apache(?:[- ](?:License[, ]*))?[- ]2(?:\.0)?", re.I)
RESTRICTED_NAMES = re.compile(
    r"(?:^|[._/-])(pycharm|intellijidea|intellij-idea|jetbrains|productlogos?|splash|aboutlogo)(?:$|[._/-])",
    re.I,
)
SCRIPT_OR_REMOTE = re.compile(
    r"<\s*(?:script|foreignObject|iframe)\b|\bon[a-z]+\s*=|"
    r"(?:href|src)\s*=\s*['\"]\s*(?:https?:|javascript:|data:)|<!DOCTYPE|<!ENTITY",
    re.I,
)


def _source_key(relative: Path) -> tuple[str, str]:
    """Return stable icon key and exact SVG variant (normal/dark, scale)."""
    stem = relative.stem
    dark = stem.endswith("_dark")
    if dark:
        stem = stem[:-5]
    size = "normal"
    if stem.endswith("@20x20"):
        size, stem = "20", stem[:-6]
    elif stem.endswith("@16x16"):
        size, stem = "16", stem[:-6]
    elif stem.endswith("@2x"):
        size, stem = "2x", stem[:-3]
    key = (relative.parent / stem).as_posix()
    return key, ("dark_" if dark else "light_") + size


def check_svg(path: Path, *, relative_path: Path | None = None) -> tuple[bool, str]:
    """Reject unlicensed, unsafe, trademark-related or malformed SVG assets."""
    if path.suffix.lower() != ".svg":
        return False, "not-svg"
    if RESTRICTED_NAMES.search((relative_path or Path(path.name)).as_posix()):
        return False, "trademark"
    try:
        if path.stat().st_size > MAX_SVG_SIZE:
            return False, "oversized"
        source = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return False, "unreadable"
    # The original copyright/license header must travel with each icon.
    first_comment = source[:1500].split("-->", 1)[0]
    if "Copyright" not in first_comment or not APACHE_NOTICE.search(first_comment):
        return False, "license-not-explicit"
    if SCRIPT_OR_REMOTE.search(source):
        return False, "unsafe-svg"
    try:
        root = ET.fromstring(source)
    except ET.ParseError:
        return False, "malformed-svg"
    if root.tag not in ("svg", "{http://www.w3.org/2000/svg}svg"):
        return False, "not-svg-root"
    return True, "ok"


def build_catalog(source_dir: Path, destination: Path, *, dry_run: bool = False) -> dict:
    """Import ALL eligible SVGs recursively; record why anything was skipped.

    source_dir can be a checkout subtree such as:
      intellij-community/community/platform/icons/src/expui

    The existing destination is not deleted: files we don't own stay intact.
    A dry run never writes files or manifests.
    """
    source_dir, destination = Path(source_dir).resolve(), Path(destination).resolve()
    if not source_dir.is_dir():
        raise ValueError(f"Source icon directory not found: {source_dir}")
    if destination == source_dir or source_dir in destination.parents:
        raise ValueError("Destination must not be inside the source icon tree")
    entries: dict[str, dict[str, dict]] = {}
    skipped: dict[str, int] = {}
    for icon in sorted(source_dir.rglob("*.svg")):
        relative = icon.relative_to(source_dir)
        safe, reason = check_svg(icon, relative_path=relative)
        if not safe:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        key, variant = _source_key(relative)
        data = icon.read_bytes()
        target = destination / "svg" / relative
        entries.setdefault(key, {})[variant] = {
            "path": (Path("svg") / relative).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(icon, target)
    catalog = {
        "version": MANIFEST_VERSION,
        "source": SOURCE_REPOSITORY,
        "license": LICENSE_URL,
        "icons": dict(sorted(entries.items())),
        "skipped": dict(sorted(skipped.items())),
    }
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "manifest.json").write_text(
            json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return catalog


@dataclass(frozen=True)
class ResolvedIcon:
    key: str
    variant: str
    svg_path: Path
    sha256: str


class JetBrainsIconCatalog:
    """Lookup for every imported action, toolwindow, node and status icon."""

    def __init__(self, directory: Path):
        self.directory = Path(directory).resolve()
        manifest = json.loads((self.directory / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("version") != MANIFEST_VERSION:
            raise ValueError("Unsupported icon manifest version")
        self.icons: dict[str, dict] = manifest["icons"]

    def __len__(self) -> int:
        return len(self.icons)

    def names(self, prefix: str = "") -> Iterator[str]:
        for name in self.icons:
            if name.startswith(prefix):
                yield name

    def resolve(self, name: str, *, dark: bool = True,
                tool_window: bool = False, compact: bool = False) -> ResolvedIcon | None:
        """Prefer New UI 20px toolwindow SVG; otherwise choose matching theme."""
        variants = self.icons.get(name)
        if not variants:
            return None
        theme, alternate = ("dark", "light") if dark else ("light", "dark")
        size_order = ("16", "normal", "20", "2x") if compact else (
            ("20", "normal", "16", "2x") if tool_window else ("normal", "16", "20", "2x")
        )
        for variant in (theme, alternate):
            for size in size_order:
                label = f"{variant}_{size}"
                if label not in variants:
                    continue
                entry = variants[label]
                file = (self.directory / entry["path"]).resolve()
                if self.directory not in file.parents or not file.is_file():
                    continue
                return ResolvedIcon(name, label, file, entry["sha256"])
        return None

    def svg(self, name: str, *, dark: bool = True, tool_window: bool = False,
            compact: bool = False) -> str | None:
        """Read one imported licensed vector, with on-disk integrity checking."""
        icon = self.resolve(name, dark=dark, tool_window=tool_window, compact=compact)
        if icon is None:
            return None
        data = icon.svg_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != icon.sha256:
            raise ValueError(f"SVG differs from licensed manifest: {name}")
        return data.decode("utf-8-sig")


def main(argv: list[str] | None = None) -> int:
    """Offline importer: point at a locally checked out JetBrains expui tree."""
    import argparse
    parser = argparse.ArgumentParser(description="Import licensed JetBrains New UI SVGs")
    parser.add_argument("source", type=Path, help="Local expui directory from an IntelliJ checkout")
    parser.add_argument("destination", type=Path, help="PYNIX icon assets directory")
    parser.add_argument("--dry-run", action="store_true", help="Only count eligible icons")
    args = parser.parse_args(argv)
    manifest = build_catalog(args.source, args.destination, dry_run=args.dry_run)
    variants = sum(len(value) for value in manifest["icons"].values())
    print(f"Eligible icon names: {len(manifest['icons'])}; SVG variants: {variants}")
    print(f"Skipped SVG files: {manifest['skipped']}")
    if not args.dry_run:
        print(f"Catalog: {args.destination / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

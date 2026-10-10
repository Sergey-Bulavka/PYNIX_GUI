# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Read-only project filesystem model for GUI application examples.

The toolkit renders tree/table controls; the application owns filesystem I/O.
No AppKit, Qt or IDE-specific objects cross this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ProjectExplorerError(Exception):
    """A recoverable project/open/read failure suitable for a UI message."""


@dataclass(frozen=True)
class ProjectEntry:
    path: str  # Project-relative POSIX path. "" denotes the project root.
    name: str
    is_directory: bool
    size: int | None


class ProjectExplorer:
    """Safe, bounded navigation of an explicitly selected local project."""

    def __init__(self, root: str | Path, *, max_depth: int = 12):
        if not isinstance(max_depth, int) or isinstance(max_depth, bool) or max_depth < 1:
            raise ValueError("max_depth must be a positive integer")
        try:
            path = Path(root).expanduser().resolve(strict=True)
            if not path.is_dir():
                raise ProjectExplorerError("Project root must be a directory.")
        except OSError as exc:
            raise ProjectExplorerError(f"Cannot open project: {exc}") from exc
        self.root = path
        self.folder = ""
        self.selected: str | None = None
        self.last_opened: str | None = None
        self.max_depth = max_depth

    def _resolve(self, relative: str) -> Path:
        if not isinstance(relative, str) or relative.startswith("/") or "\\" in relative:
            raise ProjectExplorerError("Invalid project-relative path.")
        try:
            target = (self.root / relative).resolve(strict=True)
            target.relative_to(self.root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ProjectExplorerError("Path is missing or outside the project.") from exc
        return target

    def entries(self, folder: str | None = None) -> list[ProjectEntry]:
        relative = self.folder if folder is None else folder
        directory = self._resolve(relative)
        if not directory.is_dir():
            raise ProjectExplorerError("Selected path is not a directory.")
        try:
            results = []
            for item in directory.iterdir():
                # Do not follow symlinks, including symlinks to project directories.
                if item.is_symlink():
                    continue
                try:
                    is_dir = item.is_dir()
                    size = None if is_dir else item.stat().st_size
                except OSError:
                    continue  # One damaged/unreadable entry should not hide its siblings.
                results.append(ProjectEntry(
                    item.relative_to(self.root).as_posix(),
                    item.name,
                    is_dir,
                    size,
                ))
            return sorted(results, key=lambda e: (not e.is_directory, e.name.casefold(), e.name))
        except OSError as exc:
            raise ProjectExplorerError(f"Cannot list directory: {exc}") from exc

    def tree(self, folder: str = "", *, depth: int = 0) -> list[tuple[ProjectEntry, list]]:
        """Directory-first tree limited by depth and without symlink recursion."""
        if depth >= self.max_depth:
            return []
        return [
            (entry, self.tree(entry.path, depth=depth + 1) if entry.is_directory else [])
            for entry in self.entries(folder)
        ]

    def select(self, relative: str) -> bool:
        if relative not in {entry.path for entry in self.entries()}:
            return False
        self.selected = relative
        return True

    def open(self, relative: str | None = None) -> str | None:
        """Open a folder in-place or return the selected file path for an IDE."""
        candidate = relative if relative is not None else self.selected
        if candidate is None or candidate not in {entry.path for entry in self.entries()}:
            return None
        target = self._resolve(candidate)
        if target.is_dir():
            self.folder = candidate
            self.selected = None
            return None
        self.last_opened = candidate
        return candidate

    def up(self) -> bool:
        if not self.folder:
            return False
        self.folder = Path(self.folder).parent.as_posix()
        if self.folder == ".":
            self.folder = ""
        self.selected = None
        return True

    def read_pnx(self, relative: str, *, max_bytes: int = 2_000_000) -> str:
        """Read text for IDE handoff, rejecting non-PYNIX and oversized files."""
        if not relative.lower().endswith(".pnx"):
            raise ProjectExplorerError("Only .pnx source files can be opened in the IDE.")
        path = self._resolve(relative)
        if not path.is_file():
            raise ProjectExplorerError("Source path is not a file.")
        try:
            with path.open("rb") as file:
                data = file.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ProjectExplorerError("Source file is too large to open.")
            return data.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise ProjectExplorerError(f"Cannot read PYNIX source: {exc}") from exc

"""V4.2 workspace document model, independent of AppKit/WebKit.

This layer provides safe project-local source reads and editor tab state.
It does not run a compiler or perform Git operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import tempfile


class WorkspaceError(ValueError):
    pass


@dataclass
class WorkspaceDocument:
    path: str
    text: str
    saved_text: str

    @property
    def dirty(self) -> bool:
        return self.text != self.saved_text


@dataclass
class WorkspaceSession:
    root: Path
    documents: dict[str, WorkspaceDocument] = field(default_factory=dict)
    active: str | None = None

    def __post_init__(self):
        root = Path(self.root).expanduser().resolve()
        if not root.is_dir():
            raise WorkspaceError(f"Project directory does not exist: {root}")
        self.root = root

    def resolve_file(self, relative: str) -> Path:
        if not relative or Path(relative).is_absolute():
            raise WorkspaceError("Expected a relative project path")
        candidate = (self.root / relative).resolve()
        if not candidate.is_relative_to(self.root) or not candidate.is_file():
            raise WorkspaceError("File does not exist within the project")
        return candidate

    def list_files(self, *, limit: int = 1500) -> list[str]:
        found: list[str] = []
        ignored = {".git", ".venv", "__pycache__", "node_modules", ".worktrees"}
        for directory, dirs, files in __import__("os").walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in ignored and not d.startswith("."))
            for filename in sorted(files):
                path = Path(directory) / filename
                if path.is_symlink() or filename.startswith("."):
                    continue
                found.append(path.relative_to(self.root).as_posix())
                if len(found) >= limit:
                    return found
        return found

    def list_directories(self, *, limit: int = 10000) -> list[str]:
        """List directory nodes independently from file/content preview limits."""
        import os
        found: list[str] = []
        for directory, dirs, _files in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
            for name in dirs:
                path = Path(directory) / name
                found.append(path.relative_to(self.root).as_posix())
                if len(found) >= limit:
                    return found
            # Show but do not recursively scan environments, caches or Git metadata.
            dirs[:] = [d for d in dirs if d not in {
                ".git", ".venv", "__pycache__", "node_modules", ".worktrees",
            }]
        return found

    def open(self, relative: str) -> WorkspaceDocument:
        if relative not in self.documents:
            path = self.resolve_file(relative)
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeError, OSError) as exc:
                raise WorkspaceError("File is not readable UTF-8 source") from exc
            self.documents[relative] = WorkspaceDocument(relative, text, text)
        self.active = relative
        return self.documents[relative]

    def select(self, relative: str) -> WorkspaceDocument:
        if relative not in self.documents:
            raise WorkspaceError("Document is not open")
        self.active = relative
        return self.documents[relative]

    def update(self, relative: str, text: str) -> WorkspaceDocument:
        if relative not in self.documents:
            raise WorkspaceError("Document is not open")
        doc = self.documents[relative]
        doc.text = text
        return doc

    def save(self, relative: str) -> WorkspaceDocument:
        """Atomically persist an open document without overwriting external edits."""
        doc = self.documents.get(relative)
        if doc is None:
            raise WorkspaceError("Document is not open")
        path = self.resolve_file(relative)
        try:
            disk_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise WorkspaceError("Cannot read file before saving") from exc
        if disk_text != doc.saved_text:
            raise WorkspaceError("File changed on disk; reload or resolve conflict")
        if not doc.dirty:
            return doc
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="",
                dir=path.parent, prefix=".pynix-save-", delete=False,
            ) as output:
                temp_name = output.name
                output.write(doc.text)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(temp_name, path.stat().st_mode & 0o777)
            os.replace(temp_name, path)
        except OSError as exc:
            raise WorkspaceError("Failed to save document") from exc
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)
        doc.saved_text = doc.text
        return doc

    def close(self, relative: str, *, discard: bool = False) -> None:
        doc = self.documents.get(relative)
        if doc is None:
            return
        if doc.dirty and not discard:
            raise WorkspaceError("Unsaved document: confirm discard before closing")
        self.documents.pop(relative)
        if self.active == relative:
            self.active = next(reversed(self.documents), None)

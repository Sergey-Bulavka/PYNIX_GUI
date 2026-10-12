"""Read-only Git snapshot for the PYNIX IDE workspace preview.

Git data is read from an explicit project root. No mutating Git commands.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class GitChange:
    status: str
    path: str


@dataclass(frozen=True)
class GitSnapshot:
    branch: str
    changes: tuple[GitChange, ...]
    history: tuple[str, ...]
    available: bool = True


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), "--no-optional-locks", *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5,
        check=False,
        env={"PATH": __import__("os").environ.get("PATH", "/usr/bin:/bin"),
             "GIT_OPTIONAL_LOCKS": "0", "GIT_CONFIG_NOSYSTEM": "1",
             "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"},
    )
    if result.returncode:
        raise RuntimeError("Git is unavailable or repository command failed")
    return result.stdout


def read_git_snapshot(root: Path, *, max_changes: int = 150,
                      max_history: int = 8) -> GitSnapshot:
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Project directory does not exist")
    try:
        top = Path(__import__("os").fsdecode(
            _git(root, "rev-parse", "--show-toplevel").strip())).resolve()
        if top != root:
            # Do not accidentally inspect a parent repository.
            return GitSnapshot("", (), (), False)
        branch = _git(root, "branch", "--show-current").decode("utf-8", "replace").strip()
        raw = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=normal")
        changes = []
        records = raw.split(b"\0")
        index = 0
        while index < len(records) and records[index] and len(changes) < max_changes:
            entry = records[index]
            status = entry[:2].decode("ascii", "replace")
            path = entry[3:].decode("utf-8", "replace")
            if status[0] in "RC" or status[1] in "RC":
                index += 1  # Extra original-path field for rename/copy entries.
            changes.append(GitChange(status, path))
            index += 1
        log_bytes = _git(root, "log", "-n", str(max_history), "--format=%h %s")
        history = tuple(line for line in log_bytes.decode("utf-8", "replace").splitlines() if line)
        return GitSnapshot(branch or "(detached HEAD)", tuple(changes), history)
    except (RuntimeError, subprocess.TimeoutExpired, OSError, UnicodeError):
        return GitSnapshot("", (), (), False)

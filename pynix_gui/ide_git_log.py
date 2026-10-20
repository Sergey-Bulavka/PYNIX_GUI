# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Bounded, read-only Git Log / branches / worktrees for the native PYNIX IDE.

No shell, checkouts, fetches, mutation, pager or Git hooks. Every request is
anchored to the explicitly opened project root. SHA and path operations are
validated before any subprocess is launched.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Any

_SHA = re.compile(r"^[0-9a-fA-F]{40,64}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class GitLogError(ValueError):
    """A safe, user-visible failure when Git metadata cannot be read."""


def _read(root: Path, *arguments: str, timeout: float = 8, max_bytes: int = 850_000) -> bytes:
    env = dict(os.environ)
    env.update({
        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_PAGER": "cat", "LC_ALL": "C",
    })
    try:
        p = subprocess.run(
            ["git", "-C", str(root), "--no-optional-locks", *arguments],
            cwd=str(root), env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitLogError("Git is unavailable or the command timed out") from exc
    if p.returncode != 0:
        detail = p.stderr.decode("utf-8", "replace").strip().splitlines()
        raise GitLogError(("Git command failed: " + (detail[0] if detail else "unknown error"))[:230])
    if len(p.stdout) > max_bytes:
        raise GitLogError("Git output exceeds the safe display limit")
    return p.stdout


def _root(path: Path) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise GitLogError("Project directory does not exist")
    top = Path(os.fsdecode(_read(root, "rev-parse", "--show-toplevel").strip())).resolve()
    if top != root:
        raise GitLogError("No Git repository at this project root")
    return root


def _text(raw: bytes) -> str:
    return raw.decode("utf-8", "replace")


def _references(root: Path) -> tuple[list[dict[str, str]], set[str]]:
    lines = _text(_read(root, "for-each-ref",
                        "--format=%(refname)%00%(objectname)",
                        "refs/heads", "refs/remotes", "refs/tags")).splitlines()
    out: list[dict[str, str]] = []
    names: set[str] = set()
    for line in lines[:2000]:
        parts = line.split("\x00")
        if len(parts) < 2:
            continue
        full, sha = parts[:2]
        if full.startswith("refs/heads/"):
            kind, name = "local", full[len("refs/heads/"):]
        elif full.startswith("refs/remotes/"):
            kind, name = "remote", full[len("refs/remotes/"):]
        elif full.startswith("refs/tags/"):
            kind, name = "tag", full[len("refs/tags/"):]
        else:
            continue
        out.append({"name": name, "full": full, "kind": kind, "sha": sha})
        names.add(full)
    return out, names


def _worktrees(root: Path) -> list[dict[str, Any]]:
    data = _text(_read(root, "worktree", "list", "--porcelain")).splitlines()
    out: list[dict[str, Any]] = []
    item: dict[str, Any] = {}
    for row in data + [""]:
        if not row:
            if item:
                out.append(item)
            item = {}
        elif row.startswith("worktree "):
            item["path"] = row[9:]
        elif row.startswith("HEAD "):
            item["sha"] = row[5:]
        elif row.startswith("branch "):
            item["branch"] = row[7:].removeprefix("refs/heads/")
        elif row == "detached":
            item["detached"] = True
        elif row.startswith("locked"):
            item["locked"] = row[6:].strip() or True
        elif row.startswith("prunable"):
            item["prunable"] = row[8:].strip() or True
    return out[:100]


def _validated_path(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 1000 or "\x00" in value:
        raise GitLogError("Invalid project-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or value.startswith("-"):
        raise GitLogError("Git path must stay inside the project")
    return value


def read_git_log(root: Path, *, branch: str = "", text: str = "",
                 user: str = "", since: str = "", until: str = "",
                 path: str = "", limit: int = 250) -> dict[str, Any]:
    """Return a bounded log plus local/remote refs and worktrees.

    Filtering is performed by Git on all history (not just the first page).
    The log never contains synthetic/demo commits.
    """
    root = _root(root)
    limit = min(400, max(1, int(limit)))
    refs, valid_refs = _references(root)
    # Branch --show-current is empty in detached-HEAD mode.
    try:
        current = _text(_read(root, "branch", "--show-current")).strip()
    except GitLogError:
        current = ""
    args = ["log", "--all", "--topo-order", "--date-order", "--no-show-signature",
            "--format=%x1e%H%x1f%P%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%D",
            "-n", str(limit)]
    if branch:
        # Only known refnames, never a revision expression or option.
        matches = [ref for ref in refs if ref["full"] == branch or
                   ref["name"] == branch]
        if len(matches) != 1 or matches[0]["full"] not in valid_refs:
            raise GitLogError("Unknown or ambiguous Git branch/tag")
        args[1] = matches[0]["full"]
        args.remove("--all")
    if text:
        if len(text) > 160:
            raise GitLogError("Search text is too long")
        # --fixed-strings means user text is never a regular expression.
        args.extend(["--regexp-ignore-case", "--fixed-strings", "--grep=" + text])
    if user:
        if len(user) > 140:
            raise GitLogError("Author filter is too long")
        # CLI --author supports regex; escape user input to mean literal text.
        args.append("--author=" + re.escape(user))
    for key, value in (("--since", since), ("--until", until)):
        if value:
            if not _DATE.fullmatch(value):
                raise GitLogError("Dates must use YYYY-MM-DD")
            args.append(key + "=" + (value + " 23:59:59" if key == "--until" else value))
    if path:
        args.extend(["--", _validated_path(path)])
    try:
        raw = _text(_read(root, *args))
    except GitLogError as exc:
        # An empty freshly initialized Git repository has no HEAD yet.
        if "does not have any commits yet" not in str(exc) and "bad revision" not in str(exc):
            raise
        raw = ""
    commits = []
    for record in raw.split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip("\r\n ").split("\x1f")
        if len(parts) < 7 or not _SHA.fullmatch(parts[0]):
            continue
        sha, parents, author, email, date, subject, decorations = parts[:7]
        commits.append({
            "sha": sha, "parents": parents.split() if parents else [],
            "author": author, "email": email, "date": date,
            "subject": subject, "refs": decorations,
        })
    return {
        "available": True, "branch": current or "(detached HEAD)",
        "refs": refs, "worktrees": _worktrees(root), "commits": commits,
        "truncated": len(commits) >= limit,
    }


def read_git_commit(root: Path, sha: str) -> dict[str, Any]:
    """Inspect an exact commit; never accept revision syntax such as HEAD~1."""
    root = _root(root)
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise GitLogError("Invalid full commit hash")
    content = _text(_read(root, "show", "-s",
                          "--format=%H%x1f%P%x1f%an%x1f%ae%x1f%aI%x1f%B",
                          sha)).strip().split("\x1f", 5)
    if len(content) != 6:
        raise GitLogError("Cannot read the selected commit")
    raw = _read(root, "diff-tree", "--root", "--no-commit-id",
                "--name-status", "-r", "-z", sha)
    fields = raw.split(b"\x00")
    changes: list[dict[str, str]] = []
    index = 0
    while index < len(fields) and fields[index] and len(changes) < 300:
        status = _text(fields[index]).strip()
        index += 1
        if index >= len(fields):
            break
        old_path = ""
        filename = _text(fields[index])
        index += 1
        if status.startswith(("R", "C")):
            old_path, filename = filename, (_text(fields[index]) if index < len(fields) else "")
            index += 1
        changes.append({"status": status, "path": filename, "from": old_path})
    return {
        "sha": content[0], "parents": content[1].split(),
        "author": content[2], "email": content[3],
        "date": content[4], "message": content[5],
        "files": changes,
    }


def read_git_diff(root: Path, sha: str, path: str) -> dict[str, str]:
    """Bounded read-only unified diff for an explicitly selected commit and file."""
    root = _root(root)
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise GitLogError("Invalid full commit hash")
    path = _validated_path(path)
    commit = read_git_commit(root, sha)
    if not any(file["path"] == path for file in commit["files"]):
        raise GitLogError("File is not part of the selected commit")
    try:
        diff = _text(_read(root, "show", "--no-ext-diff", "--no-textconv",
                           "--format=", "--unified=3", "--no-color",
                           sha, "--", path, max_bytes=100_000))
    except GitLogError as exc:
        if "safe display limit" in str(exc):
            return {"sha": sha, "path": path, "diff": "",
                    "error": "Diff is too large for the built-in viewer"}
        raise
    return {"sha": sha, "path": path, "diff": diff}

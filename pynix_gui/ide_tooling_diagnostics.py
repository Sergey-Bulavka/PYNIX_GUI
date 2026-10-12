"""Read-only adapter for PYNIX's public tooling diagnostics protocol V1.

Never imports compiler internals; invokes public CLI with an explicit interpreter.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from pathlib import Path


@dataclass(frozen=True)
class Problem:
    source: str
    line: int
    column: int
    code: str
    message: str


@dataclass(frozen=True)
class DiagnosticSnapshot:
    problems: tuple[Problem, ...]
    error: str = ""


def read_diagnostics(project_root: Path, compiler_python: Path, *,
                     timeout: float = 20, limit: int = 200) -> DiagnosticSnapshot:
    root = Path(project_root).resolve()
    executable = Path(compiler_python).resolve()
    manifest = root / "pynix.toml"
    if not manifest.is_file():
        return DiagnosticSnapshot((), "No pynix.toml project manifest")
    if not executable.is_file():
        return DiagnosticSnapshot((), "Compiler Python executable not found")
    try:
        completed = subprocess.run(
            [str(executable), "-m", "compiler", "tooling", "diagnostics", str(root)],
            cwd=root, capture_output=True, text=True, timeout=timeout, check=False,
        )
        if completed.returncode:
            return DiagnosticSnapshot((), "Compiler tooling returned an error")
        payload = json.loads(completed.stdout)
        if (not isinstance(payload, dict) or payload.get("protocol") != "pynix-tooling"
                or payload.get("version") != 1 or payload.get("kind") != "diagnostics"
                or not isinstance(payload.get("diagnostics"), list)):
            return DiagnosticSnapshot((), "Unexpected compiler tooling protocol")
        problems = []
        for item in payload["diagnostics"][:limit]:
            if not isinstance(item, dict):
                continue
            start = item.get("start") or {}
            if not isinstance(start, dict):
                start = {}
            problems.append(Problem(
                source=str(item.get("source") or ""),
                line=max(1, int(start.get("line") or 1)),
                column=max(1, int(start.get("column") or 1)),
                code=str(item.get("code") or ""),
                message=str(item.get("message") or ""),
            ))
        return DiagnosticSnapshot(tuple(problems))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return DiagnosticSnapshot((), "Compiler tooling unavailable")

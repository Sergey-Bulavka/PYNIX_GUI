"""Read-only public PYNIX tooling navigation adapter.

Queries are explicit user actions, never implicit compilation on each click.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess

KINDS = {"definition": "definition", "references": "references", "type-at": "typeAt"}


def query_navigation(root: Path, python: Path, command: str, source: str,
                     line: int, column: int, *, timeout: int = 20) -> dict:
    if command not in KINDS:
        raise ValueError("Unsupported language tooling command")
    root = Path(root).resolve()
    python = Path(python).resolve()
    requested = (root / source).resolve()
    if not requested.is_relative_to(root) or requested.suffix != ".pnx" or not requested.is_file():
        raise ValueError("Select a PYNIX source inside the project")
    if line < 1 or column < 1:
        raise ValueError("Line and column are one-based")
    if not python.is_file():
        raise ValueError("Compiler interpreter unavailable")
    try:
        result = subprocess.run(
            [str(python), "-m", "compiler", "tooling", command, str(root),
             str(requested), str(line), str(column)],
            cwd=root, capture_output=True, text=True, timeout=timeout, check=False,
        )
        if result.returncode:
            return {"error": "Compiler tooling query failed"}
        data = json.loads(result.stdout)
        if (not isinstance(data, dict) or data.get("protocol") != "pynix-tooling"
            or data.get("version") != 1 or data.get("kind") != KINDS[command]):
            return {"error": "Unsupported tooling protocol response"}
        return data
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return {"error": "Compiler tooling unavailable"}

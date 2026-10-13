"""Bounded, read-only PYNIX tooling symbols adapter for IDE completion."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess


def read_symbols(project_root: Path, compiler_python: Path, *,
                 timeout: float = 20, limit: int = 1200) -> dict:
    root = Path(project_root).resolve()
    interpreter = Path(compiler_python).resolve()
    if not (root / "pynix.toml").is_file() or not interpreter.is_file():
        return {"error": "Project manifest or compiler interpreter unavailable", "symbols": []}
    try:
        completed = subprocess.run(
            [str(interpreter), "-m", "compiler", "tooling", "symbols", str(root)],
            cwd=root, capture_output=True, text=True, check=False, timeout=timeout,
        )
        if completed.returncode:
            return {"error": "Compiler symbol lookup failed", "symbols": []}
        payload = json.loads(completed.stdout)
        if (not isinstance(payload, dict) or payload.get("protocol") != "pynix-tooling"
                or payload.get("version") != 1 or payload.get("kind") != "symbols"
                or not isinstance(payload.get("symbols"), list)):
            return {"error": "Unexpected compiler symbols protocol", "symbols": []}
        result = []
        for item in payload["symbols"][:limit]:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if (isinstance(name, str) and 0 < len(name) <= 128
                    and name.isidentifier() and name.isascii()):
                result.append({"name": name, "kind": str(item.get("kind") or "")[:32]})
        return {"symbols": result}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"error": "Compiler symbol lookup unavailable", "symbols": []}

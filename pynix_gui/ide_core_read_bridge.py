"""Read-only snapshot transport from the official Zunyite_IDE Core.

A fresh isolated Zunyite process has no knowledge of unsaved V4 buffers.
Never use this snapshot as the V4 editor's authoritative buffer until a
persistent shared IDE session is implemented in the next milestone.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

class CoreSnapshotError(ValueError):
    pass

def _string_literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)

def read_core_snapshot(ide_repo: Path, project: Path, compiler_python: Path,
                       *, source: str | None = None, timeout: int = 30) -> dict:
    ide_repo = Path(ide_repo).resolve()
    project = Path(project).resolve()
    compiler_python = Path(compiler_python).resolve()
    source_suffix = ".uny" if (ide_repo / "src" / "ide_session.uny").is_file() else ".pnx"
    if not (ide_repo / "src" / f"ide_session{source_suffix}").is_file():
        raise CoreSnapshotError("Official IDE Core repository is unavailable")
    if not any((project / name).is_file() for name in ("zunyite.toml", "pynix.toml")):
        raise CoreSnapshotError("Snapshot project must have a pynix.toml")
    if not compiler_python.is_file():
        raise CoreSnapshotError("Zunyite compiler interpreter is unavailable")
    if source is not None:
        if (not source or not source.endswith((".uny", ".pnx"))
                or not (project / source).resolve().is_relative_to(project)
                or not (project / source).is_file()):
            raise CoreSnapshotError("Source must be a Zunyite file inside project")
    with tempfile.TemporaryDirectory(prefix="pynix-ide-read-") as work:
        root = Path(work)
        dest = root / "src"
        dest.mkdir()
        for filename in (f"ide_session{source_suffix}", f"project{source_suffix}", f"tooling{source_suffix}"):
            shutil.copy2(ide_repo / "src" / filename, dest / filename)
        (root / ("zunyite.toml" if source_suffix == ".uny" else "pynix.toml")).write_text(
            f'[project]\nname = "zunyite-ide-read"\nsource = "src"\nentry = "main{source_suffix}"\n',
            encoding="utf-8",
        )
        program = [
            "import ide_session", "",
            "function main()",
            "    ide = ide_session.newIdeSession()",
            "    result = ide.openProject(" + _string_literal(str(project)) + ")",
        ]
        if source is not None:
            program.append("    ide.openSource(" + _string_literal(source) + ")")
        program += ["    print(Json.write(ide.workspaceReadSnapshot()))", ""]
        (dest / f"main{source_suffix}").write_text("\n".join(program), encoding="utf-8")
        env = os.environ.copy()
        # Compiler discovery follows the same configurable PYTHONPATH used in IDE tests.
        env.setdefault("PYTHONPATH", str(next((p for p in (ide_repo.parent / "Zunyite", ide_repo.parent / "PYNIX") if p.is_dir()), ide_repo.parent / "Zunyite")))
        try:
            result = subprocess.run(
                [str(compiler_python), "-m", "compiler", "run", str(root)],
                cwd=root, env=env, text=True, capture_output=True,
                timeout=timeout, check=False,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise CoreSnapshotError("Unable to query official IDE Core") from exc
    if result.returncode:
        raise CoreSnapshotError("IDE Core snapshot failed: " + (result.stderr or result.stdout)[-600:])
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    try:
        payload = json.loads(lines[-1]) if lines else None
    except (ValueError, TypeError) as exc:
        raise CoreSnapshotError("Malformed IDE Core snapshot") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("projectOpen"), bool):
        raise CoreSnapshotError("Invalid IDE Core snapshot contract")
    return payload

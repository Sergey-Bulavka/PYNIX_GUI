"""Persistent, read-only subprocess adapter for the official PYNIX_IDE Core.

The subprocess owns one IdeSession; Workspace V4 keeps its current editor and
save implementation until single-owner migration is independently verified.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import threading

from .ide_core_read_bridge import CoreSnapshotError


class PersistentCoreReader:
    def __init__(self, ide_repo: Path, project: Path, compiler_python: Path, *,
                 timeout: float = 20.0):
        self.ide_repo = Path(ide_repo).resolve()
        self.project = Path(project).resolve()
        self.compiler_python = Path(compiler_python).resolve()
        self.timeout = timeout
        self._temporary = None
        self._process = None
        self._lines = queue.Queue()
        self._thread = None

    def start(self) -> dict:
        if self._process is not None:
            raise CoreSnapshotError("IDE Core is already running")
        if not (self.ide_repo / "src" / "workspace_read_host.pnx").is_file():
            raise CoreSnapshotError("Persistent IDE Core host is missing; update PYNIX_IDE")
        if not (self.project / "pynix.toml").is_file():
            raise CoreSnapshotError("Project manifest missing")
        if not self.compiler_python.is_file():
            raise CoreSnapshotError("Compiler interpreter missing")
        self._temporary = tempfile.TemporaryDirectory(prefix="pynix-ide-core-")
        try:
            root = Path(self._temporary.name)
            source_dir = root / "src"
            source_dir.mkdir()
            for filename in ("workspace_read_host.pnx", "ide_session.pnx", "project.pnx", "tooling.pnx"):
                shutil.copy2(self.ide_repo / "src" / filename, source_dir / filename)
            (root / "pynix.toml").write_text(
                '[project]\nname = "pynix-ide-core"\nsource = "src"\nentry = "workspace_read_host.pnx"\n',
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.setdefault("PYTHONPATH", str(self.ide_repo.parent / "PYNIX"))
            self._process = subprocess.Popen(
                [str(self.compiler_python), "-u", "-m", "compiler", "run", str(root)],
                cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, bufsize=1,
            )
            self._thread = threading.Thread(target=self._read_stdout, daemon=True)
            self._thread.start()
            reply = self.request({"command": "openProject", "path": str(self.project)})
            if not reply["value"].get("opened"):
                raise CoreSnapshotError("IDE Core rejected project")
            return self.snapshot()
        except Exception:
            self.close()
            raise

    def _read_stdout(self):
        try:
            for line in self._process.stdout:
                try:
                    packet = json.loads(line.strip())
                    if isinstance(packet, dict) and "ok" in packet and "kind" in packet:
                        self._lines.put(packet)
                except ValueError:
                    continue
        finally:
            self._lines.put(None)

    def request(self, command: dict) -> dict:
        process = self._process
        if process is None or process.poll() is not None:
            raise CoreSnapshotError("IDE Core process is not running")
        if process.stdin is None:
            raise CoreSnapshotError("IDE Core stdin is unavailable")
        try:
            process.stdin.write(json.dumps(command, ensure_ascii=False) + "\n")
            process.stdin.flush()
            result = self._lines.get(timeout=self.timeout)
        except (OSError, BrokenPipeError, queue.Empty) as exc:
            raise CoreSnapshotError("IDE Core request failed or timed out") from exc
        if result is None:
            raise CoreSnapshotError("IDE Core process closed its output")
        if not result.get("ok"):
            raise CoreSnapshotError(str(result.get("value", {}).get("message", "IDE Core rejected request")))
        return result

    def snapshot(self) -> dict:
        result = self.request({"command": "snapshot"})
        if result["kind"] != "snapshot" or not isinstance(result.get("value"), dict):
            raise CoreSnapshotError("Invalid IDE Core snapshot")
        return result["value"]

    def open_source(self, source: str) -> dict:
        if (not isinstance(source, str) or not source.endswith(".pnx")
                or not (self.project / source).resolve().is_relative_to(self.project)
                or not (self.project / source).is_file()):
            raise CoreSnapshotError("Invalid project source")
        result = self.request({"command": "openSource", "source": source})
        if result["kind"] != "snapshot" or not isinstance(result.get("value"), dict):
            raise CoreSnapshotError("Invalid IDE Core source response")
        return result["value"]

    def update_source(self, source: str, content: str) -> dict:
        if not isinstance(content, str) or len(content.encode("utf-8")) > 1_000_000:
            raise CoreSnapshotError("Invalid source content")
        if (not isinstance(source, str) or not source.endswith(".pnx")
                or not (self.project / source).resolve().is_relative_to(self.project)
                or not (self.project / source).is_file()):
            raise CoreSnapshotError("Invalid project source")
        result = self.request({"command": "updateSource", "source": source, "content": content})
        snapshot = result.get("value")
        if result.get("kind") != "snapshot" or not isinstance(snapshot, dict):
            raise CoreSnapshotError("Invalid Core edit acknowledgment")
        if snapshot.get("activeSourceContent") != content:
            raise CoreSnapshotError("Core editor buffer differs from V4")
        return snapshot

    def close(self):
        process = self._process
        self._process = None
        if process is not None:
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()
                    process.wait(timeout=2)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None

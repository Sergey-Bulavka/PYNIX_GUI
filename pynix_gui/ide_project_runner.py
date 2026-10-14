"""Bounded PYNIX project execution controller for the native IDE.

No shell, no arbitrary executable selected by web content. One process per
workspace; output is captured and bounded, with explicit stop and cleanup.
"""
from __future__ import annotations
from pathlib import Path
import subprocess
import threading

class RunError(ValueError):
    pass

class ProjectRunner:
    def __init__(self, root: Path, compiler_python: Path):
        self.root = Path(root).resolve()
        self.python = Path(compiler_python).resolve()
        self.process: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self.process is not None and self.process.poll() is None:
                raise RunError("A PYNIX process is already running")
            if not (self.root / "pynix.toml").is_file():
                raise RunError("A pynix.toml project manifest is required")
            if not self.python.is_file():
                raise RunError("PYNIX compiler interpreter is unavailable")
            self.process = subprocess.Popen(
                [str(self.python), "-m", "compiler", "run", str(self.root)],
                cwd=self.root, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1, start_new_session=True,
            )

    def collect(self, *, limit: int = 200_000, timeout: float = 90) -> dict:
        with self._lock:
            proc = self.process
        if proc is None:
            raise RunError("No PYNIX process running")
        try:
            stdout, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.stop()
            stdout, _ = proc.communicate(timeout=5)
            return {"exitCode": proc.returncode, "output": stdout[:limit], "timedOut": True}
        finally:
            with self._lock:
                if self.process is proc:
                    self.process = None
        return {"exitCode": proc.returncode, "output": stdout[:limit],
                "truncated": len(stdout) > limit}

    def stop(self) -> bool:
        with self._lock:
            proc = self.process
        if proc is None or proc.poll() is not None:
            return False
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        return True

    def close(self) -> None:
        self.stop()

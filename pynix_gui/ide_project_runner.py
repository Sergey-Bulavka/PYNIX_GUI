"""Bounded PYNIX project execution controller for the native IDE.

No shell, no arbitrary executable selected by web content. One process per
workspace; output is captured and bounded, with explicit stop and cleanup.
"""
from __future__ import annotations
from pathlib import Path
import subprocess
import threading
from collections.abc import Callable

class RunError(ValueError):
    pass

class ProjectRunner:
    def __init__(self, root: Path, compiler_python: Path):
        self.root = Path(root).resolve()
        self.python = Path(compiler_python).resolve()
        self.process: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def start(self, *, mode: str = "run") -> None:
        if mode not in {"run", "check"}:
            raise RunError("Unsupported run configuration")
        with self._lock:
            if self.process is not None and self.process.poll() is None:
                raise RunError("A PYNIX process is already running")
            if not (self.root / "pynix.toml").is_file():
                raise RunError("A pynix.toml project manifest is required")
            if not self.python.is_file():
                raise RunError("PYNIX compiler interpreter is unavailable")
            self.process = subprocess.Popen(
                [str(self.python), "-u", "-m", "compiler", mode, str(self.root)],
                cwd=self.root, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1, start_new_session=True,
            )

    def collect(self, *, limit: int = 200_000, timeout: float = 90,
                on_output: Callable[[str], None] | None = None) -> dict:
        """Stream bounded output while process runs; never wait for all output first."""
        with self._lock:
            proc = self.process
        if proc is None:
            raise RunError("No PYNIX process running")
        if proc.stdout is None:
            raise RunError("Runner has no output pipe")
        collected: list[str] = []
        total = 0
        timed_out = False
        truncated = False
        completed = threading.Event()

        def watchdog():
            if not completed.wait(timeout):
                nonlocal timed_out
                if proc.poll() is None:
                    timed_out = True
                    self.stop()

        timer = threading.Thread(target=watchdog, daemon=True)
        timer.start()
        try:
            for chunk in iter(proc.stdout.readline, ""):
                remaining = max(0, limit - total)
                if remaining:
                    excerpt = chunk[:remaining]
                    collected.append(excerpt)
                    total += len(excerpt)
                    if on_output:
                        on_output(excerpt)
                if len(chunk) > remaining:
                    truncated = True
            proc.wait()
        finally:
            completed.set()
            with self._lock:
                if self.process is proc:
                    self.process = None
        return {"exitCode": proc.returncode, "output": "".join(collected),
                "truncated": truncated, "timedOut": timed_out}

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

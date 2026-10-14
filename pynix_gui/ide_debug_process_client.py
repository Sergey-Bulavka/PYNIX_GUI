"""Safe host-side adapter for experimental PYNIX debugger worker.

Only the native host chooses interpreter, project and source. Browser code
cannot inject commands or arbitrary paths into the subprocess.
"""
from __future__ import annotations

from pathlib import Path
from threading import RLock
from uuid import uuid4

import json
import os
import queue
import select
import threading
import subprocess
import time


class DebugClientError(ValueError):
    pass


class DebugProcessClient:
    def __init__(self, root: Path, python: Path):
        self.root = Path(root).resolve()
        # Keep the venv path: resolve() can follow its executable symlink
        # outside the PYNIX checkout, losing the compiler package root.
        self.python = Path(python).absolute()
        self._lock = RLock()
        self._worker = None
        self._session = None

    def launch(self, source: str) -> dict:

        with self._lock:
            if self._worker is not None:
                raise DebugClientError("Debugger already running")
            if not isinstance(source, str) or not source.endswith(".pnx"):
                raise DebugClientError("Choose a PYNIX source file")
            target = (self.root / source).resolve()
            if not target.is_relative_to(self.root) or not target.is_file():
                raise DebugClientError("Source outside project")
            if (self.root / source).is_symlink():
                raise DebugClientError("Symlink source is not allowed")
            worker = _Worker(self.python, self.root)
            try:
                worker.start()
                session = uuid4().hex
                worker.send({"protocol": "pynix-debug", "version": 1,
                             "command": "launch", "session": session, "source": source})
                response = worker.receive()
                if response.get("event") != "started":
                    raise DebugClientError(str(response.get("message", "Debug launch failed")))
                if response.get("state") == "finished":
                    # A short program can exit before launch() receives its reply.
                    # Preserve the final response but do not retain a dead worker.
                    worker.close()
                    return response
                self._worker = worker
                self._session = session
                return response
            except BaseException:
                worker.close()
                raise

    def command(self, action: str) -> dict:
        with self._lock:
            if self._worker is None or self._session is None:
                raise DebugClientError("No active debugger session")
            if action not in {"pause", "continue", "stepInto", "stepOver",
                              "stepOut", "stack", "variables", "status", "stop"}:
                raise DebugClientError("Unknown debugger action")
            try:
                self._worker.send({"protocol": "pynix-debug", "version": 1,
                                   "command": action, "session": self._session})
                result = self._worker.receive()
            except (OSError, ValueError, EOFError):
                # The worker may have exited or the pipe may be corrupt.
                # Never retain an unusable native debugger process.
                self.close()
                raise
            if action == "stop" or result.get("state") == "finished":
                self.close()
            return result

    def set_breakpoints(self, entries: list[dict]) -> dict:
        if not isinstance(entries, list) or len(entries) > 256:
            raise DebugClientError("Invalid breakpoint list")
        normalized = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise DebugClientError("Invalid breakpoint")
            source, line = entry.get("source"), entry.get("line")
            if (not isinstance(source, str) or not source.endswith(".pnx")
                    or type(line) is not int or line < 1):
                raise DebugClientError("Invalid breakpoint location")
            target = self.root / source
            if (Path(source).is_absolute() or ".." in Path(source).parts
                    or not target.resolve().is_relative_to(self.root)
                    or not target.is_file()):
                raise DebugClientError("Breakpoint source outside project")
            normalized.append({"source": source, "line": line})
        with self._lock:
            if self._worker is None or self._session is None:
                raise DebugClientError("No active debugger session")
            try:
                self._worker.send({"protocol": "pynix-debug", "version": 1,
                                   "command": "setBreakpoints", "session": self._session,
                                   "breakpoints": normalized})
                return self._worker.receive()
            except (OSError, ValueError, EOFError):
                self.close()
                raise

    def close(self):
        with self._lock:
            worker = self._worker
            self._worker = None
            self._session = None
            if worker is not None:
                worker.close()


class _Worker:
    """No import dependency on compiler inside the GUI Python environment."""
    def __init__(self, python, root):
        self.python, self.root = Path(python), Path(root)
        self._stderr_file = None
        self.process = None
        self._pending = bytearray()
        self._windows_chunks = None

    def start(self):
        if not self.python.is_file():
            raise DebugClientError("PYNIX compiler interpreter unavailable")
        import tempfile
        env = os.environ.copy()
        # A project is not the compiler checkout: the native IDE runs from
        # the project directory, while the compiler lives beside its venv.
        for parent in self.python.absolute().parents:
            if (parent / "compiler" / "debug_worker.py").is_file():
                env["PYTHONPATH"] = os.pathsep.join(
                    filter(None, (str(parent), env.get("PYTHONPATH", ""))))
                break
        self._stderr_file = tempfile.TemporaryFile(mode="w+b")
        self.process = subprocess.Popen(
            [str(self.python), "-u", "-m", "compiler.debug_worker"],
            cwd=self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self._stderr_file, env=env, start_new_session=True)
        message = self.receive()
        if message.get("event") != "ready":
            raise DebugClientError("Debug worker not ready")

    def send(self, packet):
        raw = json.dumps(packet, ensure_ascii=False).encode("utf-8")
        if len(raw) > 65536:
            raise DebugClientError("Debugger message too large")
        self.process.stdin.write(raw + b"\n")
        self.process.stdin.flush()

    def receive(self, timeout=5.0):
        """Read one bounded line without blocking the native UI indefinitely.

        Use unbuffered OS reads: select() combined with a buffered readline()
        can strand already-prefetched bytes and cause false timeouts.
        """
        deadline = time.monotonic() + timeout
        while b"\n" not in self._pending:
            if len(self._pending) > 65537:
                raise DebugClientError("Debugger sent oversized response")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise DebugClientError("Debugger response timed out")
            if os.name == 'nt':
                if self._windows_chunks is None:
                    self._windows_chunks = queue.Queue()
                    target = self._windows_chunks
                    fd = self.process.stdout.fileno()
                    def pump():
                        try:
                            while True:
                                data = os.read(fd, 4096)
                                target.put(data)
                                if not data:
                                    break
                        except OSError:
                            target.put(b'')
                    threading.Thread(target=pump, daemon=True).start()
                try:
                    chunk = self._windows_chunks.get(timeout=remaining)
                except queue.Empty as error:
                    raise DebugClientError("Debugger response timed out") from error
            else:
                readable, _, _ = select.select([self.process.stdout.fileno()], [], [], remaining)
                if not readable:
                    raise DebugClientError("Debugger response timed out")
                chunk = os.read(self.process.stdout.fileno(), 4096)
            if not chunk:
                details = ""
                if self._stderr_file is not None and self.process.poll() is not None:
                    self._stderr_file.seek(0)
                    details = self._stderr_file.read(4096).decode("utf-8", errors="replace").strip()
                raise DebugClientError(
                    "Debugger closed unexpectedly" + (": " + details[-500:] if details else "")
                )
            self._pending.extend(chunk)
        line, _, rest = self._pending.partition(b"\n")
        self._pending = bytearray(rest)
        if len(line) > 65536:
            raise DebugClientError("Debugger sent oversized response")
        try:
            data = json.loads(line.decode("utf-8"))
        except (UnicodeError, ValueError) as error:
            raise DebugClientError("Invalid debugger response") from error
        if not isinstance(data, dict) or data.get("protocol") != "pynix-debug" or data.get("version") != 1:
            raise DebugClientError("Unexpected debugger protocol")
        return data

    def close(self):
        proc = self.process
        self.process = None
        if proc is not None:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=2)
            for stream in (proc.stdin, proc.stdout):
                if stream is not None:
                    stream.close()
        if self._stderr_file is not None:
            self._stderr_file.close()
            self._stderr_file = None

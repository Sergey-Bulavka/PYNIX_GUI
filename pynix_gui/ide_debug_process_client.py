"""Safe host-side adapter for experimental PYNIX debugger worker.

Only the native host chooses interpreter, project and source. Browser code
cannot inject commands or arbitrary paths into the subprocess.
"""
from __future__ import annotations

from pathlib import Path
from threading import RLock
from uuid import uuid4

from pynix_gui.ide_workspace_session import WorkspaceError


class DebugClientError(ValueError):
    pass


class DebugProcessClient:
    def __init__(self, root: Path, python: Path):
        self.root = Path(root).resolve()
        self.python = Path(python).resolve()
        self._lock = RLock()
        self._worker = None
        self._session = None

    def launch(self, source: str) -> dict:
        from compiler.debug_worker_process import DebugWorkerProcess
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
            worker = DebugWorkerProcess(self.python, self.root)
            try:
                worker.start()
                session = uuid4().hex
                worker.send({"protocol": "pynix-debug", "version": 1,
                             "command": "launch", "session": session, "source": source})
                response = worker.receive()
                if response.get("event") != "started":
                    raise DebugClientError(str(response.get("message", "Debug launch failed")))
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
                              "stepOut", "stack", "variables", "stop"}:
                raise DebugClientError("Unknown debugger action")
            self._worker.send({"protocol": "pynix-debug", "version": 1,
                               "command": action, "session": self._session})
            result = self._worker.receive()
            if action == "stop":
                self.close()
            return result

    def close(self):
        with self._lock:
            worker = self._worker
            self._worker = None
            self._session = None
            if worker is not None:
                worker.close()

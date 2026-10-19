# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Real native V4 terminal sessions: PTYs and a separate PYNIX command console.

All subprocesses run as the current local user. No shell is started until the
user explicitly creates a tab. The UI never treats process output as HTML.
"""
from __future__ import annotations

import codecs
import os
from pathlib import Path
import select
import shlex
import signal
import subprocess
import sys
import threading
import uuid


class TerminalSessionError(ValueError):
    pass


SHELLS = {"bash": "/bin/bash", "zsh": "/bin/zsh"}


class LocalTerminalSessions:
    """Independent responsive PTYs; no blocking reads on the WK UI thread.

    A configurable safety ceiling protects the desktop from accidental PTY
    exhaustion; it is not a visible tab-count restriction.
    """

    def __init__(self, cwd: Path, limit: int = 64):
        self.cwd = Path(cwd).resolve()
        self.limit = limit
        self._sessions: dict[str, tuple[subprocess.Popen, int, object, str]] = {}

    def create(self, shell: str) -> dict:
        if shell not in SHELLS or not Path(SHELLS[shell]).is_file():
            raise TerminalSessionError("Available shells: bash, zsh")
        if len(self._sessions) >= self.limit:
            raise TerminalSessionError(
                f"Maximum of {self.limit} concurrent terminal sessions"
            )
        if os.name != "posix":
            raise TerminalSessionError("PTY shell sessions require macOS/POSIX")
        master, slave = os.openpty()
        try:
            env = {**os.environ, "TERM": "dumb", "PYNIX_PROJECT_ROOT": str(self.cwd)}
            proc = subprocess.Popen(
                [SHELLS[shell], "-i"], cwd=self.cwd,
                stdin=slave, stdout=slave, stderr=slave,
                env=env, start_new_session=True, close_fds=True,
            )
        except Exception:
            os.close(master)
            raise
        finally:
            os.close(slave)
        sid = uuid.uuid4().hex
        self._sessions[sid] = (proc, master,
                               codecs.getincrementaldecoder("utf-8")("replace"), shell)
        return {"kind": "created", "id": sid, "shell": shell}

    def write(self, sid: str, data: str) -> dict:
        state = self._sessions.get(sid)
        if state is None:
            raise TerminalSessionError("Unknown terminal session")
        if not isinstance(data, str) or len(data.encode("utf-8")) > 8192:
            raise TerminalSessionError("Terminal input exceeds 8 KiB")
        proc, master, _, _ = state
        if proc.poll() is not None:
            raise TerminalSessionError("Shell has exited")
        try:
            os.write(master, data.encode("utf-8"))
        except OSError as exc:
            raise TerminalSessionError(str(exc)) from exc
        return {"kind": "wrote", "id": sid}

    def poll(self, sid: str, max_bytes: int = 32768) -> dict:
        state = self._sessions.get(sid)
        if state is None:
            raise TerminalSessionError("Unknown terminal session")
        proc, master, decoder, _ = state
        chunks = []
        size = 0
        try:
            while size < max_bytes and select.select([master], [], [], 0)[0]:
                chunk = os.read(master, min(4096, max_bytes - size))
                if not chunk:
                    break
                chunks.append(decoder.decode(chunk))
                size += len(chunk)
        except OSError:
            pass  # EIO signals a PTY whose subprocess has exited.
        return {
            "kind": "output", "id": sid,
            "data": "".join(chunks),
            "exited": proc.poll() is not None,
            "exitCode": proc.poll(),
        }

    def close(self, sid: str) -> dict:
        state = self._sessions.pop(sid, None)
        if state is None:
            raise TerminalSessionError("Unknown terminal session")
        proc, master, _, _ = state
        try:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGHUP)
                try:
                    proc.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    proc.terminate()
        except (OSError, ProcessLookupError):
            pass
        finally:
            os.close(master)
        return {"kind": "closed", "id": sid}

    def shutdown(self) -> None:
        for sid in list(self._sessions):
            try:
                self.close(sid)
            except OSError:
                pass


class PynixCommandConsole:
    """Independent PYNIX CLI console, intentionally NOT a Python REPL.

    A proper inline expression REPL needs a separate language Design Gate.
    Here the supported commands execute the actual language/compiler safely
    against files inside the selected project.
    """

    def __init__(self, root: Path, python: Path):
        self.root = Path(root).resolve()
        self.python = Path(python)
        self._lock = threading.Lock()

    def execute(self, command: str) -> str:
        if not isinstance(command, str) or len(command) > 2000:
            return "Command too long."
        try:
            tokens = shlex.split(command.strip())
        except ValueError as exc:
            return "Syntax error: " + str(exc)
        if not tokens:
            return ""
        if tokens[0] == "help":
            return ("PYNIX Console\n"
                    "  help                  Available commands\n"
                    "  pwd                   Current project\n"
                    "  files                 Project .pnx files\n"
                    "  run path/to/file.pnx  Compile and run a PYNIX program\n"
                    "Commands execute in the PYNIX project; this is not a Python shell.")
        if tokens == ["pwd"]:
            return str(self.root)
        if tokens == ["files"]:
            return "\n".join(str(p.relative_to(self.root)) for p in
                             list(self.root.rglob("*.pnx"))[:100])
        if len(tokens) != 2 or tokens[0] != "run":
            return "Unknown PYNIX command. Type help."
        path = (self.root / tokens[1]).resolve()
        if not path.is_relative_to(self.root) or path.suffix != ".pnx" or not path.is_file():
            return "Only existing .pnx files inside the project can be run."
        if not self._lock.acquire(blocking=False):
            return "Another PYNIX command is still running."
        try:
            result = subprocess.run(
                [str(self.python), "-m", "compiler", "run",
                 str(path.relative_to(self.root)), "--single-file"],
                cwd=self.root, capture_output=True, text=True, errors="replace",
                timeout=25, env={**os.environ, "PYTHONPATH": str(self.root)},
                check=False,
            )
            output = result.stdout + result.stderr
            return (output[-100_000:] or f"Process exited {result.returncode}.")
        except (OSError, subprocess.TimeoutExpired) as exc:
            return "PYNIX execution failed: " + str(exc)
        finally:
            self._lock.release()

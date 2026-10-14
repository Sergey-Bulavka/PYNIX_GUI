"""Experimental native debugger IPC integration contracts."""
from pathlib import Path
from pynix_gui.ide_debug_process_client import DebugProcessClient, DebugClientError
import pytest


def test_client_rejects_bad_debug_sources(tmp_path):
    executable = tmp_path / "python"
    executable.write_text("", encoding="utf-8")
    client = DebugProcessClient(tmp_path, executable)
    for source in ("../escape.pnx", "missing.pnx", "/tmp/source.pnx"):
        with pytest.raises(DebugClientError):
            client.launch(source)


def test_native_debug_bridge_uses_background_worker_and_safe_ui():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    view = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert 'controller.addScriptMessageHandler_name_(debug_command_handler, "pynixDebugCommand")' in native
    assert 'run_threading.Thread(target=job, daemon=True).start()' in native
    assert 'debug_client.close()' in native
    assert 'window.pynixDebugResult=packet=>' in view
    assert "window.webkit?.messageHandlers?.pynixDebugCommand" in view


def test_worker_reads_multiple_packets_without_losing_prefetched_bytes():
    import json
    import os
    from types import SimpleNamespace
    from pynix_gui.ide_debug_process_client import _Worker

    read_fd, write_fd = os.pipe()
    worker = _Worker(Path("/usr/bin/python3"), Path("."))
    with os.fdopen(read_fd, "rb", buffering=0) as reader:
        worker.process = SimpleNamespace(stdout=reader)
        packets = [
            {"protocol": "pynix-debug", "version": 1, "event": "ready"},
            {"protocol": "pynix-debug", "version": 1, "event": "started"},
        ]
        try:
            os.write(write_fd, b"".join(json.dumps(p).encode() + b"\n" for p in packets))
            assert worker.receive(timeout=0.1)["event"] == "ready"
            assert worker.receive(timeout=0.1)["event"] == "started"
        finally:
            os.close(write_fd)


def test_worker_response_timeout_is_bounded():
    import os
    from types import SimpleNamespace
    from pynix_gui.ide_debug_process_client import _Worker

    read_fd, write_fd = os.pipe()
    worker = _Worker(Path("/usr/bin/python3"), Path("."))
    with os.fdopen(read_fd, "rb", buffering=0) as reader:
        worker.process = SimpleNamespace(stdout=reader)
        try:
            with pytest.raises(DebugClientError, match="timed out"):
                worker.receive(timeout=0.01)
        finally:
            os.close(write_fd)


def test_worker_rejects_oversized_response():
    import os
    from threading import Thread
    from types import SimpleNamespace
    from pynix_gui.ide_debug_process_client import _Worker

    read_fd, write_fd = os.pipe()
    worker = _Worker(Path("/usr/bin/python3"), Path("."))
    with os.fdopen(read_fd, "rb", buffering=0) as reader:
        worker.process = SimpleNamespace(stdout=reader)

        def send_large_packet():
            try:
                os.write(write_fd, b"x" * 65537 + b"\n")
            finally:
                os.close(write_fd)

        producer = Thread(target=send_large_packet)
        producer.start()
        try:
            with pytest.raises(DebugClientError, match="oversized"):
                worker.receive(timeout=2.0)
        finally:
            producer.join(timeout=2.0)


def test_client_releases_broken_worker_after_command_failure(tmp_path):
    class BrokenWorker:
        def __init__(self):
            self.closed = False

        def send(self, packet):
            assert packet["command"] == "stack"

        def receive(self):
            raise DebugClientError("Debugger response timed out")

        def close(self):
            self.closed = True

    client = DebugProcessClient(tmp_path, tmp_path / "python")
    worker = BrokenWorker()
    client._worker = worker
    client._session = "active"
    with pytest.raises(DebugClientError, match="timed out"):
        client.command("stack")
    assert worker.closed
    assert client._worker is None
    assert client._session is None
    with pytest.raises(DebugClientError, match="No active"):
        client.command("stack")


def test_debug_toolbar_serializes_requests_and_reports_experimental_state():
    root = Path(__file__).resolve().parents[1]
    source = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "let debugBusy=false;" in source
    assert "debugControls.set(action,control);" in source
    assert "control.disabled=debugBusy" in source
    assert "debugBusy=true;" in source
    assert "debugBusy=false;" in source
    assert "if(event==='started'){debugActive=state!=='finished';" in source
    assert "if(event==='exited'||state==='finished')" in source
    assert "Debug (experimental" in source


def test_debugger_navigation_requires_paused_valid_project_location():
    root = Path(__file__).resolve().parents[1]
    source = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "if(debugState==='paused'&&location&&" in source
    assert "byName.has(location.source)" in source
    assert "Number.isSafeInteger(location.line)&&location.line>0" in source
    assert "Number.isSafeInteger(location.column)&&location.column>0" in source
    assert "new CustomEvent('pynix:navigate'" in source


def test_client_rejects_breakpoints_outside_project(tmp_path):
    (tmp_path / "main.pnx").write_text("pass", encoding="utf-8")
    client = DebugProcessClient(tmp_path, tmp_path / "python")
    for entries in ([{"source": "../escape.pnx", "line": 1}],
                    [{"source": "/tmp/test.pnx", "line": 1}],
                    [{"source": "main.pnx", "line": True}],
                    [{}], [{}] * 257):
        with pytest.raises(DebugClientError):
            client.set_breakpoints(entries)


def test_client_transmits_project_breakpoints(tmp_path):
    (tmp_path / "main.pnx").write_text("pass", encoding="utf-8")
    class Worker:
        def __init__(self):
            self.packet = None
        def send(self, packet):
            self.packet = packet
        def receive(self):
            return {"protocol": "pynix-debug", "version": 1,
                    "command": "setBreakpoints", "breakpoints": 1}
    client = DebugProcessClient(tmp_path, tmp_path / "python")
    client._worker = Worker()
    client._session = "s1"
    result = client.set_breakpoints([{"source": "main.pnx", "line": 1}])
    assert result["breakpoints"] == 1
    assert client._worker.packet["session"] == "s1"
    assert client._worker.packet["command"] == "setBreakpoints"

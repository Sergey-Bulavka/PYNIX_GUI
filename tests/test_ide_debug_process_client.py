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

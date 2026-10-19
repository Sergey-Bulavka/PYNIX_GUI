"""Regression tests for creating more than eight native Terminal tabs.

Use fake process and file descriptors: no shells or PTYs are created in tests.
"""
import os
import sys

import pytest

from pynix_gui import ide_terminal_sessions as terminals


@pytest.mark.skipif(os.name != "posix", reason="Native PTYs require POSIX")
def test_can_create_nine_sessions_and_enforces_configurable_safety_ceiling(
    monkeypatch, tmp_path
):
    backend = terminals.LocalTerminalSessions(tmp_path)
    assert backend.limit == 64

    class FakeProcess:
        def poll(self):
            return None

    monkeypatch.setattr(terminals, "SHELLS", {"bash": sys.executable})
    monkeypatch.setattr(terminals.os, "openpty", lambda: (150, 151))
    monkeypatch.setattr(terminals.os, "close", lambda fd: None)
    monkeypatch.setattr(
        terminals.subprocess, "Popen", lambda *args, **kwargs: FakeProcess()
    )

    opened = [backend.create("bash") for _ in range(9)]
    assert len({item["id"] for item in opened}) == 9
    assert len(backend._sessions) == 9

    [backend.create("bash") for _ in range(55)]
    assert len(backend._sessions) == 64
    with pytest.raises(terminals.TerminalSessionError, match="Maximum of 64"):
        backend.create("bash")


@pytest.mark.skipif(os.name != "posix", reason="Native PTYs require POSIX")
def test_custom_limit_reports_its_actual_value(tmp_path):
    backend = terminals.LocalTerminalSessions(tmp_path, limit=2)
    backend._sessions = {"first": None, "second": None}
    with pytest.raises(terminals.TerminalSessionError, match="Maximum of 2"):
        backend.create("bash")

"""Services V1 regression tests: registry, SSE transport and native UI."""
import json
import threading
import uuid
from collections import deque
from pathlib import Path

import pytest

from pynix_gui.ide_project_services import ProjectServices, ServicesError, _endpoint


def test_mcp_sse_url_requires_https_outside_loopback():
    assert _endpoint("http://127.0.0.1:8765/sse").endswith("/sse")
    assert _endpoint("https://mcp.example.org/sse") == "https://mcp.example.org/sse"
    for url in ("http://example.org/sse", "file:///etc/passwd", "ftp://server",
                "https://me:pass@server/sse", "https://server/sse#fragment"):
        with pytest.raises(ServicesError):
            _endpoint(url)


def test_project_profiles_are_isolated_and_persisted_safely(tmp_path):
    profiles = tmp_path / "profiles"
    a = ProjectServices(tmp_path / "projectA", config_dir=profiles)
    b = ProjectServices(tmp_path / "projectB", config_dir=profiles)
    item = a.add("MCP Local", "http://localhost:8765/sse")
    assert uuid.UUID(item["id"])
    assert a.path != b.path
    assert b.list()["services"] == []
    assert a.path.stat().st_mode & 0o077 == 0
    same_project = ProjectServices(tmp_path / "projectA", config_dir=profiles)
    assert same_project.list()["services"][0]["name"] == "MCP Local"
    with pytest.raises(ServicesError, match="already exists"):
        a.add("mcp local", "http://localhost:4000/sse")
    a.remove(item["id"])
    assert a.list()["services"] == []


def test_registration_never_invents_connected_sessions(tmp_path):
    services = ProjectServices(tmp_path, config_dir=tmp_path / "conf")
    profile = services.add("codex-mcp-client", "https://example.org/sse")
    row = services.list()["services"][0]
    assert row["state"] == "disconnected"
    assert row["events"] == []
    assert row["tools"] == []
    assert row["name"] == profile["name"]


def test_sse_initialize_and_tools_are_actual_stream_messages(monkeypatch, tmp_path):
    services = ProjectServices(tmp_path, config_dir=tmp_path / "conf")
    profile = services.add("Local", "http://localhost:8765/sse")
    id_ = profile["id"]
    lines = iter([
        b"event: endpoint\n",
        b"data: /messages?session=123\n",
        b"\n",
        b"event: message\n",
        b'data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n',
        b"\n",
        b"event: message\n",
        b'data: {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"search"},{"name":"read"}]}}\n',
        b"\n",
        b"",
    ])

    class Response:
        headers = {"Content-Type": "text/event-stream"}
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def readline(self, *_): return next(lines)
        def close(self): pass

    sent = []
    monkeypatch.setattr(services._opener, "open", lambda *_a, **_k: Response())
    monkeypatch.setattr(services, "_send", lambda sid, url, body:
                        sent.append((sid, url, body)))
    state = {"state": "connecting", "since": 0, "error": "",
             "tools": [], "events": deque(maxlen=100),
             "stop": threading.Event(), "response": None}
    services._connections[id_] = state
    services._listen(id_, profile, state)
    assert state["tools"] == ["search", "read"]
    assert [body["method"] for _, _, body in sent] == [
        "initialize", "notifications/initialized", "tools/list"
    ]
    assert all(url == "http://localhost:8765/messages?session=123"
               for _, url, _ in sent)
    assert state["state"] == "error"  # Fake stream closed; no false active session.


def test_mcp_sse_rejects_cross_origin_post_endpoint(monkeypatch, tmp_path):
    services = ProjectServices(tmp_path, config_dir=tmp_path / "conf")
    profile = services.add("Local", "http://localhost:8765/sse")
    lines = iter([b"event: endpoint\n", b"data: https://attacker.invalid/post\n",
                  b"\n", b""])
    class Response:
        headers = {"Content-Type": "text/event-stream"}
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def readline(self, *_): return next(lines)
    monkeypatch.setattr(services._opener, "open", lambda *_a, **_k: Response())
    state = {"state": "connecting", "since": 0, "error": "",
             "tools": [], "events": deque(maxlen=100),
             "stop": threading.Event(), "response": None}
    services._connections[profile["id"]] = state
    services._listen(profile["id"], profile, state)
    assert state["state"] == "error"
    assert "same origin" in state["error"]


def test_services_sidebar_and_dock_are_isolated_from_project_and_packages():
    root = Path(__file__).resolve().parents[1]
    edge = (root / "pynix_gui/ide_edge_profile.py").read_text(encoding="utf-8")
    dock = (root / "pynix_gui/ide_terminal_dock.py").read_text(encoding="utf-8")
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    workspace = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    ui = (root / "pynix_gui/ide_services_dock.py").read_text(encoding="utf-8")
    assert '("Services", "toolwindows/services", "left-bottom", "existing")' in edge
    assert '"Services": "services-window"' in edge
    assert "window.pynixTerminalDock?.toggleServices?.();" in edge
    assert "const toggleServices=()=>select('services');" in dock
    assert "servicesPane.hidden=!(visible&&scope==='services');" in dock
    assert "packagesPane.hidden=!(visible&&scope==='packages');" in dock
    assert 'TERMINAL_DOCK_JS.replace("__PYNIX_PACKAGES_DOCK__", PACKAGES_DOCK_JS).replace("__PYNIX_SERVICES_DOCK__", SERVICES_DOCK_JS)' in workspace
    assert "window.pynixServicesRunEvent?.(packet);" in workspace
    assert "controller.addScriptMessageHandler_name_(services_handler, \"pynixServices\")" in native
    assert "services_registry.close()" in native
    assert ".pynix-services-pane[hidden]" in chrome
    assert "window.pynixServicesResult=result=>" in ui
    assert "Run Configuration → " in ui
    assert "MCP SSE Connection" in ui
    assert "Session</button>" in ui
    assert "Tool Calls</button>" in ui
    assert "setExplorerVisible(" not in ui
    assert "document.querySelectorAll('.rail-item')" not in ui


def test_services_do_not_auto_call_remote_tools():
    source = (Path(__file__).resolve().parents[1] / "pynix_gui" /
              "ide_project_services.py").read_text(encoding="utf-8")
    assert '"method": "initialize"' in source
    assert '"method": "tools/list"' in source
    assert '"method": "tools/call"' not in source


def test_services_tree_and_options_actions_are_real_not_inert():
    root = Path(__file__).resolve().parents[1]
    ui = (root / "pynix_gui/ide_services_dock.py").read_text(encoding="utf-8")
    css = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    backend = (root / "pynix_gui/ide_project_services.py").read_text(encoding="utf-8")
    assert 'data-sv="toolbar"' in ui
    assert 'data-sv="optionsMenu"' in ui
    assert 'data-sv="sessionTab"' in ui
    assert 'data-sv="callsTab"' in ui
    assert "svCollapsed.add('Run Configurations')" in ui
    assert "svCollapsed.add('MCP SSE')" in ui
    assert "svCollapsed.clear();svDraw();" in ui
    assert "title.addEventListener('click',()=>{" in ui
    assert "svGrouped=!svGrouped;svDraw();" in ui
    assert "servicesPane.classList.toggle('hide-tree')" in ui
    assert ".pynix-services-pane.hide-tree .pynix-services-sidebar" in css
    assert "sv('toolbar').contains(event.target)" in ui
    assert '"version": "0.1.0"' in backend
    assert "svField(session,'Version',item.version||'—')" in ui
    assert "const svDuration=seconds=>{" in ui
    assert "svDuration(Date.now()/1000-item.since)" in ui


def test_service_profiles_do_not_accept_credentials_or_remote_plaintext(tmp_path):
    registry = ProjectServices(tmp_path, config_dir=tmp_path / "cfg")
    for url in ("http://127.0.0.2:8888/sse", "http://example.com/sse",
                "https://user:secret@example.com/sse"):
        with pytest.raises(ServicesError):
            registry.add("insecure", url)
    assert registry.list()["services"] == []

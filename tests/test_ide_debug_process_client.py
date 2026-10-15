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
    assert "debugActive=state!=='finished';debugState=state||'paused';" in source
    assert "event==='exited'||state==='finished'" in source
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


def test_native_bridge_routes_breakpoint_updates_to_client():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    assert '"setBreakpoints"' in native
    assert "debug_client.set_breakpoints(breakpoints)" in native


def test_editor_gutter_toggles_and_transmits_real_breakpoints():
    root = Path(__file__).resolve().parents[1]
    source = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "const breakpoints=new Map();" in source
    assert "gutter.addEventListener('click',event=>" in source
    assert "if(!current||debugBusy||debugActive)return;" in source
    assert "if(lines.has(line))lines.delete(line);else lines.add(line);" in source
    assert "function collectBreakpoints()" in source
    assert "bridge.postMessage({action:'setBreakpoints',breakpoints:entries});" in source
    assert "command==='setBreakpoints'" in source


def test_native_debugger_marks_paused_line_and_structures_inspection():
    root = Path(__file__).resolve().parents[1]
    source = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "pynix-debug-execution-line" in source
    assert "function updateDebugExecutionLine()" in source
    assert "debugLocation={source:location.source,line:location.line,column:location.column};" in source
    assert "if(debugState!=='paused')debugLocation=null;" in source
    assert "renderSection('CALL STACK',view.frames" in source
    assert "renderSection('LOCALS',view.variables" in source
    assert "panel.replaceChildren();" in source
    assert "row.textContent=format(item);" in source


def test_debug_inspection_is_serialized_and_nonrecursive():
    root = Path(__file__).resolve().parents[1]
    source = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "let debugInspectPhase=null;" in source
    assert "debugInspectPhase='variables';" in source
    assert "bridge?.postMessage({action:'variables',source:current});" in source
    assert "bridge?.postMessage({action:'stack',source:current});" in source
    assert "['continue','status','stepInto','stepOver','stepOut','setBreakpoints','pause'].includes(command)" in source
    assert "debugFrames=[];debugVariables=[];" in source
    assert "debugLocation={source:location.source,line:location.line,column:location.column};" in source


def test_native_debug_disconnect_releases_ui_session():
    root = Path(__file__).resolve().parents[1]
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert '"disconnected" if disconnected else "error"' in native
    assert "else if(event==='disconnected'){debugActive=false;debugState='disconnected';}" in preview
    assert "event==='error'||event==='disconnected'" in preview
    assert "if(debugState!=='paused')debugLocation=null;" in preview


def test_client_closes_worker_when_program_finishes_naturally(tmp_path):
    class FinishedWorker:
        closed = False
        def send(self, packet):
            assert packet["command"] == "stack"
        def receive(self):
            return {"protocol": "pynix-debug", "version": 1,
                    "command": "stack", "state": "finished"}
        def close(self):
            self.closed = True

    client = DebugProcessClient(tmp_path, tmp_path / "python")
    worker = FinishedWorker()
    client._worker = worker
    client._session = "active"
    assert client.command("stack")["state"] == "finished"
    assert worker.closed
    assert client._worker is None
    assert client._session is None


def test_debugger_program_output_is_bounded_and_rendered_as_text():
    root = Path(__file__).resolve().parents[1]
    source = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "let debugOutput=[];" in source
    assert "if(action==='launch'){" in source
    assert "debugOutput=[];" in source
    assert "typeof packet?.output==='string'" in source
    assert "if(debugOutput.length>100)debugOutput=debugOutput.slice(-100);" in source
    assert "outputTitle.textContent='PROGRAM OUTPUT';" in source
    assert "outputText.textContent=debugOutput.join(" in source
    assert "panel.append(outputTitle,outputText);" in source


def test_client_does_not_retain_worker_if_program_finishes_during_launch(tmp_path, monkeypatch):
    from pynix_gui import ide_debug_process_client as bridge

    source = tmp_path / "main.pnx"
    source.write_text("function main()\\n    print(1)\n", encoding="utf-8")
    created = []

    class FinishedWorker:
        def __init__(self, python, root):
            self.closed = False
            created.append(self)

        def start(self):
            pass

        def send(self, packet):
            assert packet["command"] == "launch"

        def receive(self):
            return {"protocol": "pynix-debug", "version": 1,
                    "event": "started", "state": "finished", "output": "1"}

        def close(self):
            self.closed = True

    monkeypatch.setattr(bridge, "_Worker", FinishedWorker)
    client = DebugProcessClient(tmp_path, tmp_path / "python")
    first = client.launch("main.pnx")
    assert first["output"] == "1"
    assert created[0].closed
    assert client._worker is None
    assert client._session is None
    second = client.launch("main.pnx")
    assert second["state"] == "finished"
    assert created[1].closed


@pytest.mark.parametrize("action", ["continue", "stepInto", "stop"])
def test_debugger_finished_reply_preserves_final_output_and_releases_worker(tmp_path, action):
    class FinishingWorker:
        def __init__(self):
            self.closed = False

        def send(self, packet):
            assert packet["command"] == action
            assert packet["session"] == "live"

        def receive(self):
            return {"protocol": "pynix-debug", "version": 1,
                    "command": action, "state": "finished",
                    "output": "last line"}

        def close(self):
            self.closed = True

    client = DebugProcessClient(tmp_path, tmp_path / "python")
    worker = FinishingWorker()
    client._worker = worker
    client._session = "live"
    result = client.command(action)
    assert result["output"] == "last line"
    assert result["state"] == "finished"
    assert worker.closed
    assert client._worker is None
    assert client._session is None


def test_real_debug_worker_pipe_lifecycle_without_private_compiler(tmp_path):
    """Exercise actual subprocess pipes and JSON framing on every CI OS."""
    import json
    import sys
    from pynix_gui.ide_debug_process_client import _Worker

    package = tmp_path / "compiler"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "debug_worker.py").write_text(
        "import json, sys\n"
        "def send(event):\n"
        "    sys.stdout.write(json.dumps({'protocol':'pynix-debug','version':1,'event':event})+'\\n')\n"
        "    sys.stdout.flush()\n"
        "send('ready')\n"
        "for line in sys.stdin:\n"
        "    packet=json.loads(line)\n"
        "    send('pong' if packet.get('command')=='ping' else 'exited')\n"
        "    if packet.get('command')=='shutdown': break\n",
        encoding="utf-8",
    )
    worker = _Worker(Path(sys.executable), tmp_path)
    try:
        worker.start()
        worker.send({"protocol": "pynix-debug", "version": 1, "command": "ping"})
        worker.send({"protocol": "pynix-debug", "version": 1, "command": "shutdown"})
        assert worker.receive(timeout=3)["event"] == "pong"
        assert worker.receive(timeout=3)["event"] == "exited"
    finally:
        worker.close()


def test_real_debug_worker_pipe_preserves_unicode_and_split_frames(tmp_path):
    """Real process sends fragmented UTF-8 JSON and preserves Unicode."""
    import sys
    from pynix_gui.ide_debug_process_client import _Worker

    package = tmp_path / "compiler"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    script = "\n".join([
        "import json, os, sys",
        "fd = sys.stdout.fileno()",
        "def send(obj):",
        "    data = json.dumps(obj, ensure_ascii=False).encode('utf-8') + bytes([10])",
        "    for i in range(0, len(data), 2): os.write(fd, data[i:i+2])",
        "send({'protocol':'pynix-debug','version':1,'event':'ready'})",
        "for line in sys.stdin.buffer:",
        "    send({'protocol':'pynix-debug','version':1,'event':'pong','output':'Привіт 🌍'})",
        "    break",
    ])
    (package / "debug_worker.py").write_text(script + "\n", encoding="utf-8")
    worker = _Worker(Path(sys.executable), tmp_path)
    try:
        worker.start()
        worker.send({"protocol": "pynix-debug", "version": 1, "command": "ping"})
        response = worker.receive(timeout=3)
        assert response["event"] == "pong"
        assert response["output"] == "Привіт 🌍"
    finally:
        worker.close()


def test_debugger_status_polling_uses_native_bridge_and_stops_when_inactive():
    root = Path(__file__).resolve().parents[1]
    view = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    assert "let debugStatusTimer=null;" in view
    assert "clearTimeout(debugStatusTimer);" in view
    assert "pollingBridge.postMessage({action:'status',source:current});" in view
    assert "if(debugBusy||!debugActive||" in view
    assert "'continue','status','stepInto'" in view
    assert '"status", "stop", "setBreakpoints"' in native


def test_native_client_can_query_debugger_status_without_stopping(tmp_path):
    class StatusWorker:
        def __init__(self):
            self.requests = []
        def send(self, packet):
            self.requests.append(packet)
        def receive(self):
            return {"protocol": "pynix-debug", "version": 1,
                    "command": "status", "state": "running"}
        def close(self):
            raise AssertionError("Polling running debugger must not stop its worker")

    worker = StatusWorker()
    client = DebugProcessClient(tmp_path, tmp_path / "python")
    client._worker = worker
    client._session = "s1"
    packet = client.command("status")
    assert packet["state"] == "running"
    assert worker.requests[0]["command"] == "status"
    assert worker.requests[0]["session"] == "s1"
    assert client._worker is worker


def test_debug_controls_are_kept_out_of_flat_top_toolbar():
    root = Path(__file__).resolve().parents[1]
    view = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "debugMenu.className='pynix-debug-menu';" in view
    assert "debugMenu.append(debugMenuLabel,debugToolbar);" in view
    assert "append(debugMenu,debugInfoButton);" in view
    assert ".workspace-mode .pynix-debug-toolbar{position:absolute" in html
    assert "grid-template-columns:repeat(3,minmax(78px,1fr))" in html


def test_debug_start_remains_primary_visible_action_and_reports_state():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    css = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "control.classList.add('pynix-debug-primary');" in js
    assert "document.querySelector('.workspace-toolbar')?.appendChild(control);" in js
    assert "debugToolbar.appendChild(control);" in js
    assert "debugMenuLabel.textContent='Steps ▾';" in js
    assert "debugInfoButton.textContent='● '" in js
    assert "debugInfoButton.title=packet?.message||'Debugger connection failed';" in js
    assert ".workspace-mode .workspace-toolbar .pynix-debug-primary" in css


def test_secondary_workspace_commands_use_overflow_not_flat_toolbar():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "toolsMenu.className='pynix-tools-menu';" in js
    assert "toolsMenuItems.className='pynix-tools-menu-items';" in js
    assert "newSourceButton,renameFileButton,deleteFileButton" in js
    assert "toolsMenuItems.appendChild(action);" in js
    assert ".workspace-mode .pynix-tools-menu-items{position:absolute" in html
    assert ".workspace-mode .workspace-toolbar>.run-control{display:none}" in html


def test_debug_worker_discovers_compiler_outside_user_project(tmp_path):
    """A venv-based compiler works even if the edited project is unrelated."""
    import os
    import sys
    from pynix_gui.ide_debug_process_client import _Worker

    compiler_root = tmp_path / "PYNIX"
    project = tmp_path / "user-project"
    project.mkdir()
    module = compiler_root / "compiler"
    module.mkdir(parents=True)
    (module / "__init__.py").write_text("", encoding="utf-8")
    (module / "debug_worker.py").write_text(
        "import sys, json\n"
        "print(json.dumps({'protocol':'pynix-debug','version':1,'event':'ready'}),flush=True)\n"
        "for line in sys.stdin:\n"
        " print(json.dumps({'protocol':'pynix-debug','version':1,'event':'pong'}),flush=True)\n",
        encoding="utf-8",
    )
    venv_bin = compiler_root / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    venv_bin.mkdir(parents=True)
    interpreter = venv_bin / ("python.exe" if os.name == "nt" else "python")
    try:
        interpreter.symlink_to(sys.executable)
    except (OSError, NotImplementedError):
        import shutil
        shutil.copy2(sys.executable, interpreter)
    worker = _Worker(interpreter, project)
    try:
        worker.start()
        worker.send({"protocol": "pynix-debug", "version": 1, "command": "ping"})
        assert worker.receive()["event"] == "pong"
    finally:
        worker.close()


def test_v5_docked_debugger_panel_keeps_controls_and_short_stack_paths():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "debugPanelBar.className='pynix-debug-panel-toolbar';" in js
    assert "terminal?.prepend(debugPanelBar);" in js
    assert "['continue','pause','stepInto','stepOver','stepOut','stop']" in js
    assert "el.textContent.trim()==='DEBUG CONSOLE'" in js
    assert ".split('/').pop()" in js
    assert ".workspace-mode .pynix-debug-panel-toolbar{display:flex" in html


def test_v5_debug_inspector_has_separate_stack_and_locals_sections():
    root = Path(__file__).resolve().parents[1]
    view = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "inspector.className='pynix-debug-inspector';" in view
    assert "section.className='pynix-debug-inspector-section';" in view
    assert "if(inspector.childElementCount)panel.appendChild(inspector);" in view
    assert ".workspace-mode .pynix-debug-inspector{display:grid;" in html


def test_v5_debug_dock_is_session_scoped_and_console_tab_is_selected():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    css = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "debugPanelBar.hidden=true;" in js
    assert "debugPanelBar.hidden=!debugActive;" in js
    assert "debugTab.classList.add('pynix-active-tab');" in js
    assert ".workspace-mode .pynix-debug-panel-toolbar[hidden]{display:none}" in css
    assert ".workspace-mode .editor-tabs button.active" in css


def test_reference_workspace_has_compact_jetbrains_geometry_and_dark_chrome():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    template = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "/* V5 JetBrains reference-layout pass." in template
    assert ".workspace-mode header{height:44px" in template
    assert ".workspace-mode .workspace-toolbar{height:45px" in template
    assert ".workspace-mode .tree{width:var(--explorer-width,238px)" in template
    assert ".workspace-mode .editor-tabs{height:38px" in template
    assert ".workspace-mode .terminal-console{color:#cbd2e1;background:#1e1f25}" in template


def test_reference_dark_theme_matches_editor_gutter_and_debug_layers():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    html = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "/* V5 reference shell: PyCharm New UI visual geometry" in html
    assert "--ide-base:#1e1f22" in html
    assert ".workspace-mode .rail{background:#2b2d30;width:42px" in html
    assert ".workspace-mode .pynix-edit-layer .pynix-edit-gutter{background:#1e1f22!important" in html
    assert ".workspace-mode .pynix-edit-layer .pynix-debug-execution-line{background:rgba(183,156,88,.18)" in html
    assert ".workspace-mode .pynix-edit-keyword{color:#c49ddd!important}" in html


def test_reference_toolbar_keeps_run_debug_visible_and_moves_secondary_actions():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "secondaryLabels=new Set(['Preview','Definition','References','Type','Restart'])" in js
    assert "toolsMenuItems.appendChild(button);" in js
    assert "window.addEventListener('load',()=>{" in js
    assert "control.classList.add('pynix-debug-primary');" in js


def test_reference_gutter_breakpoint_replaces_line_number():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    source = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "row.className=marked.has(i)?'pynix-gutter-breakpoint':'pynix-gutter-number';" in source
    assert "row.textContent=marked.has(i)?'●':String(i).padStart(3,' ');" in source
    assert ".pynix-edit-gutter{width:48px!important" in html
    assert "padding-left:60px!important" in html


def test_reference_breakpoint_is_red_and_number_rows_match_line_height():
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert ".pynix-edit-gutter>span{display:block;height:19px;line-height:19px" in html
    assert ".pynix-gutter-breakpoint{color:#e66b75!important" in html


def test_bottom_tool_window_can_collapse_and_restore_without_destroying_contents():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    js = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (root / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "function setToolWindowVisible(visible){" in js
    assert "terminal.classList.toggle('pynix-tool-window-collapsed',!visible);" in js
    assert "dockToggle.addEventListener('click',()=>setToolWindowVisible(false));" in js
    assert "dockRestore.addEventListener('click',()=>setToolWindowVisible(true));" in js
    assert "terminalResizer.hidden=!visible;" in js
    assert ".integrated-terminal.pynix-tool-window-collapsed{display:none!important}" in html

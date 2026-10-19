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
    assert 'TERMINAL_DOCK_JS.replace("__PYNIX_PACKAGES_DOCK__", PACKAGES_DOCK_JS)' in workspace
    assert 'SERVICES_DOCK_JS.replace("__PYNIX_SERVICES_JETBRAINS_ICONS__", services_jetbrains_icons_json())' in workspace
    assert "window.pynixServicesRunEvent?.(packet,lastRunRequest);" in workspace
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
    assert "servicesPane.classList.toggle('hide-tree',!svPreferences.showTree)" in ui
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


def test_services_header_is_inside_rounded_dock_with_13px_regular_text():
    root = Path(__file__).resolve().parents[1]
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    style = chrome.split("/* Services: split-tree tool window")[1].split("</style>")[0]

    assert ".workspace-mode .integrated-terminal .pynix-services-pane{" in style
    assert "width:100%!important;height:100%!important;min-width:0" in style
    assert "border-radius:9px!important;overflow:hidden!important" in style
    assert ".workspace-mode .integrated-terminal .pynix-services-header{" in style
    assert "height:41px!important;min-height:41px!important;flex:0 0 41px!important" in style
    assert "background:#1b1c1f!important;border-bottom:1px solid #36383e!important" in style
    assert "border-radius:9px 9px 0 0!important" in style
    assert ".workspace-mode .integrated-terminal .pynix-services-header strong{" in style
    assert "font:400 13px/18px" in style
    assert "font-size:15px" not in style
    assert "font-size:12px" not in style
    assert "font:600 12px" not in style
    assert "font-size:13px!important" in style


def test_services_uses_exact_bundled_jetbrains_svg_assets():
    import json
    from pynix_gui.ide_icon_parity import BUNDLED_ICONS
    from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog
    from pynix_gui.ide_services_dock import (
        SERVICES_JETBRAINS_ICON_NAMES, services_jetbrains_icons_json,
        SERVICES_DOCK_JS,
    )
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    expected = {
        "add": "general/add",
        "group": "general/show",
        "newMcp": "general/openNewTab",
        "expand": "general/expandAll",
        "collapse": "general/collapseAll",
        "dropdown": "general/dropdown",
        "refresh": "general/locate",
        "settings": "general/settings",
        "checked": "actions/checked",
        "chevronRight": "general/chevronRight",
        "help": "general/help",
        "options": "general/moreVertical",
        "hide": "general/hide",
        "run": "toolwindows/run",
        "mcp": "nodes/services",
    }
    assert SERVICES_JETBRAINS_ICON_NAMES == expected
    icons = json.loads(services_jetbrains_icons_json())
    assert set(icons) == set(expected)
    for slot, name in expected.items():
        source = catalog.svg(name, dark=True, compact=True)
        assert source is not None, name
        assert icons[slot] == source  # Unchanged, checksum-verified JetBrains artwork.
        assert "Copyright" in source and "Apache 2.0" in source
    assert "const svIcons=__PYNIX_SERVICES_JETBRAINS_ICONS__;" in SERVICES_DOCK_JS
    assert "new DOMParser().parseFromString(source,'image/svg+xml')" in SERVICES_DOCK_JS
    assert "svg.classList.add('pynix-services-jb-icon');" in SERVICES_DOCK_JS
    assert "sv(key).replaceChildren(vector);" in SERVICES_DOCK_JS
    assert "const dropdown=svIcon('dropdown');" in SERVICES_DOCK_JS
    assert "icon.appendChild(typeIcon);" in SERVICES_DOCK_JS
    assert 'class="pynix-services-toolbar-separator"' in SERVICES_DOCK_JS
    assert 'data-sv="newMcp"' in SERVICES_DOCK_JS
    assert "sv('newMcp').addEventListener('click',svAddMcp);" in SERVICES_DOCK_JS
    assert "menuAction('MCP SSE Connection…',svAddMcp);" in SERVICES_DOCK_JS
    assert "const svIcon=paths=>'<svg" not in SERVICES_DOCK_JS


def test_services_jetbrains_icons_keep_native_16px_size_in_mac_theme():
    root = Path(__file__).resolve().parents[1]
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    iconless = (root / "pynix_gui/ide_iconless_mode.py").read_text(encoding="utf-8")
    assert ".workspace-mode .pynix-services-header button>svg," in chrome
    assert ".workspace-mode .pynix-services-toolbar>button>svg," in chrome
    assert "width:16px!important;height:16px!important" in chrome
    assert ".pynix-services-toolbar .pynix-services-dropdown{" in chrome
    assert ".pynix-services-toolbar-separator{" in chrome
    for selector in (
        ".pynix-services-header button>svg",
        ".pynix-services-toolbar>button>svg",
        ".pynix-services-item-icon>svg",
    ):
        assert ".workspace-mode.pynix-iconless .pynix-services-pane " + selector in iconless
    assert "display:block!important" in iconless
    assert "width:16px!important;height:16px!important" in iconless


def test_services_right_actions_match_pycharm_and_only_appear_on_hover():
    from pynix_gui.ide_services_dock import SERVICES_JETBRAINS_ICON_NAMES, SERVICES_DOCK_JS
    from pynix_gui.ide_icon_parity import BUNDLED_ICONS
    from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog

    assert SERVICES_JETBRAINS_ICON_NAMES["refresh"] == "general/locate"
    assert "general/refresh" not in SERVICES_JETBRAINS_ICON_NAMES.values()
    assert JetBrainsIconCatalog(BUNDLED_ICONS).svg("general/locate", dark=True)
    assert 'data-sv="refresh" title="Select Active Service"' in SERVICES_DOCK_JS
    assert "sv('refresh').addEventListener('click',()=>{" in SERVICES_DOCK_JS
    assert "svRefresh();" in SERVICES_DOCK_JS

    root = Path(__file__).resolve().parents[1]
    css = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    for action in ('refresh', 'options', 'hide'):
        assert 'button[data-sv="' + action + '"]' in css
    assert "opacity:0!important;visibility:hidden!important" in css
    assert "pointer-events:none!important" in css
    assert ".pynix-services-pane:hover .pynix-services-header>button" in css
    assert 'button:focus-visible' in css


def test_services_options_menu_matches_jetbrains_with_real_actions():
    ui = (Path(__file__).resolve().parents[1] /
          "pynix_gui/ide_services_dock.py").read_text(encoding="utf-8")
    for item in (
        "Navigate with Single Click", "Always Select Opened Element",
        "Always Select Active Service", "Show Services Tree",
        "Configure Services Tool Window", "Double Click to Run Configuration",
        "Show Toolbar", "View Mode", "Move to", "Resize",
        "Remove from Sidebar", "Restore to Sidebar", "Help",
    ):
        assert item in ui
    assert "document.body.appendChild(optionsMenu);" in ui
    assert "optionsMenu.setAttribute('aria-label','Services Options');" in ui
    assert "new CustomEvent('pynix:services-pin'" in ui
    assert "localStorage.setItem('pynix.services.options'" in ui
    assert "servicesPane.classList.toggle('hide-toolbar'" in ui
    assert "servicesPane.classList.toggle('hide-tree'" in ui
    assert "terminal.style.setProperty('flex-basis'" in ui
    assert "window.open('https://www.jetbrains.com/help/pycharm/services-tool-window.html'" in ui
    assert "svOption('Floating',null,{parent:host,disabled:true});" in ui
    assert "svOption('Windowed',null,{parent:host,disabled:true});" in ui
    assert "svOption('Left',null,{parent:host,disabled:true});" in ui
    assert "svOption('Right',null,{parent:host,disabled:true});" in ui
    assert "sv('options').setAttribute('aria-expanded'" in ui
    assert "const svShowOptions=()=>{" in ui


def test_services_sidebar_can_be_restored_through_more_tool_windows():
    root = Path(__file__).resolve().parents[1]
    edge = (root / "pynix_gui/ide_edge_profile.py").read_text(encoding="utf-8")
    assert '("Services", "toolwindows/services", "", "services-window")' in edge
    assert "window.addEventListener('pynix:services-pin',syncPin);" in edge
    assert "button.classList.toggle('pynix-services-unpinned',!pinned)" in edge
    assert ".pynix-extra-tool.pynix-services-unpinned{display:none!important}" in edge


def test_services_option_submenus_can_float_outside_dock():
    root = Path(__file__).resolve().parents[1]
    css = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    iconless = (root / "pynix_gui/ide_iconless_mode.py").read_text(encoding="utf-8")
    assert "position:fixed!important;top:0;left:0;" in css
    assert "overflow:visible!important" in css
    assert ".pynix-services-option-wrap.has-submenu:hover>.pynix-services-submenu" in css
    assert ".pynix-services-options-menu .pynix-services-option-mark>svg" in iconless


def test_services_options_use_original_consistent_16px_jetbrains_icons():
    root = Path(__file__).resolve().parents[1]
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    iconless = (root / "pynix_gui/ide_iconless_mode.py").read_text(encoding="utf-8")
    menu = chrome.split("/* JetBrains Services Options is portaled")[1].split(
        "/* Header actions are contextual")[0]

    # Keep the compact 13px Options typography consistent with Services.
    assert "height:27px!important" in menu
    assert "min-height:27px!important" in menu
    assert "height:36px!important" not in menu
    assert "font:400 13px/18px" in menu
    assert "width:322px!important" in menu
    assert "margin-left:auto;color:#888c96;font-size:13px" in menu
    assert "padding:4px!important;display:flex!important" in menu
    assert "background:#45474e!important;margin:3px 5px!important" in menu

    # The 20px mark slot preserves PyCharm alignment but its contents
    # (checkbox, gear, Help, submenu chevron) must all be native 16px SVGs.
    mark = menu.split(".workspace-mode .pynix-services-option-mark{")[1].split("}")[0]
    assert "width:20px!important;height:20px!important" in mark
    assert "font-size:13px!important" in mark
    icons = menu.split(".workspace-mode .pynix-services-option-mark>svg,")[1].split("}")[0]
    assert ".workspace-mode .pynix-services-option-arrow{" in icons
    assert "width:16px!important;height:16px!important" in icons
    assert "max-width:16px!important;max-height:16px!important" in icons
    assert "width:20px!important;height:20px!important" not in icons
    assert "width:18px!important;height:18px!important" not in icons

    # Normal macOS iconless theme must not blow up individual icons.
    theme = iconless.split(
        "/* Options is portaled to body; restore original JetBrains 16x16 SVG sizes"
    )[1].split("/* Only the perimeter")[0]
    assert ".pynix-services-option-mark>svg," in theme
    assert ".pynix-services-option-arrow{" in theme
    assert "width:16px!important;height:16px!important" in theme
    assert "width:20px!important;height:20px!important" not in theme
    assert "width:18px!important;height:18px!important" not in theme


def test_services_options_checkmarks_use_original_jetbrains_asset():
    from pynix_gui.ide_services_dock import (
        SERVICES_JETBRAINS_ICON_NAMES, SERVICES_DOCK_JS, services_jetbrains_icons_json,
    )
    from pynix_gui.ide_icon_parity import BUNDLED_ICONS
    from pynix_gui.ide_jetbrains_icons import JetBrainsIconCatalog
    import json

    assert SERVICES_JETBRAINS_ICON_NAMES["checked"] == "actions/checked"
    catalog = JetBrainsIconCatalog(BUNDLED_ICONS)
    exact_svg = catalog.svg("actions/checked", dark=True, compact=True)
    assert exact_svg
    assert json.loads(services_jetbrains_icons_json())["checked"] == exact_svg
    assert "const check=svIcon('checked');" in SERVICES_DOCK_JS
    assert "if(check)mark.appendChild(check);" in SERVICES_DOCK_JS
    assert "mark.textContent='✓';" not in SERVICES_DOCK_JS
    assert "const svg=svIcon(config.icon);" in SERVICES_DOCK_JS
    assert "const arrow=svIcon('chevronRight');" in SERVICES_DOCK_JS

def test_services_options_labels_are_13px_without_changing_jetbrains_svg_size():
    root = Path(__file__).resolve().parents[1]
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    full = chrome.split("/* Services: split-tree tool window")[1].split("</style>")[0]
    menu = full.split("/* JetBrains Services Options is portaled")[1].split(
        "/* Header actions are contextual")[0]
    header = full.split(".workspace-mode .integrated-terminal .pynix-services-header strong{")[1].split("}")[0]

    assert "font:400 13px/18px" in menu
    assert "font:400 18px/24px" not in menu
    assert "height:27px!important" in menu
    assert "width:322px!important" in menu
    assert "width:190px!important" in menu
    assert "font:400 13px/18px" in header
    assert "width:16px!important;height:16px!important" in menu


def test_services_tree_shortcut_uses_mac_key_glyphs_not_one_font_fallback_run():
    root = Path(__file__).resolve().parents[1]
    ui = (root / "pynix_gui/ide_services_dock.py").read_text(encoding="utf-8")
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    menu = chrome.split("/* JetBrains Services Options is portaled")[1].split(
        "/* Header actions are contextual")[0]

    # It is a native Mac keyboard shortcut, not a JetBrains SVG toolbar icon.
    assert "if(config.shortcut==='⇧⌘T'){" in ui
    assert "hint.classList.add('pynix-services-shortcut-keys');" in ui
    assert "hint.setAttribute('aria-label','Shift Command T');" in ui
    assert "[['shift','⇧'],['command','⌘'],['letter','T']]" in ui
    assert "part.textContent=glyph;" in ui
    assert "part.setAttribute('aria-hidden','true');" in ui
    assert "}else hint.textContent=config.shortcut;" in ui
    assert "toggle('Show Services Tree','showTree',null,'⇧⌘T');" in ui

    # JetBrains-like fixed macOS metrics, with a shared baseline and tighter gap.
    assert "font:400 13px/16px -apple-system" in menu
    assert ".pynix-services-option-shortcut.pynix-services-shortcut-keys{" in menu
    assert "width:34px!important;height:16px!important" in menu
    assert "align-items:center!important" in menu
    for selector, width, size in (
        ("shift", 12, 14),
        ("command", 13, 14),
        ("letter", 9, 13),
    ):
        block = menu.split(
            ".workspace-mode .pynix-services-shortcut-" + selector + "{"
        )[1].split("}")[0]
        assert f"width:{width}px!important" in block
        assert f"font-size:{size}px!important" in block
    assert "font:400 13px/18px" in menu  # Main menu typography is unchanged.

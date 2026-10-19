"""Package manager and PyCharm-like Packages panel regression tests."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pynix_gui.ide_project_packages import PackageError, ProjectPackages


@pytest.fixture
def env(tmp_path):
    executable = tmp_path / ".venv" / "bin" / "python"
    executable.parent.mkdir(parents=True)
    executable.write_text("# test interpreter\n")
    return ProjectPackages(tmp_path)


def test_missing_environment_never_falls_back_to_system_python(tmp_path):
    manager = ProjectPackages(tmp_path)
    with pytest.raises(PackageError, match="No project .venv"):
        manager.list_installed()


def test_list_installed_uses_only_project_venv(monkeypatch, env):
    captured = []
    def fake_run(command, **kwargs):
        captured.append((command, kwargs))
        return subprocess.CompletedProcess(
            command, 0,
            '[{"name":"pynix-gui","version":"0.1.6.dev0"},'
            '{"name":"requests","version":"2.32.0"}]',
            "WARNING: pip version check disabled",
        )
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = env.list_installed()
    assert result["interpreter"] == str(env.python)
    assert [item["name"] for item in result["packages"]] == [
        "pynix-gui", "requests"
    ]
    assert captured[0][0] == [
        str(env.python), "-m", "pip", "list", "--format=json"
    ]
    assert captured[0][1]["cwd"] == env.root
    assert captured[0][1]["timeout"] == 30


@pytest.mark.parametrize("name", ["-r", "../file", "bad package", "x;ls", "", "a/b"])
def test_rejects_unsafe_package_names(name):
    with pytest.raises(PackageError):
        ProjectPackages.name(name)


@pytest.mark.parametrize("version", ["", "--extra-index-url", "1;rm", "../x"])
def test_rejects_invalid_package_versions(version):
    with pytest.raises(PackageError):
        ProjectPackages.version(version)


def test_mutations_use_argument_arrays_never_shell(monkeypatch, env):
    calls = []
    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "done", "")
    monkeypatch.setattr(subprocess, "run", fake_run)
    env.change("install", "requests", "2.32.3")
    env.change("upgrade", "requests")
    env.change("uninstall", "requests")
    assert calls[0][0][-3:] == [
        "install", "--disable-pip-version-check", "requests==2.32.3"
    ]
    assert calls[1][0][-4:] == [
        "install", "--disable-pip-version-check", "--upgrade", "requests"
    ]
    assert calls[2][0][-3:] == ["uninstall", "-y", "requests"]
    assert all("shell" not in kwargs for _, kwargs in calls)
    with pytest.raises(PackageError, match="Unsupported"):
        env.change("delete-all", "requests")


def test_metadata_lookup_uses_pypi_https_and_bounds_text(monkeypatch, env):
    from pynix_gui import ide_project_packages
    seen = []
    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, limit):
            assert limit == 512_001
            return json.dumps({
                "info": {
                    "name": "requests", "version": "2.32.3",
                    "summary": "HTTP Client", "description": "Package docs",
                    "project_urls": {"Homepage": "https://requests.readthedocs.io"},
                },
                "releases": {"2.32.3": [{"filename": "x.whl"}]}
            }).encode("utf-8")
    def fake_open(request, timeout):
        seen.append((request.full_url, timeout))
        return FakeResponse()
    monkeypatch.setattr(ide_project_packages.urllib.request, "urlopen", fake_open)
    result = env.details("requests")
    assert seen == [("https://pypi.org/pypi/requests/json", 7)]
    assert result["version"] == "2.32.3"
    assert result["versions"] == ["2.32.3"]
    assert result["homepage"].startswith("https://")


def test_packages_ui_is_isolated_from_project_tree_and_run():
    root = Path(__file__).resolve().parents[1]
    edge = (root / "pynix_gui/ide_edge_profile.py").read_text(encoding="utf-8")
    dock = (root / "pynix_gui/ide_terminal_dock.py").read_text(encoding="utf-8")
    chrome = (root / "pynix_gui/ide_pycharm_chrome.py").read_text(encoding="utf-8")
    ui = (root / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    package_ui = (root / "pynix_gui/ide_packages_dock.py").read_text(encoding="utf-8")
    native = (root / "examples/ide_native_v4.py").read_text(encoding="utf-8")

    assert '"PYNIX Packages": "packages-window"' in edge
    assert '("PYNIX Packages", "pynix/pynix-packages", "left-bottom", "existing")' in edge
    assert "window.pynixTerminalDock?.togglePackages?.()" in edge
    assert "const togglePackages=()=>select('packages');" in dock
    assert "packagesPane.hidden=!(visible&&scope==='packages');" in dock
    assert "header.hidden=visible&&scope==='packages';" in dock
    assert "toolConsole.hidden=scope!=='other';" in dock
    assert "window.pynixPackagesResult=result=>" in package_ui
    assert "pynixPackages" in package_ui
    assert "PACKAGES_DOCK_JS.replace" not in ui
    assert 'TERMINAL_DOCK_JS.replace("__PYNIX_PACKAGES_DOCK__", PACKAGES_DOCK_JS)' in ui
    assert "packagePane" not in dock or "__PYNIX_PACKAGES_DOCK__" in dock
    assert "controller.addScriptMessageHandler_name_(packages_handler, \"pynixPackages\")" in native
    assert "run_threading.Thread(target=perform, daemon=True).start()" in native
    assert "packages_lock.acquire(blocking=False)" in native
    assert ".pynix-packages-pane[hidden]" in chrome
    assert "setExplorerVisible(" not in package_ui
    assert "document.querySelectorAll('.rail-item')" not in package_ui


def test_package_controls_require_confirmation_and_use_safe_dom():
    ui = (Path(__file__).resolve().parents[1] / "pynix_gui" /
          "ide_packages_dock.py").read_text(encoding="utf-8")
    assert "window.confirm(message)" in ui
    assert "packagePart('description').textContent" in ui
    assert "packageList.replaceChildren()" in ui
    assert "packagePart('version').value" in ui
    assert "noopener noreferrer" in ui

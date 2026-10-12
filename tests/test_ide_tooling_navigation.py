import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from pynix_gui.ide_tooling_navigation import query_navigation
from pynix_gui.ide_workspace_preview import attach_navigation


def test_definition_query_uses_public_compiler_cli(monkeypatch, tmp_path):
    (tmp_path / "main.pnx").write_text("function main()", encoding="utf-8")
    exe = tmp_path / "python"
    exe.write_text("")
    observed = []
    def run(cmd, **kwargs):
        observed.append(cmd)
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            "protocol":"pynix-tooling","version":1,"kind":"definition",
            "definition":{"name":"main","source":"main.pnx","start":{"line":1,"column":1}}}))
    monkeypatch.setattr("pynix_gui.ide_tooling_navigation.subprocess.run",run)
    result=query_navigation(tmp_path, exe, "definition", "main.pnx", 1, 10)
    assert result["definition"]["name"]=="main"
    assert observed[0][2:5] == ["compiler","tooling","definition"]
    assert observed[0][-2:] == ["1","10"]


def test_reject_bad_navigation_query(tmp_path):
    exe=tmp_path/"python"
    exe.write_text("")
    (tmp_path/"valid.pnx").write_text("x")
    with pytest.raises(ValueError):
        query_navigation(tmp_path,exe,"execute","valid.pnx",1,1)
    with pytest.raises(ValueError):
        query_navigation(tmp_path,exe,"definition","../escape.pnx",1,1)
    with pytest.raises(ValueError):
        query_navigation(tmp_path,exe,"definition","valid.pnx",0,1)


def test_navigation_result_has_safe_script_encoding():
    result={"protocol":"pynix-tooling","version":1,"kind":"definition",
            "definition":{"name":"</script><script>bad()</script>","source":"main.pnx"}}
    html=attach_navigation("<body></body>",result,"definition")
    assert "</script><script>bad()" not in html
    assert "\\u003c/script" in html
    assert "row.textContent=value" in html


def test_native_navigation_arguments_present():
    source=(Path(__file__).resolve().parents[1]/"examples"/"ide_native_v4.py").read_text()
    for flag in ("--nav-command","--nav-source","--nav-line","--nav-column"):
        assert flag in source

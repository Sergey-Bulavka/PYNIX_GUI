from pynix_gui.ide_file_icons import file_icon_type, ICON_TINT
from pynix_gui.ide_workspace_preview import workspace_bootstrap
from pynix_gui.ide_workspace_session import WorkspaceSession

def test_file_type_recognition():
    expected = {"main.pnx":"pynix","compiler.py":"python","README.md":"markdown",
                "pyproject.toml":"settings","data.json":"json","image.png":"image",
                "script.sh":"terminal","unknown.bin":"file",".gitignore":"git"}
    assert {name:file_icon_type(name) for name in expected} == expected
    assert set(expected.values()) <= set(ICON_TINT)

def test_case_insensitive_and_nested_paths():
    assert file_icon_type("src/TEST.PY") == "python"
    assert file_icon_type("docs/NOTES.MD") == "markdown"

def test_project_preview_has_icon_metadata(tmp_path):
    (tmp_path/"example.pnx").write_text("function main()")
    (tmp_path/"README.md").write_text("# title")
    source=workspace_bootstrap(WorkspaceSession(tmp_path))
    assert '"icon": "pynix"' in source
    assert '"icon": "markdown"' in source
    assert "fileIconMarkup(fileType)" in source

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


def test_python_icon_uses_upstream_original_vector_not_hand_drawn_path():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "python-original-a" in source
    assert "linearGradient" in source
    assert 'viewBox=\'0 0 128 128\'' in source
    assert "M12 2C6 2" not in source


def test_python_svg_is_valid_javascript_template_literal():
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    start = src.index("if(type==='python') return ")
    end = src.index("if(type==='markdown')", start)
    statement = src[start:end]
    assert "return `<svg " in statement
    assert "</svg>`;" in statement
    assert statement.count("`") == 2
    assert "xmlns='http://www.w3.org/2000/svg'" in statement



def test_additional_source_resource_types_use_stable_file_extensions():
    from pynix_gui.ide_file_icons import ICON_BY_EXTENSION, SPECIAL_NAMES
    expected={
        "styles/main.css":"code", "src/main.js":"code", "src/App.tsx":"code",
        "db/schema.sql":"code", "config/dev.yaml":"settings",
        "assets/logo.svg":"image", "assets/photo.webp":"image",
        "assets/snapshot.png":"image", "fonts/app.woff2":"font",
        "artifacts/source.zip":"archive", "gradle/build.gradle":"settings",
        "docs/table.csv":"text",
    }
    assert {path:file_icon_type(path) for path in expected}==expected
    assert all(value in ICON_TINT for value in expected.values())
    assert SPECIAL_NAMES["dockerfile"]=="settings"
    assert ICON_BY_EXTENSION[".jsx"]=="code"


def test_binary_resource_files_are_listed_as_nontext_not_dispatched_to_editor(tmp_path):
    (tmp_path/"main.pnx").write_text("function main()",encoding="utf-8")
    (tmp_path/"assets").mkdir()
    (tmp_path/"assets"/"logo.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path/"assets"/"archive.zip").write_bytes(b"PK\x03\x04")
    (tmp_path/"assets"/"page.css").write_text("body {}")
    bootstrap=workspace_bootstrap(WorkspaceSession(tmp_path))
    assert '"name": "assets/logo.png"' in bootstrap
    assert '"name": "assets/archive.zip"' in bootstrap
    assert '"name": "assets/page.css"' in bootstrap
    assert bootstrap.count('"nonText": true') == 2
    assert '"icon": "image"' in bootstrap
    assert '"icon": "archive"' in bootstrap
    assert 'if(!file.nonText){' in bootstrap
    assert "if(bridge)bridge.postMessage({source:name});" in bootstrap
    assert "file.name.endsWith('.pnx')" in bootstrap

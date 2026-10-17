"""PyCharm-like colors: real V4 Python/PYNIX lexer, not a demo editor."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from pynix_gui.ide_editor_lexer import EDITOR_LEXER_JS
from pynix_gui.ide_editor_theme import EDITOR_THEME_STYLE, apply_editor_darcula


def test_editor_theme_is_a_noninvasive_final_css_layer():
    source='<html><body class="workspace-mode"><main>Editor</main></body></html>'
    result=apply_editor_darcula(source)
    assert "Editor</main>" in result
    assert result.count('id="pynix-v4-editor-darcula"')==1
    assert apply_editor_darcula(result)==result
    assert apply_editor_darcula("non html")=="non html"
    for style in (
        "#bcbec4", "#cf8e6d", "#6aab73", "#56a8f5",
        "#b3ae60", "#7a7e85",
        ".pynix-edit-python-keyword", ".pynix-edit-python-definition",
        ".pynix-edit-python-decorator", ".pynix-edit-python-comment",
        ".pynix-edit-keyword", ".pynix-edit-string",
        ".tree .project-entry .project-label",
        ".pynix-edit-layer .pynix-edit-highlight",
    ):
        assert style in EDITOR_THEME_STYLE, style
    for dangerous in (".pynix-source-input{", "padding-left:", "inset:",
                      "font-size:", ".pynix-custom-caret{", "pointer-events:"):
        assert dangerous not in EDITOR_THEME_STYLE


def test_native_v4_installs_editor_palette_after_existing_styles():
    src=(Path(__file__).resolve().parents[1] /
         "examples/ide_native_v4.py").read_text("utf-8")
    assert "document = apply_editor_darcula(document)" in src
    assert src.index("document = apply_editor_darcula(document)") > src.index(
        "document = apply_native_tooltips(document)"
    )
    assert src.index("document = apply_editor_darcula(document)") > src.index(
        "document = apply_iconless_mode(document)"
    )
    bootstrap=(Path(__file__).resolve().parents[1] /
               "pynix_gui/ide_workspace_preview.py").read_text("utf-8")
    assert "return EDITOR_LEXER_JS + \"\"\"<script>" in bootstrap
    assert "window.pynixHighlightTokens(value,current||'')" in bootstrap
    assert "const previewTokens=file.tokens?[]:window.pynixHighlightTokens(file.text,file.name);" in bootstrap
    assert "decorateSegment(value.slice(part.start,part.end),part.start)" in bootstrap


def _node_tokens(source, filename):
    if shutil.which("node") is None:
        pytest.skip("Node.js is required for the JavaScript lexer smoke test")
    js=EDITOR_LEXER_JS.split(">",1)[1].rsplit("</script>",1)[0]
    execution=(
        "global.window=global;\n"+js+
        "\nconst text="+json.dumps(source)+
        ";\nconst filename="+json.dumps(filename)+
        ";\nconsole.log(JSON.stringify(window.pynixHighlightTokens(text,filename)));\n"
    )
    result=subprocess.run(["node","-e",execution],text=True,
                          capture_output=True,timeout=20,check=True)
    return json.loads(result.stdout)


def test_python_darcula_lexer_recognizes_pytest_fixture_sample_losslessly():
    source=(
        "from pathlib import Path\n"
        "import pytest\n"
        "@pytest.fixture\n"
        "def pynix_project(tmp_path: Path):\n"
        "    for relative, source in files.items():\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "    return tmp_path\n"
    )
    results=_node_tokens(source,"tests/conftest.py")
    def match(text,kind):
        return any(source[t["start"]:t["end"]]==text and t["kind"]==kind
                   for t in results)
    for spelling in ("from","import","def","for","in","return"):
        assert match(spelling,"python-keyword"),spelling
    assert match("@pytest.fixture","python-decorator")
    assert match("pynix_project","python-definition")
    assert match("Path","python-plain")
    assert match("True","python-constant")
    assert match("mkdir","python-call")
    assert not any(t["kind"]=="python-comment" for t in results)


def test_strings_comments_and_triple_docstrings_do_not_leak_nested_tokens():
    source=(
        '"""Docstring with from import 42 and // safely""" \n'
        "x = f'# {42} True'  # real comment\n"
        "y = '''multiline\nreturn 123\nstill string'''\n"
        "result = 6 // 2\n"
    )
    tokens=_node_tokens(source,"src/demo.py")
    kinds=[(source[t["start"]:t["end"]],t["kind"]) for t in tokens]
    assert any(text.startswith('"""') and kind=="python-string" for text,kind in kinds)
    assert ("# real comment","python-comment") in kinds
    assert any(text.startswith("f'") and kind=="python-string" for text,kind in kinds)
    assert any(text.startswith("'''multiline") and "return 123" in text
               and kind=="python-string" for text,kind in kinds)
    assert ("6","python-number") in kinds
    assert ("2","python-number") in kinds
    assert not any("return"==text and kind=="python-keyword" for text,kind in kinds)


def test_pynix_lexer_is_language_specific_and_unknown_files_remain_plain():
    source='function main() {\n  print("from import") // comment\n  return true\n}'
    tokens=_node_tokens(source,"main.pnx")
    kinds=[(source[t["start"]:t["end"]],t["kind"]) for t in tokens]
    assert ("function","keyword") in kinds
    assert ("main","definition") in kinds
    assert ('"from import"',"string") in kinds
    assert ("// comment","comment") in kinds
    assert ("true","constant") in kinds
    assert _node_tokens(source,"file.md")==[]

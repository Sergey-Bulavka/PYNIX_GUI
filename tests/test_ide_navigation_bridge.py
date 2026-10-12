"""V4.8 navigation bridge contracts; executable without AppKit."""
import pytest
from pynix_gui.ide_navigation_bridge import (
    validate_request, result_script, attach_navigation_controls,
)


def test_valid_selection_for_tooling():
    sources = {"examples/hello.pnx", "compiler/tooling.py"}
    assert validate_request({"command": "definition", "source": "examples/hello.pnx",
                             "line": 1, "column": 9}, sources) == (
                             "definition", "examples/hello.pnx", 1, 9)


@pytest.mark.parametrize("message", [
    {}, {"command": "run", "source": "examples/hello.pnx", "line": 1, "column": 1},
    {"command": "definition", "source": "../private.pnx", "line": 1, "column": 1},
    {"command": "references", "source": "compiler/tooling.py", "line": 1, "column": 1},
    {"command": "definition", "source": "examples/hello.pnx", "line": True, "column": 1},
    {"command": "definition", "source": "examples/hello.pnx", "line": 0, "column": 1},
])
def test_invalid_navigation_never_reaches_tooling(message):
    with pytest.raises(ValueError):
        validate_request(message, {"examples/hello.pnx", "compiler/tooling.py"})


def test_result_serialization_is_script_safe():
    script = result_script({"error": "</script><script>alert('bad')</script>"}, "definition")
    assert "</script><script>" not in script
    assert "\\u003c/script" in script


def test_controls_use_single_click_and_source_selection():
    document = attach_navigation_controls("<body></body>")
    assert "window.pynixActiveSource" in document
    assert "handler.postMessage({command,source,line,column})" in document
    assert "code.addEventListener('click'" in document
    assert "pynix:navigate" in document
    assert "window.pynixNavigationResult" in document


def test_native_host_installs_real_webkit_handler():
    from pathlib import Path
    code = (Path(__file__).resolve().parents[1] / "examples" /
            "ide_native_v4.py").read_text()
    assert "class NavigationHandler(NSObject)" in code
    assert 'addScriptMessageHandler_name_(navigation_handler, "pynixNavigation")' in code
    assert "validate_request(" in code
    assert "query_navigation(" in code


def test_navigation_waits_for_lazy_file_to_be_ready():
    from pynix_gui.ide_navigation_bridge import navigation_controls
    javascript = navigation_controls()
    assert "pynix:file-ready" in javascript
    assert "if(!ready)" in javascript
    assert "Wait for the source file to finish loading" in javascript


def test_pyobjc_file_request_is_normalized():
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "examples" / "ide_native_v4.py").read_text()
    assert "request = dict(request)" in src
    assert "source = request.get(\"source\")" in src

"""Debugger availability is reported truthfully until a runtime API exists."""
from pynix_gui.ide_debug_capabilities import current_debug_capabilities


def test_debug_capabilities_do_not_claim_unimplemented_runtime_stepping():
    info = current_debug_capabilities()
    assert info["protocol"] == "pynix-debug-capabilities"
    assert info["version"] == 1
    assert info["supported"] is False
    for feature in ("breakpoints", "pause", "step_into", "step_over",
                    "step_out", "stack_frames", "variables"):
        assert info[feature] is False
    assert "pause/step" in info["reason"]


def test_debug_ui_does_not_claim_interactive_support():
    from pathlib import Path
    preview = (Path(__file__).resolve().parents[1] /
               "pynix_gui" / "ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "Debug (experimental" in preview
    assert "Interactive stepping and source mapping have not passed release acceptance." in preview

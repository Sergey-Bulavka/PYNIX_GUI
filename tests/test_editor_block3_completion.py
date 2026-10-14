"""Block 3 local completion integration checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completion_is_explicit_and_edits_through_editor_history():
    source = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "function completionPrefix()" in source
    assert "function offerCompletion()" in source
    assert "function applyCompletion(index)" in source
    assert "completionKeywords=['function','import','module'" in source
    assert "event.code==='Space'" in source
    assert "event.key==='ArrowDown'||event.key==='ArrowUp'" in source
    assert "replaceSelection(word,range.start,range.end)" in source
    assert "editorInput.value.slice(range.start,range.end)!==range.prefix" in source


def test_completion_ui_has_explicit_hidden_state_and_accessibility():
    source = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    html = (ROOT / "examples/icon_direction_preview.html").read_text(encoding="utf-8")
    assert "completionBox.hidden=true" in source
    assert "completionBox.setAttribute('role','listbox')" in source
    assert "item.setAttribute('role','option')" in source
    assert ".pynix-completion-popup[hidden]{display:none!important}" in html
    assert "completionBox.appendChild(item)" in source



def test_local_rename_requires_confirmation_and_preserves_undo():
    source = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "function selectedIdentifier()" in source
    assert "function renameLocalIdentifier()" in source
    assert "Rename occurrences in CURRENT file (textual, not semantic)" in source
    assert "window.confirm('Replace '+matches.length+' code identifiers named" in source
    assert ".filter(match=>match[0]===old)" in source
    assert "pushUndo(byName.get(current));" in source
    assert "editorInput.dispatchEvent(new Event('input',{bubbles:true}))" in source


def test_on_demand_compiler_problems_are_navigable():
    source = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    native = (ROOT / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    assert "window.pynixLiveDiagnosticsResult=payload=>" in source
    assert 'bridge.postMessage({});' in source
    assert "new CustomEvent('pynix:navigate'" in source
    assert 'controller.addScriptMessageHandler_name_(diagnostics_handler, "pynixDiagnostics")' in native
    assert "read_diagnostics(session.root, compiler_python)" in native


def test_compiler_navigation_uses_live_editor_and_rejects_stale_buffer():
    bridge = (ROOT / "pynix_gui/ide_navigation_bridge.py").read_text(encoding="utf-8")
    source = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "editor.value.slice(0,editor.selectionStart)" in bridge
    assert "window.pynixHasUnsavedSource?.(source)" in bridge
    assert "Save changes before querying compiler navigation" in bridge
    assert "window.pynixHasUnsavedSource=source=>" in source



def test_project_symbol_completion_uses_public_compiler_protocol():
    source = (ROOT / "pynix_gui/ide_tooling_symbols.py").read_text(encoding="utf-8")
    native = (ROOT / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    preview = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert '"tooling", "symbols", str(root)' in source
    assert 'payload.get("protocol") != "pynix-tooling"' in source
    assert "payload.get(\"version\") != 1" in source
    assert 'controller.addScriptMessageHandler_name_(symbols_handler, "pynixProjectSymbols")' in native
    assert "window.pynixProjectSymbolsResult=packet=>" in preview
    assert "compilerSymbols,...identifiers" in preview
    assert "completionButton.textContent='Complete'" in preview



def test_semantic_rename_requires_core_preflight_and_preserves_disk():
    source = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    native = (ROOT / "examples/ide_native_v4.py").read_text(encoding="utf-8")
    refactor = (ROOT / "pynix_gui/ide_semantic_rename.py").read_text(encoding="utf-8")
    assert "window.pynixSemanticRenamePlan=packet=>" in source
    assert "semanticRenameButton.textContent='Rename Symbol'" in source
    assert "file.text!==item.before||file.savedText!==item.before" in source
    assert "const revision=Math.max(coreRevisions.get(item.source)||0" in source
    assert 'controller.addScriptMessageHandler_name_(semantic_rename_handler, "pynixSemanticRename")' in native
    assert 'state["dirty"] or state["content"] != entry["before"]' in native
    assert "entry[\"coreRevision\"] = state[\"revision\"]" in native
    assert 'def plan_semantic_rename(' in refactor
    assert 'return {"symbol": old_name' in refactor


def test_block3_test_runner_isolated_and_has_cross_file_rename(tmp_path):
    import subprocess
    runner = ROOT / "scripts" / "test_editor_block3.sh"
    source = runner.read_text(encoding="utf-8")
    assert "mktemp -d" in source
    assert 'cat > "$PROJECT/src/util.pnx"' in source
    assert "press F2" in source
    assert 'bash scripts/run_ide_workspace.sh "$PROJECT"' in source
    assert "rm -rf" not in source
    result = subprocess.run(["bash", "-n", str(runner)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_compiler_results_select_output_before_rendering():
    bridge = (ROOT / "pynix_gui/ide_navigation_bridge.py").read_text(encoding="utf-8")
    block = bridge.split("window.pynixNavigationResult=packet=>", 1)[1]
    assert block.index("outputTab?.click();") < block.index("output.replaceChildren();")
    assert "normalizeSource(ref.source)" in block
    assert "normalizeSource(d.source)" in block


def test_cross_file_semantic_rename_accepts_unloaded_indexed_sources():
    preview = (ROOT / "pynix_gui/ide_workspace_preview.py").read_text(encoding="utf-8")
    assert "window.pynixIndexedSources=files.map(file=>file.name)" in preview
    rename = preview.split("window.pynixSemanticRenamePlan=packet=>", 1)[1].split(
        "semanticRenameButton.addEventListener", 1)[0]
    assert "if(file.unloaded){" in rename
    assert "file.text=item.before;file.savedText=item.before;file.unloaded=false;" in rename
    assert "!file.unloaded&&(file.text!==item.before||file.savedText!==item.before)" in rename

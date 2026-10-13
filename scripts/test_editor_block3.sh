#!/usr/bin/env bash
# Isolated acceptance for PYNIX IDE Block 3 language services.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$(mktemp -d "${TMPDIR:-/tmp}/pynix-editor-block3.XXXXXX")"
mkdir -p "$PROJECT/src"
cat > "$PROJECT/pynix.toml" <<'TOML'
[project]
name = "editor-block3-acceptance"
source = "src"
entry = "main.pnx"
TOML
cat > "$PROJECT/src/main.pnx" <<'PNX'
function helper()
    return 7

function main()
    let result = helper()
    print(result)
PNX
cat > "$PROJECT/src/notes.pnx" <<'PNX'
function secondary()
    return 1
PNX
echo "BLOCK 3 ISOLATED PROJECT: $PROJECT"
echo "1. Open src/main.pnx and type 'fun'; click Complete or press Ctrl+Space."
echo "2. Verify keyword/function suggestions and accept one using Tab or Enter; Undo."
echo "3. Save the file, select helper() call. Try Definition, References and Type."
echo "4. Rename Local (F2) is textual current-file-only; try it and undo."
echo "5. Click Problems with valid saved code; check compiler reports zero issues."
echo "6. Introduce a syntax error, Save, click Problems, and inspect the error."
echo "7. Restore the code, Save, click Problems; error should disappear."
echo "8. Make unsaved edits and invoke Definition; stale query must be rejected."
echo "All edits stay within the temporary project."
cd "$ROOT"
bash scripts/run_ide_workspace.sh "$PROJECT" \
  --compiler-python /Users/morphey/PycharmProjects/PYNIX/.venv/bin/python \
  --ide-core /Users/morphey/PycharmProjects/PYNIX_IDE

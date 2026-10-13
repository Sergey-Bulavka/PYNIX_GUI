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
import util

function main()
    let result = util.helper()
    print(result)
PNX
cat > "$PROJECT/src/util.pnx" <<'PNX'
public function helper()
    return 7

function check()
    return helper()
PNX
echo "BLOCK 3 ISOLATED PROJECT: $PROJECT"
echo "1. Open src/main.pnx and type 'fun'; click Complete or press Ctrl+Space."
echo "2. Verify keyword/function suggestions and accept one using Tab or Enter; Undo."
echo "3. Save main.pnx, select util.helper() call. Try Definition, References and Type."
echo "4. Place caret on helper in util.helper(), press F2, rename to renamedHelper."\necho "   Confirm; inspect main.pnx and util.pnx tabs. Both must be unsaved until Cmd+S."\necho "   Save both, confirm names in both sources. Shift+F2 tests conservative Rename Local."
echo "5. Click Problems with valid saved code; check compiler reports zero issues."
echo "6. Introduce a syntax error, Save, click Problems, and inspect the error."
echo "7. Restore the code, Save, click Problems; error should disappear."
echo "8. Make unsaved edits and invoke Definition; stale query must be rejected."
echo "All edits stay within the temporary project."
cd "$ROOT"
bash scripts/run_ide_workspace.sh "$PROJECT" \
  --compiler-python /Users/morphey/PycharmProjects/PYNIX/.venv/bin/python \
  --ide-core /Users/morphey/PycharmProjects/PYNIX_IDE

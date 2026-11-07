#!/usr/bin/env bash
# Isolated acceptance for Zunyite IDE Block 3 language services.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$(mktemp -d "${TMPDIR:-/tmp}/zunyite-editor-block3.XXXXXX")"
mkdir -p "$PROJECT/src"
cat > "$PROJECT/zunyite.toml" <<'TOML'
[project]
name = "editor-block3-acceptance"
source = "src"
entry = "main.uny"
TOML
cat > "$PROJECT/src/main.uny" <<'UNY'
import util

function main()
    let result = util.helper()
    print(result)
UNY
cat > "$PROJECT/src/util.uny" <<'UNY'
public function helper()
    return 7

function check()
    return helper()
UNY
echo "BLOCK 3 ISOLATED PROJECT: $PROJECT"
echo "1. Open src/main.uny and type 'fun'; click Complete or press Ctrl+Space."
echo "2. Verify keyword/function suggestions and accept one using Tab or Enter; Undo."
echo "3. Save main.uny, select util.helper() call. Try Definition, References and Type."
echo "4. Place caret on helper in util.helper(), press F2, rename to renamedHelper."
echo "   Confirm; inspect main.uny and util.uny tabs. Both must be unsaved until Cmd+S."
echo "   Save both, confirm names in both sources. Shift+F2 tests conservative Rename Local."
echo "5. Click Problems with valid saved code; check compiler reports zero issues."
echo "6. Introduce a syntax error, Save, click Problems, and inspect the error."
echo "7. Restore the code, Save, click Problems; error should disappear."
echo "8. Make unsaved edits and invoke Definition; stale query must be rejected."
echo "All edits stay within the temporary project."
COMPILER_PYTHON="${ZUNYITE_COMPILER_PYTHON:-$ROOT/../Zunyite/.venv/bin/python}"
IDE_CORE="${ZUNYITE_IDE_CORE:-$ROOT/../Zunyite_IDE}"
if [[ ! -x "$COMPILER_PYTHON" || ! -f "$IDE_CORE/src/workspace_read_host.uny" ]]; then
  echo "Zunyite compiler or IDE Core checkout is unavailable" >&2
  exit 2
fi
cd "$ROOT"
bash scripts/run_ide_workspace.sh "$PROJECT" \
  --compiler-python "$COMPILER_PYTHON" \
  --ide-core "$IDE_CORE"

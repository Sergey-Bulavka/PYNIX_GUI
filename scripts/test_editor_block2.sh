#!/usr/bin/env bash
# Isolated macOS acceptance runner for Zunyite IDE editor Block 2.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$(mktemp -d "${TMPDIR:-/tmp}/zunyite-editor-block2.XXXXXX")"
mkdir -p "$PROJECT/src"
cat > "$PROJECT/zunyite.toml" <<'TOML'
[project]
name = "editor-block2-acceptance"
source = "src"
entry = "main.uny"
TOML
cat > "$PROJECT/src/main.uny" <<'UNY'
function main()
    let total = 0
    if total == 0
        print("total")
        print("total")
    print("done")

function helper()
    print("helper")
UNY
cat > "$PROJECT/src/extra.uny" <<'UNY'
function extra()
    let count = 1
    print(count)
UNY
echo "EDITOR BLOCK 2 TEST PROJECT: $PROJECT"
echo "1. Verify line numbers and syntax colors; edit nested function and press Enter."
echo "2. Type ( [ { and quotes; use Cmd+Z/Cmd+Shift+Z."
echo "3. Select 'total', press Cmd+D twice and replace both occurrences."
echo "4. Try Cmd+Option+Down and Option+Click for extra carets, type text and Esc."
echo "5. Try Cmd+/, Cmd+Shift+D, Option+ArrowUp/ArrowDown."
echo "6. Use Find/Replace, Fold/Unfold and Preview gutter arrows."
echo "7. Switch between files, Save each via Cmd+S, reopen and check the text."
echo "All test files are isolated. No existing project files will be modified."
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

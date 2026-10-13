#!/usr/bin/env bash
# Isolated macOS acceptance runner for PYNIX IDE editor Block 2.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$(mktemp -d "${TMPDIR:-/tmp}/pynix-editor-block2.XXXXXX")"
mkdir -p "$PROJECT/src"
cat > "$PROJECT/pynix.toml" <<'TOML'
[project]
name = "editor-block2-acceptance"
source = "src"
entry = "main.pnx"
TOML
cat > "$PROJECT/src/main.pnx" <<'PNX'
function main()
    let total = 0
    if total == 0
        print("total")
        print("total")
    print("done")

function helper()
    print("helper")
PNX
cat > "$PROJECT/src/extra.pnx" <<'PNX'
function extra()
    let count = 1
    print(count)
PNX
echo "EDITOR BLOCK 2 TEST PROJECT: $PROJECT"
echo "1. Verify line numbers and syntax colors; edit nested function and press Enter."
echo "2. Type ( [ { and quotes; use Cmd+Z/Cmd+Shift+Z."
echo "3. Select 'total', press Cmd+D twice and replace both occurrences."
echo "4. Try Cmd+Option+Down and Option+Click for extra carets, type text and Esc."
echo "5. Try Cmd+/, Cmd+Shift+D, Option+ArrowUp/ArrowDown."
echo "6. Use Find/Replace, Fold/Unfold and Preview gutter arrows."
echo "7. Switch between files, Save each via Cmd+S, reopen and check the text."
echo "All test files are isolated. No existing project files will be modified."
cd "$ROOT"
bash scripts/run_ide_workspace.sh "$PROJECT" \
  --compiler-python /Users/morphey/PycharmProjects/PYNIX/.venv/bin/python \
  --ide-core /Users/morphey/PycharmProjects/PYNIX_IDE

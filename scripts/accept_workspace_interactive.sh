#!/usr/bin/env bash
# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
# Non-destructive interactive acceptance of native Zunyite Workspace V4.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
COMPILER="${ZUNYITE_COMPILER_ROOT:-$ROOT/../Zunyite}"
CORE="${ZUNYITE_IDE_ROOT:-$ROOT/../Zunyite_IDE}"
PYTHON="$COMPILER/.venv/bin/python"
if [[ ! -x "$PYTHON" || ! -f "$CORE/src/workspace_read_host.uny" ]]; then
  echo "Expected sibling Zunyite/.venv and Zunyite_IDE checkout" >&2
  exit 2
fi
PROJECT="$(mktemp -d "${TMPDIR:-/tmp}/zunyite-gui-acceptance.XXXXXX")"
mkdir -p "$PROJECT/src"
cat > "$PROJECT/zunyite.toml" <<'TOML'
[project]
name = "workspace-acceptance"
source = "src"
entry = "main.uny"
TOML
cat > "$PROJECT/src/main.uny" <<'UNY'
function main()
    first = 3
    second = first + 4
    print(second)
UNY
cat > "$PROJECT/src/helper.uny" <<'UNY'
function helper()
    return 42
UNY
cat > "$PROJECT/src/legacy.pnx" <<'PNX'
function legacy()
    return 1
PNX

echo "Temporary project: $PROJECT"
echo "1. Verify IDE Core: connected in the native window."
echo "2. Open src/main.uny; Run Current File must print 7."
echo "3. Change the 4 on line 3 to 5; Cmd+S; Run must print 8."
echo "4. Revert it to 4 and Cmd+S before debugging."
echo "5. Click gutter beside line 4 (print(second)) to set a breakpoint."
echo "6. Start Debug; Continue to breakpoint; expect line 4 paused and second=7."
echo "7. Verify Locals/Call Stack, Step Into, Step Over and Continue."
echo "8. Open helper.uny; switch between tabs and verify content remains intact."
echo "9. Create src/created.uny via Project > New File; save it and reopen."
echo "10. Rename created.uny to renamed.uny with its tab closed; verify tree."
echo "11. With a deliberate syntax error in helper.uny, Save, check Problems,"
echo "    then undo the error and save again."
echo "12. Confirm Terminal, Run, Problems, Git and Settings can open/close."
echo "All changes are restricted to the temporary project above."
echo
cd "$ROOT"
exec bash scripts/run_ide_workspace.sh "$PROJECT" \
  --ide-core "$CORE" --compiler-python "$PYTHON"

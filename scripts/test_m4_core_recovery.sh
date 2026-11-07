#!/usr/bin/env bash
# Isolated manual Core crash/recovery acceptance test for macOS.
# Does not modify or delete any existing Zunyite project.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$(mktemp -d "${TMPDIR:-/tmp}/zunyite-m4-recovery.XXXXXX")"
mkdir -p "$PROJECT/src"
cat > "$PROJECT/zunyite.toml" <<'TOML'
[project]
name = "m4-recovery-test"
source = "src"
entry = "first.uny"
TOML
cat > "$PROJECT/src/first.uny" <<'UNY'
function main()
    print("first-original")
UNY
cat > "$PROJECT/src/second.uny" <<'UNY'
function second()
    print("second-original")
UNY
echo "ISOLATED PROJECT: $PROJECT"
echo "Only edit first.uny and second.uny in this temporary project."
echo "1. Edit both .uny files WITHOUT saving."
echo "2. Note the Core PID in the bottom-right IDE Core indicator."
echo "3. In a separate Terminal run: kill -9 <CORE_PID> (replace with the exact displayed number)."
echo "4. Click the Core indicator to restart and restore both buffers."
echo "5. Switch between both tabs; verify BOTH unsaved edits are present."
echo "6. Save both files and verify their contents in the printed temporary directory."
echo "Do not use killall, pkill or a PID guessed from unrelated processes."
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

#!/usr/bin/env bash
# Isolated manual Core crash/recovery acceptance test for macOS.
# Does not modify or delete any existing PYNIX project.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$(mktemp -d "${TMPDIR:-/tmp}/pynix-m4-recovery.XXXXXX")"
mkdir -p "$PROJECT/src"
cat > "$PROJECT/pynix.toml" <<'TOML'
[project]
name = "m4-recovery-test"
source = "src"
entry = "first.pnx"
TOML
cat > "$PROJECT/src/first.pnx" <<'PNX'
function main()
    print("first-original")
PNX
cat > "$PROJECT/src/second.pnx" <<'PNX'
function second()
    print("second-original")
PNX
echo "ISOLATED PROJECT: $PROJECT"
echo "Only edit first.pnx and second.pnx in this temporary project."
echo "1. Edit both .pnx files WITHOUT saving."
echo "2. Note the Core PID in the bottom-right IDE Core indicator."
echo "3. In a separate Terminal run: kill -9 <CORE_PID> (replace with the exact displayed number)."
echo "4. Click the Core indicator to restart and restore both buffers."
echo "5. Switch between both tabs; verify BOTH unsaved edits are present."
echo "6. Save both files and verify their contents in the printed temporary directory."
echo "Do not use killall, pkill or a PID guessed from unrelated processes."
cd "$ROOT"
bash scripts/run_ide_workspace.sh "$PROJECT" \
  --compiler-python /Users/morphey/PycharmProjects/PYNIX/.venv/bin/python \
  --ide-core /Users/morphey/PycharmProjects/PYNIX_IDE

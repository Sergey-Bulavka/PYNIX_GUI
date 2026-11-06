#!/usr/bin/env bash
# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0
# Full acceptance of three sibling checkouts. Safe: no pull/reset or edits to source.
set -euo pipefail

GUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
WORKSPACE="$(cd "$GUI/.." && pwd -P)"
COMPILER="${ZUNYITE_COMPILER_ROOT:-$WORKSPACE/Zunyite}"
IDE="${ZUNYITE_IDE_ROOT:-$WORKSPACE/Zunyite_IDE}"
MODE="${1:-full}"
if [[ "$MODE" != "full" && "$MODE" != "quick" ]]; then
  echo "Usage: bash scripts/verify_full_stack.sh [full|quick]" >&2
  exit 2
fi

for path in "$COMPILER" "$IDE" "$GUI"; do
  if [[ ! -d "$path/.git" ]]; then
    echo "Missing Git checkout: $path" >&2
    exit 2
  fi
done

COMPILER_PY="$COMPILER/.venv/bin/python"
IDE_PY="$IDE/.venv/bin/python"
GUI_PY="$GUI/.venv/bin/python"
for executable in "$COMPILER_PY" "$GUI_PY"; do
  if [[ ! -x "$executable" ]]; then
    echo "Missing Python environment: $executable" >&2
    exit 2
  fi
done
if [[ ! -x "$IDE_PY" ]]; then
  IDE_PY="$COMPILER_PY"
fi

export PYTHONPATH="$COMPILER:$GUI:$IDE/tests${PYTHONPATH:+:$PYTHONPATH}"

step() {
  echo
  echo "================================================================"
  echo "== $1"
  echo "================================================================"
}
for path in "$COMPILER" "$IDE" "$GUI"; do
  step "Git state: $path"
  git -C "$path" log -1 --format='%h %s'
  git -C "$path" diff --check
  git -C "$path" status --short
done

if [[ "$MODE" == "full" ]]; then
  step "Compiler: full suite"
  (cd "$COMPILER" && "$COMPILER_PY" -m pytest -q)

  step "Official IDE Core: full suite (isolated test-path overrides)"
  (cd "$IDE" && unset ZUNYITE_TEST_ROOT ZUNYITE_TEST_PYTHON PYNIX_TEST_ROOT PYNIX_TEST_PYTHON && "$IDE_PY" -m pytest -q)

  step "Workspace V4 GUI: full suite"
  (cd "$GUI" && "$GUI_PY" -m pytest -q)
else
  step "Compiler: migration and repository contract"
  (cd "$COMPILER" && "$COMPILER_PY" -m pytest -q \
    tests/test_repository_contract.py tests/test_zunyite_examples_migration.py)
  step "GUI: relevant Run/Core/Debug tests"
  (cd "$GUI" && "$GUI_PY" -m pytest -q \
    tests/test_ide_workspace_launcher.py \
    tests/test_ide_project_runner.py \
    tests/test_ide_workspace_session.py \
    tests/test_ide_core_persistent.py \
    tests/test_ide_debug_process_client.py)
fi

step "Real compiler + official IDE Core integration"
"$COMPILER_PY" "$IDE/scripts/verify_zunyite_integration.py" \
  --compiler "$COMPILER" --python "$COMPILER_PY"

step "Isolated live Core buffer/recovery + Run Current File"
(cd "$GUI" && "$GUI_PY" scripts/smoke_full_stack.py \
  --ide-core "$IDE" --compiler-python "$COMPILER_PY")

step "Live debugger protocol bridge (legacy .pnx compatibility)"
(cd "$GUI" && "$COMPILER_PY" scripts/test_real_debugger_bridge.py)

step "AUTOMATED CHECKS PASSED"
echo "Native macOS interaction still needs visual/manual acceptance."
echo "No existing project source was edited by the live integration smoke."

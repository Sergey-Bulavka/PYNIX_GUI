#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Missing executable virtualenv Python: $PYTHON" >&2
  echo "Create the project virtual environment first." >&2
  exit 2
fi

echo "Using Python: $("$PYTHON" -c 'import sys; print(sys.executable)')"

run_tests() {
  "$PYTHON" -m pip install -e . pytest
  "$PYTHON" -m pytest -q
}

run_gallery() {
  echo
  echo "============================================================"
  echo "Product Gallery: examples/showcase.py"
  echo "Explore all Gallery sections, then close the window."
  echo "============================================================"
  "$PYTHON" examples/showcase.py
}

run_smokes() {
  local scripts=(
    "examples/adv_01_commands_smoke.py"
    "examples/adv_02_tree_table_smoke.py"
    "examples/adv_03_drag_dock_smoke.py"
    "examples/adv_04_canvas_smoke.py"
    "examples/adv_05_editor_smoke.py"
    "examples/resources_smoke.py"
  )

  for script in "${scripts[@]}"; do
    echo
    echo "============================================================"
    echo "Native smoke: $script"
    echo "Close the window after checking it to continue."
    echo "============================================================"
    "$PYTHON" "$script"
  done
}

case "$MODE" in
  tests)
    run_tests
    ;;
  smokes)
    run_smokes
    ;;
  gallery)
    run_gallery
    ;;
  all)
    run_tests
    run_smokes
    run_gallery
    ;;
  *)
    echo "Usage: bash scripts/verify_macos.sh [tests|smokes|gallery|all]" >&2
    exit 2
    ;;
esac

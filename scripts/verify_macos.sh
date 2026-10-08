#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Missing .venv. Create the project virtual environment first." >&2
  exit 2
fi

source .venv/bin/activate

run_tests() {
  python -m pip install -e .
  python -m pytest -q
}

run_smokes() {
  local scripts=(
    "examples/adv_01_commands_smoke.py"
    "examples/adv_02_tree_table_smoke.py"
    "examples/adv_03_drag_dock_smoke.py"
    "examples/adv_04_canvas_smoke.py"
    "examples/adv_05_editor_smoke.py"
    "examples/resources_smoke.py"
    "examples/showcase.py"
  )

  for script in "${scripts[@]}"; do
    echo
    echo "============================================================"
    echo "Native smoke: $script"
    echo "Close the window after checking it to continue."
    echo "============================================================"
    python "$script"
  done
}

case "$MODE" in
  tests)
    run_tests
    ;;
  smokes)
    run_smokes
    ;;
  all)
    run_tests
    run_smokes
    ;;
  *)
    echo "Usage: bash scripts/verify_macos.sh [tests|smokes|all]" >&2
    exit 2
    ;;
esac

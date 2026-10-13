#!/usr/bin/env bash
# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "PYNIX GUI virtual environment not found: $PYTHON" >&2
  exit 2
fi
if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/run_ide_workspace.sh /path/to/project [extra V4 options]" >&2
  exit 2
fi
PROJECT="$1"
shift
if [[ ! -d "$PROJECT" ]]; then
  echo "Project directory not found: $PROJECT" >&2
  exit 2
fi

cd "$ROOT"
exec "$PYTHON" -m examples.ide_native_v4 --project "$PROJECT" "$@"

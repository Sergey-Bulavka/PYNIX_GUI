#!/usr/bin/env bash
# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Zunyite GUI virtual environment not found: $PYTHON" >&2
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

# Automatically connect the official IDE Core when its checkout is nearby.
# Explicit --ide-core takes precedence; ZUNYITE_IDE_CORE=off disables discovery.
# The workspace remains usable in standalone GUI mode when no Core is installed.
CORE="${ZUNYITE_IDE_CORE:-$ROOT/../Zunyite_IDE}"
EXPLICIT_CORE=false
for arg in "$@"; do
  if [[ "$arg" == "--ide-core" || "$arg" == --ide-core=* ]]; then
    EXPLICIT_CORE=true
    break
  fi
done
if [[ "$EXPLICIT_CORE" == false && "$CORE" != off && -f "$CORE/src/workspace_read_host.uny" ]]; then
  echo "Connecting Zunyite IDE Core: $CORE"
  cd "$ROOT"
  exec "$PYTHON" -m examples.ide_native_v4 --project "$PROJECT" --ide-core "$CORE" "$@"
fi

cd "$ROOT"
exec "$PYTHON" -m examples.ide_native_v4 --project "$PROJECT" "$@"

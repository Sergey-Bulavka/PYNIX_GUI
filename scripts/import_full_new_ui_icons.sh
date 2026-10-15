#!/usr/bin/env bash
# Import all explicitly Apache-2.0 JetBrains IntelliJ New UI SVG assets.
# Sparse clone keeps the checkout bounded: no IDE source tree is downloaded.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi
DEST="$ROOT/pynix_gui/assets/jetbrains_new_ui"

MODE="${1:---dry-run}"
if [[ "$MODE" != "--dry-run" && "$MODE" != "--apply" ]]; then
  echo "Usage: $0 [--dry-run|--apply]" >&2
  exit 2
fi
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT

echo "Fetching only official JetBrains New UI icons (sparse checkout)…"
git clone --quiet --depth=1 --filter=blob:none --sparse \
  https://github.com/JetBrains/intellij-community.git "$TEMP/intellij-community"
git -C "$TEMP/intellij-community" sparse-checkout set platform/icons/src/expui
SOURCE="$TEMP/intellij-community/platform/icons/src/expui"
REVISION="$(git -C "$TEMP/intellij-community" rev-parse HEAD)"
echo "JetBrains upstream commit: $REVISION"
if [[ ! -d "$SOURCE" ]]; then
  echo "Official expui source directory is missing: $SOURCE" >&2
  exit 1
fi

if [[ "$MODE" == "--dry-run" ]]; then
  "$PYTHON" -m pynix_gui.ide_jetbrains_icons "$SOURCE" "$DEST" --dry-run
  echo "No files have been modified. Run --apply after reviewing licensing."
else
  "$PYTHON" -m pynix_gui.ide_jetbrains_icons "$SOURCE" "$DEST"
  printf '%s\n' "$REVISION" > "$DEST/UPSTREAM_COMMIT"
  "$PYTHON" -m examples.icon_catalog_gallery "$DEST"
  echo "Imported approved files and generated offline gallery."
  echo "Review git diff before committing the expanded icon catalog."
fi

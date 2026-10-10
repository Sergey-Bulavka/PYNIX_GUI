# Stability & Release Readiness — audit (2026-10-10)

## Current baseline

- PYNIX GUI version: **0.1.6-dev**, explicitly **pre-alpha** in packaging.
- Standalone Python API and PYNIX language adapter have been accepted on real macOS.
- Responsive Workspace V2, Responsive Content V1, text layout V1–V4,
  and Advanced Components Quality V1 have passed user macOS smoke checks.
- GitHub CI tests Python 3.12 on macOS, Windows, and Ubuntu.
- **Native interactive Windows/Qt acceptance is still missing.**
- Linux is a layout/model test platform, not an advertised native backend.

## Reliability and API checks

1. The public `pynix_gui.__all__` and installed package `py.typed` must remain
   importable. The declared `pyproject.toml` version must match the runtime.
2. The runtime provides stable `PYNIX-GUI-00x` codes and chains backend errors.
3. `GUIEvent` validates well-formed controls and finite window resize events.
4. The manually driven AppKit event loop must route menu shortcuts while
   retaining native editing keys.
5. Responsive layout must honor **minimum** widths separately from desired/
   preferred widths, retaining scroll access for wide Table and Canvas.
6. Focus, keyboard tab-order, high DPI and cross-platform native scrollbar
   behavior require live interaction testing; headless tests are not proof.

## Fixes implemented in this gate

- CI now builds both source distribution and wheel on all three platforms.
- `scripts/check_dist.py` validates package contents including `py.typed`,
  and imports the installed wheel in an isolated virtual environment.
- Regression tests pin importable public names and release metadata.
- Update the release documentation to reflect completed responsive work.

## Release decision: HOLD

Do **not** tag 0.2.0 or call this a production-ready commercial GUI until:
- interactive Windows/Qt validation (keyboard, editor, table, Canvas, dialogs,
  resizing, theme and HiDPI);
- manual macOS light/dark and VoiceOver review;
- repeated use of a non-demo PYNIX application for regression coverage;
- review of metadata/version gates and clean artifact installation;
- confirmation from owner that the documented limitations are acceptable.

The version remains **0.1.6-dev**. Passing CI is necessary but not sufficient
for a release.

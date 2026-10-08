# Consolidated Verification Plan

Run this plan after the current large implementation batch. Do not skip directly to Showcase.

## Phase A — install and full standalone regression

macOS:

```bash
cd /Users/morphey/PycharmProjects/PYNIX_GUI
git pull --ff-only
source .venv/bin/activate
python -m pip install -e .
python -m pytest -q
```

Expected collection is approximately 96 tests after the current batch. The exact collected
count is authoritative; zero failures are required.

If collection fails, fix import/syntax/contract issues before any native smoke.

## Phase B — focused regressions

```bash
python -m pytest tests/test_advanced_canvas.py -q
python -m pytest tests/test_advanced_editor.py -q
python -m pytest tests/test_resources.py -q
python -m pytest tests/test_windows_backend_contract.py -q
```

Also rerun previously accepted Advanced suites:

```bash
python -m pytest tests/test_advanced_commands.py -q
python -m pytest tests/test_advanced_structured.py -q
python -m pytest tests/test_advanced_drag_dock.py -q
```

## Phase C — macOS native acceptance

Run one at a time:

```bash
python examples/adv_01_commands_smoke.py
python examples/adv_02_tree_table_smoke.py
python examples/adv_03_drag_dock_smoke.py
python examples/adv_04_canvas_smoke.py
python examples/adv_05_editor_smoke.py
python examples/resources_smoke.py
python examples/showcase.py
```

### ADV-04 Canvas checks

- window renders without traceback;
- rectangle, ellipse, triangle/path and text are visible;
- clipping/transform example is visible;
- resize scales retained scene;
- clicking card/circle/triangle emits ACTIVATE with the semantic hit target;
- no raw coordinate/native event appears.

### ADV-05 Rich Editor checks

- initial syntax-style spans are visible;
- typing works;
- Backspace/Delete work;
- arrows/Home/End/PageUp/PageDown work;
- multiline selection works;
- mouse selection works;
- scrolling works;
- Cmd+A/C/X/V/Z behave natively;
- selection events do not trap or jump caret;
- text edits emit CHANGE;
- closing exits cleanly.

### Resource checks

- logical vector resource resolves by catalog name;
- vector icon renders at requested size;
- no native image object is passed by application code;
- missing-resource behavior is noted for follow-up rather than crashing the process.

### ADV-01 regression polish checks

- a standard macOS application menu exists automatically;
- File/View application menus remain present;
- controls embedded inside dialog content emit normal GUIEvent values;
- dialog controls remain interactive after the main window rerenders while a sheet is open.

### Showcase checks

- toolbar and status bar look coherent;
- project Tree works with keyboard;
- Table selection works;
- Rich Editor works;
- Canvas is visible and clickable;
- menu shortcut opens dialog;
- dialog closes cleanly;
- resize remains usable;
- System appearance remains readable.

## Phase D — appearance

Repeat Showcase in macOS Light and Dark appearances.

Verify:

- primary/secondary text contrast;
- selected rows;
- editor background/text;
- separators/borders;
- Canvas semantic colors;
- disabled state;
- focus visibility;
- dialog/menu legibility.

## Phase E — Windows parity

On the Windows machine:

```powershell
cd <PYNIX_GUI checkout>
py -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m pytest -q
.venv\Scripts\python examples\showcase.py
```

Verify the Windows checklist in docs/WINDOWS_BACKEND.md.

Do not mark Windows parity accepted from CI alone; real interactive Windows verification is
required.

## Phase F — CI

Check GitHub Actions on:

- macos-latest;
- windows-latest;
- ubuntu-latest.

Ubuntu proves backend-neutral model/layout portability only.

## Phase G — acceptance/versioning

Only after green evidence:

1. mark ADV-04 ACCEPTED;
2. bump to 0.1.4-dev;
3. mark ADV-05 ACCEPTED;
4. bump to 0.1.5-dev;
5. accept resources/macOS product polish;
6. bump to 0.1.6-dev;
7. accept Windows parity after real Windows smoke;
8. bump to 0.2.0-dev;
9. synchronize README, roadmap and completion gate;
10. then begin PYNIX language-surface integration/finalization and later IDE work.


## Phase H — PYNIX language integration

After standalone PYNIX_GUI is green, verify the language adapter and static surface:

```bash
cd /Users/morphey/PycharmProjects/PYNIX
git pull --ff-only
source .venv/bin/activate
python -m pip install -e ../PYNIX_GUI
python -m pytest   tests/test_gui_core.py   tests/test_gui_controls.py   tests/test_gui_layout.py   tests/test_gui_surfaces.py   tests/test_gui_design.py   tests/test_gui_runtime_adapter.py   tests/test_gui_package_ownership.py   tests/test_gui_advanced_product.py   -q
```

Then run the full PYNIX regression:

```bash
python -m pytest -q
```

The prior accepted baseline was 3912 passed, 43 skipped, with one unrelated duplicate-zip
warning. The new exact count is authoritative; zero failures are required.

Finally run the real PYNIX-language native smoke:

```bash
PYTHONPATH=/Users/morphey/PycharmProjects/PYNIX \
/Users/morphey/PycharmProjects/PYNIX/.venv/bin/python \
-m compiler examples/gui_advanced_product_smoke.pnx
```

Verify that MenuBar, Tree, Table, Rich Editor, Canvas and Dialog are reached through PYNIX
source rather than direct Python standalone calls.

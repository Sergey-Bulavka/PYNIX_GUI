# PyCharm Settings reference → PYNIX Settings implementation contract

Status: **documentation and architecture baseline**, not a claim that Settings
pages have been implemented. Reference: official PyCharm 2026.2 help and
six user-supplied macOS PyCharm Settings screenshots (2026-10-19). The
screenshots show **a particular installation's configured state**, not
necessarily factory defaults.

## 1. Non-negotiable architecture

PyCharm has THREE distinct kinds of settings that PYNIX must model:

1. **IDE/global** — appearance, IDE UI font and zoom, keymap, editor's default
   font, general editing preferences, general tool-window behavior. Used for
   all projects opened in one installation.
2. **Current project** — project code style, inspections, file encodings,
   per-path overrides, Python/PYNIX runtime/tooling, VCS, run/debug
   configurations and project-local profiles.
3. **Defaults for new projects** — a template applied to newly created
   projects; MUST NOT retroactively overwrite existing projects.

Effective values must be resolved as `explicit project value >
new-project template only at project creation > global default > built-in
default`. Some settings are GLOBAL-ONLY and MUST NOT be overridden by the
project layer (e.g. IDE zoom); some are PROJECT-ONLY. Every option must
declare scope, type, default, capability, migration and runtime consumer.

Use separate persistence namespaces, not one localStorage blob:
- macOS global: OS user config/application support directory.
- Per-project settings: structured profile keyed by resolved project path or
  shareable project config if explicitly opted in, **never silently write**
  into user source directories.
- New-project template: separate persisted profile, copied when project created.
- Frontend stores only view state; the Python host is authoritative for
  settings that affect reading/writing code, compilers or project storage.
- `Cancel` drops a working copy, `Apply` persists and applies without closing,
  `OK` persists/applies and closes, `Restore Defaults` restores the relevant
  scope only. Dirty state enables Apply; invalid input disables Apply/OK.
- Never expose a working checkbox when the required backend behavior is absent.
  Unsupported settings may be shown as disabled with an explanation.

**Font separation (the mistake behind Services Options comparisons):**
- **IDE UI font**: menus, tool windows, buttons, tree rows.
- **Editor font**: code in tabs; point size and line-height multiplier.
- **Console font**: separate from both UI and editor.
- **IDE zoom**: scaling for all UI dimensions (fonts, icon boxes, padding).
- **Retina / backing scale factor**: device pixels per logical CSS pixel.
- A screenshot showing Editor | Font | Size `13.0` is **13 pt for editor code**,
  NOT an instruction to force every menu to `13px`.
- A JetBrains 16x16 source SVG has a viewBox/source size; final optical pixel
  size depends on IDE zoom, platform scaling, component layout and CSS.
  Never calibrate icons separately to arbitrary screenshots with no control
  over all four factors.

Sources:
- https://www.jetbrains.com/help/pycharm/configuring-project-and-ide-settings.html
- https://www.jetbrains.com/help/pycharm/project-and-ide-settings.html
- https://www.jetbrains.com/help/pycharm/setting-up-your-project.html
- https://www.jetbrains.com/help/pycharm/settings-appearance.html
- https://www.jetbrains.com/help/pycharm/settings-editor-font.html

## 2. Initial navigation tree to implement

Settings — PYNIX (macOS native window, searchable tree on left,
breadcrumb/content right, stable bottom bar: Help, Cancel, Apply, OK):

- **Appearance & Behavior**
  - Appearance: Theme, Sync with OS, UI zoom, UI font, compact mode,
    scrollbar contrast, UI/editor text antialiasing.
  - System Settings: project directory, reopen previous project and other
    **verified** host capabilities; don't expose nonfunctional items.
  - Menus and Toolbars: later, once command registry is stable.
  - Notifications and Keymap: separate later contracts.
- **Editor**
  - General: Code Completion, Auto Import, Smart Keys, Editor Tabs,
    Caret/Appearance, Gutter, Soft Wraps, Code Folding.
  - **Code Editing**
  - **Font**
  - **Color Scheme**, including scheme-specific font override.
  - **Code Style**
  - **Inspections**
  - **File and Code Templates**, **File Types**.
  - **TODO**, **Reader Mode**, **Minimap**, **Intentions**, **File Encodings**.
- **Build / Run / Debug**, **Languages & Frameworks**, **Tools**: introduce
  only when the corresponding PYNIX and Python backend capabilities exist.
- **Settings for New Projects**: separate entry/context, using ONLY project
  setting categories and defaults, not a second global IDE-settings screen.

Tree order should follow real user expectations while retaining PYNIX-specific
items as explicit additions; do not copy whole PyCharm settings categories
if PYNIX has no behavior for them.

## 3. Screenshots inventory (USER CONFIGURATION, not vendor defaults)

These are verified on the uploaded 2026-10-19 screenshots:

| Area | Visible option/state | PYNIX design rule |
| --- | --- | --- |
| Code Editing | Matched brace **on**, current scope **off**, usages at caret **on** | Highlight requires an actual editor selection/highlight engine |
| Code Editing | Quick documentation on hover **on** | Respect tooltip delay and symbol availability |
| Code Editing | Refactoring confirmation **In editor**, preselect current name **on**, inline local dialog **on** | Must hook real rename/inline symbol workflow |
| Code Editing | Error stripe min height **2 px**, autoreparse **300 ms**, next-error highest priority | Tie to diagnostics pipeline, not just CSS |
| Code Editing | Editor tooltip delay **500 ms** | Common tooltip scheduling contract |
| TODO | Multiline indented TODO **on**, patterns **TODO** and **FIXME**, no custom filters | Regex scanner over comments, configurable flags |
| Reader Mode | Enable **on**; render docs **on**; warning widget, ligatures, larger height **off** | Auto-activate only for supported read-only/library files |
| Reader Mode | Virtual format code **on**, active color scheme selected | MUST NOT mutate source buffer |
| Minimap | Enable **off**, Position **Right**, Scale **Fill**; other controls disabled | Do not render miniature editor while disabled |
| Intentions | Enabled tree with selected intention and Before/After samples | Source registry of *implemented* intentions only |
| File Encodings | Global **UTF-8**, Project **System Default UTF-8** | Explicit precedence, BOM/declared-encoding handling |
| File Encodings | Per-path table empty, properties UTF-8, native-to-ascii off, UTF-8 without BOM | Files saved safely (no silent recoding/loss) |
| Editor Font | JetBrains Mono, `13.0 pt`, line-height `1.2`, ligatures off (earlier user screenshot) | Editor-only, not UI/global CSS font size |

**Do not mislabel observed checkbox states as PyCharm factory defaults.**
Known vendor-documented defaults include:
- Editor default font line-height multiplier **1.2** (Font documentation).
- Two built-in TODO patterns: case-insensitive **TODO/FIXME**.
- Default editor tab limit **10**.
- UTF-8 files created **without BOM** by default.
Other defaults must be measured from a clean, version-matched PyCharm profile
or labeled **PYNIX proposed default**, not presented as authoritative.

## 4. Feature behavior and dependencies

### 4.1 Appearance & Behavior | Appearance (P0)
- Separate `ui.font.family`, `ui.font.size`, `ui.zoom`, `ui.compact`,
  `ui.theme` and `editor.font.*` (no shared `font-size` global selector).
- Set CSS variables on the V4 root, e.g. `--pynix-ui-font-size`,
  `--pynix-ui-scale`, `--pynix-jetbrains-icon-size`,
  `--pynix-ui-row-height`. UI zoom changes these **coherently**;
  macOS screenshot comparison must control backing pixel ratio.
- Use the existing licensed JetBrains icon catalog with native viewBox;
  icon size and button hit area are separate dimensions.
- Persist scope globally; keyboard/mouse accessibility unchanged.

### 4.2 Editor | General (P0)
- Appearance: show line numbers, breadcrumbs, current line highlighting,
  soft wraps, folding and caret preferences (only where editor API exists).
- Tabs: placement, single/multiple row behavior, overflow, pinning and
  preview tabs. **PyCharm's documented default tab limit is 10**.
  Existing PYNIX tab mechanisms must be reused.
- Code Completion/Auto Import/Smart Keys: use compiler language services and
  a documented PYNIX/Python capability matrix. Do not import symbols or
  auto-insert text if backend doesn't support reliable undo.
- Editor font size is in **points**; line-height multiplier is a factor.

### 4.3 Editor | Code Editing (P1)
- Matched bracket pairs and symbol usages: consume accurate caret positions
  and lexical/semantic mappings; avoid highlight flicker on tabs/layout.
- Documentation tooltip and delay: share scheduled hover mechanism.
- Error stripe/next-error behavior: consume real diagnostics severity/order.
- Refactoring controls must connect to actual rename/inline operations.

### 4.4 Editor | TODO (P1)
- Default patterns: `\\btodo\\b.*` and `\\bfixme\\b.*`,
  case-insensitive. Store patterns, case flags and named filters.
- Index only comment tokens where lexer support exists; ignore string
  literals. Group indented continuation lines if enabled.
- TODO tool window and settings must use the same matcher.

### 4.5 Editor | Reader Mode (P2)
- Read-only/library files only; rendered documentation is **not available for
  Python docstrings** per JetBrains. Respect language capabilities.
- Virtual formatting **never writes back into the source**.

### 4.6 Editor | Minimap (P2)
- Off by default in PYNIX until renderer exists; settings not a placebo.
- On enable: right/left placement, Fill/Fit scale, between scrollbar option,
  viewport thumb and click-to-scroll; Hover structural data only when
  compiler/index can provide structures.

### 4.7 Editor | Intentions (P2)
- Only real registered refactorings/quick-fixes; group/enable/disable,
  full-text search, Before/After previews from real examples.
- Do not clone PyCharm's JavaScript/CSS/Docker actions when PYNIX has no
  implementation.

### 4.8 Editor | File Encodings (P0 data safety)
- Precedence: explicit file/directory > project > global.
- Detect UTF-8 BOM and coding declarations before allowing overrides.
- Default PYNIX UTF-8 without BOM; explicit user confirmation before
  conversion that might lose data; preserve unsaved buffers.
- Properties encoding and native-to-ascii controls only when supported by
  actual properties handler.

Sources:
- https://www.jetbrains.com/help/pycharm/code-editing.html
- https://www.jetbrains.com/help/pycharm/using-todo.html
- https://www.jetbrains.com/help/pycharm/reader-mode.html
- https://www.jetbrains.com/help/pycharm/settings-file-encodings.html
- https://www.jetbrains.com/help/pycharm/intentions-settings.html
- https://www.jetbrains.com/help/pycharm/using-code-editor.html
- https://www.jetbrains.com/help/pycharm/creating-and-optimizing-imports.html

## 5. Actual PYNIX repository audit (2026-10-19)

Branch: `feature/icon-system-v4`.

- `examples/ide_native_v4.py` is the supported macOS host.
- `pynix_gui/ide_workspace_preview.py` has editor/render runtime and
  tool-window integrations but no centralized IDE/project/default settings
  model or native Settings dialog.
- `pynix_gui/ide_native_menu.py` currently has no Settings storage.
- `docs/IDE_V4_TOPBAR_SEARCH_SETTINGS_BETA_GATE.md` explicitly says the
  toolbar Settings gear only delegates to an existing tool action/window;
  **it is not evidence of a full PyCharm Settings implementation.**
- There are localized preferences in Services, Packages, Terminal; they
  should migrate to a versioned settings service with compatibility reads.
- Keep `PYNIX`, `PYNIX_GUI` and `PYNIX_IDE` boundaries explicit; UI
  settings belong to IDE/GUI host, compiler analysis defaults belong to
  language/tooling integration.

## 6. Implementation batches, in dependency order

1. **Settings data core**: typed/versioned registry; global/project/new-project
   scopes, defaults and inheritance; atomic persistence, corruption recovery,
   validation and migration; unit tests.
2. **Native Settings shell**: navigation tree, search, breadcrumbs,
   project badges, Cancel/Apply/OK/Reset, unsaved-changes handling,
   keyboard focus, dark/light consistent with UI metrics.
3. **Appearance / Editor Font / Console Font**: real live previews;
   persistent UI zoom; canonical scales and JetBrains icon metrics.
   This is the prerequisite for visually correcting Services Options.
4. **Editor General / Tabs / Code Editing**: connect only to real editor
   events and compiler analysis; tests for open buffers, caret, diagnostics.
5. **Encodings / TODO**: filesystem-safe overrides, comment index,
   filters and actual tool window with tests.
6. **Reader / Minimap / Intentions**: stage behind feature capabilities;
   implement and test behavior before enabling interactive toggles.
7. **Project default templates + migration**: new-project-only application,
   import/export, backward compatible migration from scattered localStorage.
8. **Mac acceptance**: compare PyCharm and PYNIX at the same display zoom,
   backing pixel scale, OS font smoothing, window size and selected theme.
   Run focused + full pytest, macOS smoke, file save/undo tests.

## 7. Acceptance: do not mistake a mock UI for a finished feature

- Global setting persists across two projects, a project setting does not
  leak into another, and new-project defaults affect only new projects.
- Cancel discards all staged changes; Apply applies only validated options;
  OK closes after success; version upgrade handles old profiles.
- Changing Editor Font does not change Services/Packages/Terminal menus.
- Changing UI zoom changes icon dimensions, text and spacing together
  without CSS precedence fights or tab overlap.
- Minimap disabled means no minimap renders; TODO filters work on real code;
  reader mode never modifies source; encodings avoid BOM-related breakages.
- Disabled or unavailable options are never represented as working toggles.
- Screenshot parity is measured on macOS only after the *same* UI font
  settings and backing/display zoom are confirmed in both apps.

**This document is a contract for the next implementation step.**
It intentionally does NOT assert that the current PYNIX GUI implements these
PyCharm behaviors.

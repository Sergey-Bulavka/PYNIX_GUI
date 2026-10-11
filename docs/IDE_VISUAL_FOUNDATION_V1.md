# PYNIX IDE Visual Foundation V1

Status: implementation contract (visual acceptance pending).

## Product target
An IDE-first desktop experience with a stable spatial hierarchy. Build a *visual shell* before moving functional editor commands into it. The shell must be reusable in PYNIX_GUI, not a collection of PYNIX_IDE-specific hacks.

## Spatial contract
At reference size 1440 × 900:
- Top application bar: 48 px; app identity, current project, window tools.
- Primary toolbar: 40 px; compact action affordances (do not render long rows of buttons).
- Left activity rail: 48 px, never scrolls with file explorer.
- Explorer sidebar: default 256 px, minimum 192 px, resizable; tree rows aligned on baseline, disclosure arrows centered.
- Center document area: consumes all remaining width, editor tabs 36 px, source editor fills available height.
- Bottom workspace: initial 208 px, resizable or collapsible; terminal / problems / output tabs.
- Status bar: 26 px pinned to window bottom, project state + line/column + encoding + diagnostics.
- Right tool area: closed by default; opens to show inspector on explicit action.
- Minimum usable desktop viewport: 1024 × 640; below minimum, prioritize center editor and collapse auxiliary tools, never overlap or clip action labels.

## Style tokens
Colors (dark reference):
- canvas: #11151C; chrome: #171D26; sidebar: #1A222D; surface: #202B39.
- border: #303A49; primary text: #E5EDF8; muted text: #97A9C0.
- accent: #70B7FF; selection: #28445F; positive: #80C9A4; error: #F08A91.
Typography:
- UI default 13 px, dense metadata 11 px, toolbar 12 px.
- Code editor uses an actual monospaced family at 13 px; line height 20 px.
- Scale icons to row text metrics, not hardcoded 24px for every use.
Geometry:
- base spacing 4 px; tree row 26 px; toolbar action 28–32 px.
- 1 px separator; corner radius 6 px for controls, 8 px for dialogs.
- Center document area should not have decorative card insets.

## Interactions / states
- Project opens into explorer and editor; source tabs persist across explorer navigation.
- Every tool area has collapsed, active, keyboard-focused and loading states.
- Hover types must not rewrite the source or move selection.
- Sources, references and diagnostics open in tool windows; long output is scrollable.
- Menus and buttons cannot push document editor off-screen.
- Resize layout at 1024/1280/1440/1920 px; allow side-by-side panel resizing and hide sidebars without repositioning editor content incorrectly.
- macOS traffic lights remain native and unobstructed.

## Development gates
1. GUI library supports theme token mapping, Dock/Split/Toolbar/Tab/StatusBar composition (reuse existing controls where appropriate).
2. Build a real `ide_shell_showcase` running on macOS with sample source text, mock diagnostics, explorer tree and terminal.
3. Screenshot acceptance: aligned text/icons, no blank unused work area, centered main editor, no clipping at four target widths.
4. Keyboard acceptance: navigate explorer/tree, switch tabs, focus editor, toggle bottom pane.
5. Only after gates 1–4: route existing PYNIX_IDE sessions and tooling into shell; bring Hover into editor.

## Deferred
No full debugger, AI features, plugin marketplace, remote development or parallel Windows-native UI redesign in this gate.

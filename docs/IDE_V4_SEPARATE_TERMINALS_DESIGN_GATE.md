# Design Gate — Separate system and PYNIX terminals in native IDE V4

## Task
The supplied PyCharm screenshots show a real shell picker (bash/zsh/Settings), a centered chevron, hover-only New Tab button and independent Python Console. PYNIX needs separate System Terminal and PYNIX Terminal, with mutually exclusive active icons and real commands.

## Reference review
- JetBrains Terminal creates genuine PTY shell sessions per tab, supports shell profiles and independent process lifetime.
- PyCharm Python Console runs language commands in an interpreter, separate from the system shell.
- VS Code panels demonstrate a shared docking host with independent tool states. A common container does not imply shared buttons, buffers or commands.
- Existing PYNIX V4 gave Terminal and PYNIX Terminal the same rail:4 action, with a disabled plus and a Unicode chevron. It was a Run output mock, not a terminal.

## Native implementation
1. Distinct actions terminal:system and terminal:pynix; each icon observes only its own scope and the actual dock visibility.
2. System Terminal uses independent POSIX PTY shell subprocesses (macOS bash/zsh), with opaque tab IDs, bounded output and keyboard writes, process close and app-exit cleanup. Maximum eight sessions. Opening Terminal does not launch a shell until requested.
3. Chevron uses a centered 15px SVG. Popup contains bash, zsh and Settings for default shell selection. Plus and chevron appear on dock hover and keyboard focus. Cmd+T creates a new session when the Terminal has focus.
4. PYNIX Console has separate input/output and only supports bounded, project-scoped commands: help, pwd, files and run FILE.pnx via the real PYNIX compiler. This is not yet a full PYNIX expression REPL and never pretends to be a Python interpreter.
5. Previous Run/Problems/Debug toolTabs and output snapshots are retained. Terminal consoles are distinct DOM panels; switching does not mix their data. When dock is hidden, editor/tree reclaim height.
6. Security: shell names are allowlisted; session count/input/output are bounded; children receive SIGHUP on close; PYNIX compiler cannot run source files outside the project; terminal text is never rendered as HTML.

## Acceptance
- New Local session accepts commands and prints actual bash/zsh output.
- Plus creates a second process; switch tabs and verify independent contents.
- Dropdown opens bash, zsh, Settings and returns after changing preference.
- System Terminal and PYNIX Terminal never highlight simultaneously.
- PYNIX Console help/files/run behave independently, and Run/Problems/Debug still work.
- Resizing the dock and hiding it do not leave a blank reserved area.
- Run full pytest and native macOS interactive visual acceptance. Static CSS/JS tests cannot verify mouse behavior in WKWebView.

## Tests
python -m pytest tests/test_ide_v4_separate_terminals.py tests/test_ide_v4_terminal_dock.py tests/test_ide_edge_profile.py -q

python -m pytest -q

git diff --check

# PYNIX interactive debugging — runtime integration gate

## Verified at source level (2026-10-14)

The compiler repository `Sergey-Bulavka/PYNIX` exposes
`compiler.backend.Interpreter`, `Interpreter.run()`, and the public
`execute(...)` function. Inspection of the current backend entry points
did **not** identify a public versioned pause/step/stack/variables debugger
protocol. Consequently the native IDE cannot honestly advertise breakpoints,
single-step execution, or variable inspection as working.

The IDE exposes `pynix-debug-capabilities` v1 with all interactive flags
disabled. Run and Check remain separate real compiler operations.

## Proposed compiler API — versioned v1

* `start(source, breakpoints)` — return session ID and initial state.
* `continue(session)`, `pause(session)`, `stepInto(session)`,
  `stepOver(session)`, `stepOut(session)`.
* `frames(session)`, `variables(session, frameId)`.
* `stop(session)` — terminate and clean up process.
* Events: started, stopped(reason, location), output, exited, error.
* All source locations are normalized project-relative paths with 1-based
  line/column; reject out-of-root files.
* Source-level stepping requires compiler IR to preserve source locations.
  If location mappings are missing, gate that operation off.
* Debug runtime must run separately from WKWebView and communicate over a
  bounded authenticated local channel; never execute scripts from web UI.

## Acceptance criteria

1. Pausing and continuing real interpreter code is deterministic.
2. Breakpoints respect actual executable lines.
3. StepOver does not enter calls; StepInto does; StepOut exits current frame.
4. Stack and variable values are fetched from the paused runtime only.
5. Runtime failures and user stop leave no orphan processes.
6. Feature capabilities report false until compiler tests prove each feature.

Do not implement decorative controls or use Python's pdb as a substitute
for stepping PYNIX IR. Add implementation in the language repo first,
then enable IDE controls through the versioned debugger protocol.

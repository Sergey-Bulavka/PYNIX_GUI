# GUI-ADV-05 — Rich Editor / Text Content

## Status

Implementation batch in progress; verification deferred to the consolidated test pass.

Target version after acceptance: **PYNIX GUI 0.1.5-dev**.

## Goal

Provide a professional, language-agnostic large-text editor suitable for source code, logs,
configuration, structured plain text and other text-heavy desktop applications.

## Public semantics

```text
GUITextSpan(start, end, role)

rich_editor(
    target,
    text,
    selectionStart,
    selectionEnd,
    spans=(),
    readOnly=false
)
```

The application owns text and selection state.

Text edits emit:

```text
GUIEvent("CHANGE", target=..., text=...)
```

Caret/selection movement emits:

```text
GUIEvent(
    kind="EDITOR_SELECTION",
    target=...,
    selection_start=...,
    selection_end=...
)
```

## Styling

Spans are language-agnostic semantic roles:

```text
plain keyword type string number comment function property
constant warning error muted strong
```

The editor does not know PYNIX syntax. A language service or ordinary application may
produce spans.

Spans are immutable, non-overlapping ranges inside the current text.

## Required desktop behavior

- editable and read-only modes;
- native caret and selection;
- keyboard navigation;
- multiline editing;
- native scrolling;
- monospaced default presentation;
- deterministic controlled rerender;
- selection restoration;
- semantic spans;
- large-document behavior without one native widget per line.

Raw NSTextView/Win32 edit handles remain private backend details.

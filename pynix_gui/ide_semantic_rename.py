"""Compiler-backed, reviewable symbol rename plans.

Returns complete before/after snapshots, never writes to disk. The editor
must verify each snapshot against its clean buffer before applying a plan.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re

from .ide_tooling_navigation import query_navigation

_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
_RESERVED = frozenset((
    "function", "module", "import", "from", "as", "let", "var", "const",
    "if", "elif", "else", "while", "for", "in", "return", "break",
    "continue", "class", "interface", "type", "enum", "match", "case",
    "try", "catch", "finally", "raise", "public", "private", "async",
    "await", "true", "false", "none", "null",
))


class RenamePlanError(ValueError):
    """Cannot safely construct the requested source rename plan."""


def _relative_project_path(root: Path, value: object) -> tuple[str, Path]:
    if not isinstance(value, str):
        raise RenamePlanError("Invalid symbol source")
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_relative_to(root) or path.suffix != ".pnx" or not path.is_file():
        raise RenamePlanError("Symbol spans outside indexed PYNIX sources")
    return path.relative_to(root).as_posix(), path


def _read_source(root: Path, source: object, originals: dict[str, str]) -> tuple[str, str]:
    relative, path = _relative_project_path(root, source)
    if relative not in originals:
        if len(originals) >= 100 or path.stat().st_size > 1_000_000:
            raise RenamePlanError("Rename exceeds safe file limits")
        try:
            originals[relative] = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError) as exc:
            raise RenamePlanError("Cannot read rename source") from exc
        if len(originals[relative].encode("utf-8")) > 1_000_000:
            raise RenamePlanError("Rename source exceeds 1 MB")
        if sum(len(value.encode("utf-8")) for value in originals.values()) > 2_000_000:
            raise RenamePlanError("Rename plan exceeds 2 MB of source")
    return relative, originals[relative]


def plan_semantic_rename(root: Path, compiler_python: Path,
                         source: str, line: int, column: int, new_name: str) -> dict:
    """Build conservative cross-file edits from real compiler reference spans."""
    root = Path(root).resolve()
    if not isinstance(new_name, str) or not _NAME.fullmatch(new_name) or new_name in _RESERVED:
        raise RenamePlanError("New symbol name must be a non-keyword PYNIX identifier")
    payload = query_navigation(root, compiler_python, "references", source, line, column)
    if payload.get("error"):
        raise RenamePlanError(str(payload["error"]))
    if payload.get("protocol") != "pynix-tooling" or payload.get("kind") != "references" or payload.get("version") != 1:
        raise RenamePlanError("Invalid compiler reference protocol")
    definition = payload.get("definition")
    references = payload.get("references")
    if not isinstance(definition, dict) or not isinstance(references, list):
        raise RenamePlanError("No resolved symbol at cursor")
    old_name = definition.get("name")
    if not isinstance(old_name, str) or not _NAME.fullmatch(old_name):
        raise RenamePlanError("Unrecognized compiler symbol")
    if old_name == new_name:
        raise RenamePlanError("Name is unchanged")
    originals: dict[str, str] = {}
    edits: dict[str, set[int]] = defaultdict(set)

    # Declaration offsets may point at "function" / "public", not the
    # identifier. Locate the declared name within the compiler-reported line.
    def_relative, definition_text = _read_source(root, definition.get("source"), originals)
    span = definition.get("start")
    if not isinstance(span, dict) or type(span.get("line")) is not int:
        raise RenamePlanError("Missing compiler declaration position")
    declaration_line = span["line"]
    lines = definition_text.splitlines(keepends=True)
    if not 1 <= declaration_line <= len(lines):
        raise RenamePlanError("Compiler declaration line is invalid")
    prefix = sum(len(entry) for entry in lines[:declaration_line - 1])
    candidate = lines[declaration_line - 1]
    matcher = re.search(r"\b(?:function|class|interface|enum|type|const|let|var)\s+"
                        + re.escape(old_name) + r"\b", candidate)
    if not matcher:
        raise RenamePlanError("Cannot locate compiler declaration name safely")
    position = prefix + matcher.end() - len(old_name)
    edits[def_relative].add(position)

    if len(references) > 3000:
        raise RenamePlanError("Too many references for safe interactive rename")
    for item in references:
        if not isinstance(item, dict):
            raise RenamePlanError("Invalid compiler reference")
        relative, text = _read_source(root, item.get("source"), originals)
        start, end = item.get("start"), item.get("end")
        if not isinstance(start, dict) or not isinstance(end, dict):
            raise RenamePlanError("Invalid compiler reference span")
        first, last = start.get("offset"), end.get("offset")
        if type(first) is not int or type(last) is not int or not 0 <= first < last <= len(text):
            raise RenamePlanError("Compiler reference offset does not match file")
        token = text[first:last]
        # Qualified spans such as module.helper include the final identifier.
        if not token.endswith(old_name):
            raise RenamePlanError("Compiler reference text differs from target")
        pos = last - len(old_name)
        if (pos > 0 and re.match(r"[A-Za-z0-9_]", text[pos - 1])
                and text[pos - 1] != "."):
            raise RenamePlanError("Compiler reference does not end at token boundary")
        if last < len(text) and re.match(r"[A-Za-z0-9_]", text[last]):
            raise RenamePlanError("Compiler reference overlaps a longer identifier")
        edits[relative].add(pos)

    files = []
    for relative in sorted(edits):
        before = originals[relative]
        indexes = sorted(edits[relative])
        if not indexes or any(before[pos:pos + len(old_name)] != old_name for pos in indexes):
            raise RenamePlanError("Compiler reference no longer matches saved file")
        after = before
        for pos in reversed(indexes):
            after = after[:pos] + new_name + after[pos + len(old_name):]
        if after != before:
            files.append({"source": relative, "before": before, "after": after,
                          "occurrences": len(indexes)})
    if not files:
        raise RenamePlanError("No safe symbol edits found")
    return {"symbol": old_name, "newName": new_name, "files": files,
            "occurrences": sum(item["occurrences"] for item in files)}

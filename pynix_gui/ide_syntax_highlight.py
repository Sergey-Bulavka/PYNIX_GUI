"""Small deterministic PYNIX source highlighter for the read-only IDE preview.

Presentation only: this is not a compiler parser or semantic analyzer.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

_TOKEN = re.compile(r'(?P<comment>\#.*|//.*)|(?P<string>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(?P<number>\b\d+(?:\.\d+)?\b)|(?P<word>\b[A-Za-z_][A-Za-z_0-9]*\b)')
_KEYWORDS = frozenset({
    "function", "module", "import", "from", "as", "let", "var", "const",
    "if", "else", "elif", "while", "for", "in", "return", "break",
    "continue", "true", "false", "none", "null", "and", "or", "not",
    "class", "interface", "type", "enum", "match", "case", "try",
    "catch", "finally", "raise", "public", "private", "async", "await",
})


@dataclass(frozen=True)
class Token:
    kind: str
    text: str


def highlight_line(source: str) -> tuple[Token, ...]:
    """Tokenize one display line, preserving every source character."""
    result: list[Token] = []
    end = 0
    for match in _TOKEN.finditer(source):
        if match.start() > end:
            result.append(Token("plain", source[end:match.start()]))
        kind = match.lastgroup or "plain"
        value = match.group()
        if kind == "word":
            kind = "keyword" if value in _KEYWORDS else "plain"
        result.append(Token(kind, value))
        end = match.end()
    if end < len(source):
        result.append(Token("plain", source[end:]))
    return tuple(result)


def highlight_document(source: str) -> list[list[dict[str, str]]]:
    return [[{"kind": part.kind, "text": part.text}
             for part in highlight_line(line)] for line in source.split("\n")]

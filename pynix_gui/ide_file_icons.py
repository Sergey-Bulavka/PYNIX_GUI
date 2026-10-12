"""File type icon registry for PYNIX IDE V4.

Mapping is centralized so Explorer and editor tabs identify files consistently.
"""
from pathlib import PurePath

ICON_BY_EXTENSION = {
    ".pnx": "pynix",
    ".py": "python",
    ".pyi": "python",
    ".md": "markdown",
    ".markdown": "markdown",
    ".json": "json",
    ".jsonc": "json",
    ".toml": "settings",
    ".yaml": "settings",
    ".yml": "settings",
    ".xml": "code",
    ".html": "code",
    ".css": "code",
    ".js": "code",
    ".ts": "code",
    ".sh": "terminal",
    ".bash": "terminal",
    ".zsh": "terminal",
    ".txt": "text",
    ".svg": "image",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
}
SPECIAL_NAMES = {
    "dockerfile": "settings",
    "makefile": "settings",
    ".gitignore": "git",
    ".gitattributes": "git",
    "license": "text",
}
ICON_TINT = {
    "pynix": "#79BCF7", "python": "#F2C35A", "markdown": "#76ADFA",
    "json": "#D7B1F3", "settings": "#BDA8F0", "code": "#91C5F6",
    "terminal": "#9CDBB4", "text": "#ABBCD1", "image": "#E6AF8A",
    "git": "#ED9C73", "file": "#B2C1D2",
}


def file_icon_type(path: str) -> str:
    name = PurePath(path).name.lower()
    if name in SPECIAL_NAMES:
        return SPECIAL_NAMES[name]
    return ICON_BY_EXTENSION.get(PurePath(name).suffix, "file")

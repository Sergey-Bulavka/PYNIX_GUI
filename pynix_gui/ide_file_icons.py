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
    ".csv": "text",
    ".sql": "code",
    ".properties": "settings",
    ".gradle": "settings",
    ".java": "code",
    ".jsp": "code",
    ".jspf": "code",
    ".toml": "settings",
    ".yaml": "settings",
    ".yml": "settings",
    ".xml": "code",
    ".html": "code",
    ".htm": "code",
    ".css": "code",
    ".js": "code",
    ".mjs": "code",
    ".cjs": "code",
    ".jsx": "code",
    ".ts": "code",
    ".tsx": "code",
    ".sh": "terminal",
    ".bash": "terminal",
    ".zsh": "terminal",
    ".txt": "text",
    ".svg": "image",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".gif": "image",
    ".bmp": "image",
    ".zip": "archive",
    ".jar": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".woff": "font",
    ".woff2": "font",
    ".ttf": "font",
    ".otf": "font",
}
SPECIAL_NAMES = {
    "dockerfile": "settings",
    "makefile": "settings",
    ".editorconfig": "settings",
    ".dockerignore": "settings",
    ".gitignore": "git",
    ".gitattributes": "git",
    "license": "text",
}
ICON_TINT = {
    "pynix": "#79BCF7", "python": "#F2C35A", "markdown": "#76ADFA",
    "json": "#D7B1F3", "settings": "#BDA8F0", "code": "#91C5F6",
    "terminal": "#9CDBB4", "text": "#ABBCD1", "image": "#E6AF8A",
    "git": "#ED9C73", "file": "#B2C1D2",
    "archive": "#C7B5E7", "font": "#B8CFDE",
}


def file_icon_type(path: str) -> str:
    name = PurePath(path).name.lower()
    if name in SPECIAL_NAMES:
        return SPECIAL_NAMES[name]
    return ICON_BY_EXTENSION.get(PurePath(name).suffix, "file")

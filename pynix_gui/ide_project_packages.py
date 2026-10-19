# Copyright 2026 Sergii V. Bulavka
# SPDX-License-Identifier: Apache-2.0
"""Package manager for the current project's Python virtual environment.

All calls run off the WKWebView main thread. pip arguments are arrays, never
shell commands; package names/versions are validated before subprocesses start.
Only this project's .venv is supported: system Python is never modified.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")
VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+!-]{0,99}$")


class PackageError(Exception):
    """A package operation could not be completed."""


class ProjectPackages:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.python = self.root / ".venv" / "bin" / "python"

    def interpreter(self) -> Path:
        if not self.python.is_file():
            raise PackageError("No project .venv/bin/python found. Create a virtual environment first.")
        return self.python

    @staticmethod
    def name(value: object) -> str:
        if not isinstance(value, str) or not NAME.fullmatch(value):
            raise PackageError("Invalid package name")
        return value

    @staticmethod
    def version(value: object) -> str:
        if not isinstance(value, str) or not VERSION.fullmatch(value):
            raise PackageError("Invalid package version")
        return value

    def pip(self, args: list[str], *, timeout: int = 150) -> str:
        python = self.interpreter()
        try:
            completed = subprocess.run(
                [str(python), "-m", "pip", *args],
                cwd=self.root, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PackageError(f"Package command failed: {exc}") from exc
        output = (completed.stdout + "\n" + completed.stderr).strip()[-10000:]
        if completed.returncode != 0:
            raise PackageError(output or f"pip exited with code {completed.returncode}")
        # JSON is emitted only to stdout. A harmless pip warning on stderr
        # must never break the Installed Packages panel.
        if args == ["list", "--format=json"]:
            return completed.stdout
        return output

    def list_installed(self) -> dict:
        raw = self.pip(["list", "--format=json"], timeout=30)
        try:
            packages = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise PackageError("Unable to parse pip list") from exc
        if not isinstance(packages, list):
            raise PackageError("Unexpected pip response")
        return {
            "interpreter": str(self.interpreter()),
            "packages": sorted(
                [{"name": str(item["name"]), "version": str(item["version"])}
                 for item in packages if isinstance(item, dict)
                 and isinstance(item.get("name"), str)
                 and isinstance(item.get("version"), str)],
                key=lambda item: item["name"].lower(),
            ),
        }

    def details(self, name: str) -> dict:
        name = self.name(name)
        # PyPI offers an official, exact-name JSON API, not fuzzy search.
        url = "https://pypi.org/pypi/" + urllib.parse.quote(name) + "/json"
        request = urllib.request.Request(
            url, headers={"User-Agent": "PYNIX-IDE/1.0 (package metadata)"})
        try:
            with urllib.request.urlopen(request, timeout=7) as response:
                if response.status != 200:
                    raise PackageError(f"PyPI returned HTTP {response.status}")
                raw = response.read(512_000 + 1)
                if len(raw) > 512_000:
                    raise PackageError("PyPI metadata is too large")
                data = json.loads(raw)
        except (urllib.error.URLError, ValueError, OSError) as exc:
            raise PackageError(f"PyPI metadata unavailable: {exc}") from exc
        info = data.get("info") or {}
        releases = data.get("releases") or {}
        if not isinstance(info, dict) or not isinstance(releases, dict):
            raise PackageError("Invalid PyPI metadata")
        versions = [v for v in releases if isinstance(v, str) and VERSION.fullmatch(v)
                    and isinstance(releases[v], list) and releases[v]]
        # Latest is listed first; older versions remain selectable.
        versions.sort(key=lambda v: (v != str(info.get("version", "")), v), reverse=False)
        project_urls = info.get("project_urls") or {}
        homepage = (project_urls.get("Homepage") or info.get("home_page") or
                    info.get("project_url") or "")
        if not isinstance(homepage, str) or not homepage.startswith("https://"):
            homepage = "https://pypi.org/project/" + urllib.parse.quote(name) + "/"
        return {
            "name": str(info.get("name") or name),
            "version": str(info.get("version") or ""),
            "summary": str(info.get("summary") or "")[:2000],
            "description": str(info.get("description") or "")[:9000],
            "homepage": homepage[:1000],
            "versions": versions[:80],
        }

    def change(self, action: str, name: str, version: str | None = None) -> dict:
        name = self.name(name)
        if action == "install":
            spec = name + ("==" + self.version(version) if version else "")
            output = self.pip(["install", "--disable-pip-version-check", spec])
        elif action == "upgrade":
            output = self.pip(["install", "--disable-pip-version-check", "--upgrade", name])
        elif action == "uninstall":
            output = self.pip(["uninstall", "-y", name])
        else:
            raise PackageError("Unsupported package action")
        return {"name": name, "action": action, "output": output}

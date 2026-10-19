# Copyright 2026 PYNIX contributors
# SPDX-License-Identifier: Apache-2.0
"""Project Services: configured MCP SSE connections and observable sessions.

Native networking is kept out of WKWebView. A connection does not invoke any
remote tools: only initialize and tools/list are sent over the MCP transport.
Profiles are project-scoped in the user's config dir, never in source control.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import deque
from pathlib import Path


class ServicesError(ValueError):
    pass


def _endpoint(url: str) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise ServicesError("Invalid MCP SSE URL")
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
        raise ServicesError("Use an HTTP(S) MCP SSE URL without embedded credentials")
    if parts.fragment:
        raise ServicesError("Fragments are not supported in MCP SSE URLs")
    if parts.scheme == "http" and parts.hostname.lower() not in ("localhost", "127.0.0.1", "::1"):
        raise ServicesError("Remote MCP SSE connections require HTTPS")
    try:
        if parts.port is not None and parts.port < 1:
            raise ServicesError("Invalid port")
    except ValueError as exc:
        raise ServicesError("Invalid port") from exc
    return url


def _name(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 80:
        raise ServicesError("Service name must contain 1–80 characters")
    if any(ord(ch) < 32 for ch in value):
        raise ServicesError("Control characters are not allowed in service names")
    return value.strip()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ServicesError("MCP SSE redirects require an explicit endpoint URL")


class ProjectServices:
    """A bounded registry for manually configured, unauthenticated MCP SSE."""

    def __init__(self, root: Path, config_dir: Path | None = None):
        self.root = Path(root).resolve()
        base = config_dir or (Path.home() / ".config" / "pynix" / "ide-services")
        digest = hashlib.sha256(os.fsencode(self.root)).hexdigest()[:24]
        self.path = Path(base) / f"{digest}.json"
        self._lock = threading.RLock()
        self._connections: dict[str, dict] = {}
        self._profiles = self._read()
        self._opener = urllib.request.build_opener(_NoRedirect())

    def _read(self) -> list[dict]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError, OSError):
            return []
        if not isinstance(data, list):
            return []
        profiles = []
        for item in data[:40]:
            if not isinstance(item, dict):
                continue
            try:
                id_ = str(uuid.UUID(str(item["id"])))
                profiles.append({"id": id_, "name": _name(item["name"]),
                                 "url": _endpoint(item["url"]), "type": "mcp-sse"})
            except (KeyError, TypeError, ValueError):
                continue
        return profiles

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.parent.chmod(0o700)
        tmp = self.path.with_name(self.path.name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as out:
                json.dump(self._profiles, out, ensure_ascii=False, indent=2)
            tmp.chmod(0o600)
            tmp.replace(self.path)
        finally:
            tmp.unlink(missing_ok=True)

    def list(self) -> dict:
        with self._lock:
            services = []
            for profile in self._profiles:
                runtime = self._connections.get(profile["id"]) or {}
                services.append({
                    **profile,
                    "state": runtime.get("state", "disconnected"),
                    "since": runtime.get("since"),
                    "client": "PYNIX IDE",
                    "transport": "SSE",
                    "tools": list(runtime.get("tools", [])),
                    "events": list(runtime.get("events", []))[-100:],
                    "error": runtime.get("error", ""),
                })
            return {"services": services}

    def add(self, name: str, url: str) -> dict:
        profile = {"id": str(uuid.uuid4()), "type": "mcp-sse",
                   "name": _name(name), "url": _endpoint(url)}
        with self._lock:
            if len(self._profiles) >= 40:
                raise ServicesError("Maximum of 40 service profiles")
            if any(p["name"].casefold() == profile["name"].casefold()
                   for p in self._profiles):
                raise ServicesError("A service with this name already exists")
            self._profiles.append(profile)
            self._save()
        return profile

    def remove(self, id_: str):
        self.disconnect(id_)
        with self._lock:
            if not any(p["id"] == id_ for p in self._profiles):
                raise ServicesError("Service not found")
            self._profiles = [p for p in self._profiles if p["id"] != id_]
            self._connections.pop(id_, None)
            self._save()

    def _record(self, id_: str, kind: str, detail: str):
        with self._lock:
            info = self._connections.get(id_)
            if info is not None:
                info["events"].append({"time": time.time(), "type": kind,
                                       "detail": str(detail)[:1000]})

    def connect(self, id_: str):
        with self._lock:
            profile = next((p for p in self._profiles if p["id"] == id_), None)
            if profile is None:
                raise ServicesError("Service not found")
            old = self._connections.get(id_)
            if old and old["state"] in ("connecting", "connected"):
                raise ServicesError("Service is already connecting or connected")
            state = {"state": "connecting", "since": time.time(), "error": "",
                     "tools": [], "events": deque(maxlen=100),
                     "stop": threading.Event(), "response": None}
            self._connections[id_] = state
        thread = threading.Thread(target=self._listen, args=(id_, dict(profile), state),
                                  daemon=True, name="pynix-mcp-sse")
        thread.start()

    def disconnect(self, id_: str):
        with self._lock:
            info = self._connections.get(id_)
            if not info:
                return
            info["stop"].set()
            info["state"] = "disconnected"
            response = info.get("response")
        if response:
            try:
                response.close()
            except OSError:
                pass

    def close(self):
        with self._lock:
            ids = list(self._connections)
        for id_ in ids:
            self.disconnect(id_)

    def _send(self, id_: str, url: str, payload: dict):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        try:
            with self._opener.open(request, timeout=8) as response:
                # For SSE transport, the reply is normally on the GET stream.
                response.read(8192)
        except (OSError, urllib.error.URLError) as exc:
            raise ServicesError(f"Cannot send MCP request: {exc}") from exc
        self._record(id_, "request", payload.get("method", "notification"))

    def _listen(self, id_: str, profile: dict, runtime: dict):
        stopped = runtime["stop"]
        try:
            request = urllib.request.Request(
                profile["url"], headers={"Accept": "text/event-stream",
                                          "Cache-Control": "no-cache"})
            with self._opener.open(request, timeout=3600) as response:
                with self._lock:
                    if stopped.is_set():
                        return
                    runtime["response"] = response
                    content_type = response.headers.get("Content-Type", "")
                    if "text/event-stream" not in content_type:
                        raise ServicesError("Server did not return text/event-stream")
                    runtime["state"] = "connected"
                self._record(id_, "connection", "SSE stream connected")
                endpoint = None
                event = "message"
                data_lines = []
                while not stopped.is_set():
                    line = response.readline(65537)
                    if not line:
                        break
                    if len(line) > 65536:
                        raise ServicesError("SSE event line is too large")
                    decoded = line.decode("utf-8", "replace").rstrip("\r\n")
                    if decoded.startswith("event:"):
                        event = decoded[6:].strip()
                    elif decoded.startswith("data:"):
                        data_lines.append(decoded[5:].lstrip())
                        if sum(map(len, data_lines)) > 65536:
                            raise ServicesError("SSE message is too large")
                    elif not decoded:
                        data = "\n".join(data_lines)
                        if event == "endpoint" and data:
                            candidate = urllib.parse.urljoin(profile["url"], data)
                            base = urllib.parse.urlsplit(profile["url"])
                            target = urllib.parse.urlsplit(candidate)
                            if (target.scheme, target.netloc) != (base.scheme, base.netloc):
                                raise ServicesError("MCP SSE endpoint must use the same origin")
                            endpoint = candidate
                            self._record(id_, "endpoint", "Received MCP POST endpoint")
                            self._send(id_, endpoint, {
                                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2024-11-05",
                                           "capabilities": {},
                                           "clientInfo": {"name": "PYNIX IDE", "version": "0.1.0"}}})
                        elif event == "message" and data:
                            try:
                                msg = json.loads(data)
                            except ValueError:
                                self._record(id_, "message", "Unparseable SSE message")
                            else:
                                if isinstance(msg, dict):
                                    if msg.get("id") == 1 and "result" in msg and endpoint:
                                        self._record(id_, "response", "initialize completed")
                                        self._send(id_, endpoint, {
                                            "jsonrpc": "2.0",
                                            "method": "notifications/initialized"})
                                        self._send(id_, endpoint, {
                                            "jsonrpc": "2.0", "id": 2, "method": "tools/list",
                                            "params": {}})
                                    elif msg.get("id") == 2 and "result" in msg:
                                        result = msg.get("result") or {}
                                        tools = result.get("tools", []) if isinstance(result, dict) else []
                                        with self._lock:
                                            runtime["tools"] = [str(t.get("name"))[:120]
                                                for t in tools[:100] if isinstance(t, dict)
                                                and isinstance(t.get("name"), str)]
                                        self._record(id_, "response",
                                                     f"tools/list: {len(runtime['tools'])} tools")
                                    elif msg.get("error"):
                                        self._record(id_, "error",
                                                     str(msg["error"])[:300])
                        event = "message"
                        data_lines = []
                if not stopped.is_set():
                    raise ServicesError("SSE connection closed by the server")
        except Exception as exc:
            if not stopped.is_set():
                with self._lock:
                    runtime["state"] = "error"
                    runtime["error"] = str(exc)[:400]
                self._record(id_, "error", str(exc)[:400])
        finally:
            with self._lock:
                runtime["response"] = None
                if stopped.is_set():
                    runtime["state"] = "disconnected"

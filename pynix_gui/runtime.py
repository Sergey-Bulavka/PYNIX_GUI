# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Backend-neutral GUI window lifecycle and runtime boundary."""

from __future__ import annotations

from dataclasses import dataclass

from .core import GUIError, GUIEvent, GUIView, validate_view


@dataclass(slots=True)
class GUIRuntimeState:
    """Mutable runtime-owned state for the current GUI application context."""

    window: "GUIWindow | None" = None


class GUIWindow:
    """Managed wrapper around an opaque backend window handle."""

    __slots__ = ("_backend", "_handle", "_closed", "_runtime_state")

    def __init__(self, backend, handle, runtime_state: GUIRuntimeState | None = None):
        self._backend = backend
        self._handle = handle
        self._closed = False
        self._runtime_state = runtime_state

    @property
    def closed(self) -> bool:
        return self._closed

    def _require_open(self) -> None:
        if self._closed:
            raise GUIError("PYNIX-GUI-002", "GUI window is closed.")

    def render(self, view: GUIView) -> None:
        self._require_open()
        validate_view(view)

        try:
            self._backend.render(self._handle, view)
        except GUIError:
            raise
        except Exception as error:
            raise GUIError(
                "PYNIX-GUI-003",
                "GUI view rendering failed.",
            ) from error

    def next_event(self) -> GUIEvent:
        self._require_open()

        try:
            event = self._backend.next_event(self._handle)
        except GUIError:
            raise
        except Exception as error:
            raise GUIError(
                "PYNIX-GUI-004",
                "GUI event processing failed.",
            ) from error

        if isinstance(event, GUIEvent):
            return event

        raise GUIError(
            "PYNIX-GUI-004",
            "GUI backend produced an invalid logical event.",
        )

    def close(self) -> None:
        if self._closed:
            return

        try:
            self._backend.close(self._handle)
        except GUIError:
            raise
        except Exception as error:
            raise GUIError(
                "PYNIX-GUI-002",
                "GUI window closing failed.",
            ) from error

        self._closed = True

        if self._runtime_state is not None and self._runtime_state.window is self:
            self._runtime_state.window = None


class GUIRuntime:
    """Backend-neutral GUI runtime facade used by language adapters."""

    __slots__ = ("backend", "state")

    def __init__(self, backend, state: GUIRuntimeState | None = None):
        self.backend = backend
        self.state = state if state is not None else GUIRuntimeState()

    def is_available(self) -> bool:
        if self.backend is None:
            return False

        try:
            return self.backend.is_available() is True
        except Exception:
            return False

    def _require_available(self):
        if not self.is_available():
            raise GUIError(
                "PYNIX-GUI-001",
                "Required GUI capability is unavailable.",
            )
        return self.backend

    def open(self, title: str, width: int, height: int) -> GUIWindow:
        if type(title) is not str:
            raise GUIError(
                "PYNIX-GUI-002",
                "GUI window title must be String.",
            )

        if (
            type(width) is not int
            or type(height) is not int
            or width <= 0
            or height <= 0
        ):
            raise GUIError(
                "PYNIX-GUI-002",
                "GUI window dimensions must be positive Int values.",
            )

        backend = self._require_available()

        if self.state.window is not None:
            raise GUIError(
                "PYNIX-GUI-002",
                "Only one live GUI window is supported per runtime.",
            )

        try:
            handle = backend.open(title, width, height)
        except GUIError:
            raise
        except Exception as error:
            raise GUIError(
                "PYNIX-GUI-002",
                "GUI window creation failed.",
            ) from error

        if handle is None:
            raise GUIError(
                "PYNIX-GUI-002",
                "GUI window creation failed.",
            )

        window = GUIWindow(backend, handle, self.state)
        self.state.window = window
        return window

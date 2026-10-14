"""Explicit capability gate for the PYNIX interactive debugger.

The current compiler backend exposes execute()/Interpreter.run(), but not
a public pausable debugger protocol. Keep IDE controls honest and disabled
until a versioned runtime interface exists.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DebugCapabilities:
    protocol: str = "pynix-debug-capabilities"
    version: int = 1
    supported: bool = False
    breakpoints: bool = False
    pause: bool = False
    step_into: bool = False
    step_over: bool = False
    step_out: bool = False
    stack_frames: bool = False
    variables: bool = False
    reason: str = (
        "PYNIX compiler has no verified public pause/step/stack debugger "
        "protocol. Run/Check are available; interactive Debug is not."
    )

    def to_payload(self) -> dict:
        return asdict(self)


def current_debug_capabilities() -> dict:
    return DebugCapabilities().to_payload()

"""Cross-repository smoke check: native IDE client talking to the real PYNIX worker.

Run by the external debugger CI job with PYNIX compiler installed on PYTHONPATH.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

# Running a script by path does not add the repository root to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pynix_gui.ide_debug_process_client import DebugProcessClient


def test_real_debugger():
    with TemporaryDirectory(prefix="pynix-debug-smoke-") as directory:
        root = Path(directory)
        (root / "main.pnx").write_text(
            "function main()\n"
            "    first = 3\n"
            "    second = first + 4\n"
            "    print(second)\n",
            encoding="utf-8",
        )
        client = DebugProcessClient(root, Path(sys.executable))
        try:
            launched = client.launch("main.pnx")
            assert launched["event"] == "started", launched
            assert launched["state"] == "paused", launched
            initial_status = client.command("status")
            assert initial_status["state"] == "paused", initial_status
            assert initial_status.get("location"), initial_status
            bp = client.set_breakpoints([{"source": "main.pnx", "line": 4}])
            assert bp["breakpoints"] == 1, bp
            continued = client.command("continue")
            assert continued["state"] == "paused", continued
            position = continued.get("location")
            assert position is not None and position["line"] == 4, continued
            stack = client.command("stack")
            assert stack["state"] == "paused", stack
            assert isinstance(stack.get("frames"), list), stack
            variables = client.command("variables")
            assert isinstance(variables.get("variables"), list), variables
            client.set_breakpoints([])
            completed = client.command("stepInto")
            assert completed["state"] == "finished", completed
            assert completed.get("output") == "7", completed
            assert client._worker is None
        finally:
            client.close()


if __name__ == "__main__":
    test_real_debugger()
    print("Real PYNIX debugger IDE bridge smoke passed")

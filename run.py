"""Development entrypoint.

Run with:  python run.py
Then open  http://127.0.0.1:8000 (or the next free port if 8000 is busy).
"""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

# Allow `python run.py` without an editable install by exposing the src layout.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import uvicorn


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Return True when the given TCP port is free on the provided host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
        return True


def resolve_port(requested_port: int | None = None, host: str = "127.0.0.1") -> int:
    """Return the requested port if free, otherwise the next available port."""
    requested = requested_port if requested_port is not None else int(os.getenv("PORT", "8000"))
    if requested < 1:
        raise ValueError("Port must be a positive integer")

    for port in [requested, *range(requested + 1, requested + 11)]:
        if is_port_available(port, host=host):
            return port

    raise RuntimeError(f"No free port found in range {requested}-{requested + 10}")


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = resolve_port(host=host)
    uvicorn.run(
        "stadium_assistant.app:app",
        host=host,
        port=port,
        reload=bool(os.getenv("RELOAD", "")),
    )

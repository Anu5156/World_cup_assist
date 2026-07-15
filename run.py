"""Development entrypoint.

Run with:  python run.py
Then open  http://127.0.0.1:8000
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow `python run.py` without an editable install by exposing the src layout.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "stadium_assistant.app:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=bool(os.getenv("RELOAD", "")),
    )

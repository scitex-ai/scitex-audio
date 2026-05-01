"""Smoke tests: every example script must run to completion."""

import subprocess
import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
QUICKSTART = EXAMPLES_DIR / "quickstart.py"


def test_quickstart_smoke(tmp_path):
    """Quickstart example must import and introspect cleanly (offline-safe)."""
    assert QUICKSTART.exists(), f"missing example: {QUICKSTART}"
    result = subprocess.run(
        [sys.executable, str(QUICKSTART)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"{QUICKSTART.name} failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

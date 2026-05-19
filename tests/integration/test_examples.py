"""Smoke tests: every example script must run to completion."""

import subprocess
import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
QUICKSTART = EXAMPLES_DIR / "quickstart.py"


def test_quickstart_smoke_quickstart_exists(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert QUICKSTART.exists(), f"missing example: {QUICKSTART}"


def test_quickstart_smoke_result_returncode_equals_n_0(tmp_path):
    # Arrange
    # Act
    # Arrange
    # Act
    # Arrange
    # Act
    result = subprocess.run(
        [sys.executable, str(QUICKSTART)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
    )
    # Act
    # Assert
    assert result.returncode == 0, (
        f"{QUICKSTART.name} failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )



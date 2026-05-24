#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: /home/ywatanabe/proj/scitex-audio/tests/examples/test_01_speak_basic.py

"""Smoke test for examples/01_speak_basic.py.

Per scitex-dev audit-project PS303: every example must have a matching
test under tests/examples/. Validates the example parses cleanly without
exercising audio hardware (which the CI environment lacks).
"""

import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "01_speak_basic.py"


def test_example_exists_example_exists():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert EXAMPLE.exists(), f"missing example: {EXAMPLE}"


def test_compiles_r_returncode_equals_n_0():
    # Arrange
    # Act
    # Arrange
    # Act
    # Arrange
    # Act
    _r = subprocess.run(
        [sys.executable, "-m", "py_compile", str(EXAMPLE)],
        check=True,
    )
    # Assert
    assert _r.returncode == 0

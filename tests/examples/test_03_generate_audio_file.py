#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: /home/ywatanabe/proj/scitex-audio/tests/examples/test_03_generate_audio_file.py

"""Smoke test for examples/03_generate_audio_file.py.

Per scitex-dev audit-project PS303: every example must have a matching
test under tests/examples/. Validates the example parses cleanly without
exercising network-dependent TTS backends (which the CI environment lacks).
"""

import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "03_generate_audio_file.py"


def test_example_exists():
    assert EXAMPLE.exists(), f"missing example: {EXAMPLE}"


def test_compiles():
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(EXAMPLE)],
        check=True,
    )

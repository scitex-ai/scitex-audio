"""Isolation for e2e tests: redirect user-state to tmp, blank API keys.

A deleted key var gets repopulated from the real `.env` via dotenv, so
keys are set to a blank `" "` instead of removed. No `monkeypatch` —
explicit save/restore (PA-306).
"""

from __future__ import annotations

import os

import pytest

_ISOLATED_VARS = (
    "SCITEX_DIR",
    "SCITEX_AUDIO_ELEVENLABS_API_KEY",
    "ELEVENLABS_API_KEY",
)


@pytest.fixture(autouse=True)
def _scitex_audio_e2e_isolation(tmp_path):
    previous = {name: os.environ.get(name) for name in _ISOLATED_VARS}
    os.environ["SCITEX_DIR"] = str(tmp_path / ".scitex")
    os.environ["SCITEX_AUDIO_ELEVENLABS_API_KEY"] = " "
    os.environ["ELEVENLABS_API_KEY"] = " "
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

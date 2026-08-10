#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the STT backend-selection layer in scitex_audio._stt.

No mocks: backend choice is driven through the real precedence inputs
(explicit argument, environment variable, on-disk discovery).
"""

import os

import pytest

from scitex_audio import _stt


@pytest.fixture
def env_save_restore():
    """Snapshot the STT backend env var; restore on teardown."""
    saved = os.environ.get(_stt.BACKEND_ENV_VAR)
    try:
        yield
    finally:
        if saved is None:
            os.environ.pop(_stt.BACKEND_ENV_VAR, None)
        else:
            os.environ[_stt.BACKEND_ENV_VAR] = saved


class TestResolveBackend:
    def test_explicit_argument_wins_over_env(self, env_save_restore):
        # Arrange
        os.environ[_stt.BACKEND_ENV_VAR] = _stt.BACKEND_WHISPER_CPP
        # Act
        chosen = _stt.resolve_backend(_stt.BACKEND_FASTER_WHISPER)
        # Assert
        assert chosen == _stt.BACKEND_FASTER_WHISPER

    def test_env_used_when_no_explicit_argument(self, env_save_restore):
        # Arrange
        os.environ[_stt.BACKEND_ENV_VAR] = _stt.BACKEND_FASTER_WHISPER
        # Act
        chosen = _stt.resolve_backend()
        # Assert
        assert chosen == _stt.BACKEND_FASTER_WHISPER

    def test_auto_keyword_falls_through_to_detection(self, env_save_restore):
        # Arrange
        os.environ.pop(_stt.BACKEND_ENV_VAR, None)
        # Act
        chosen = _stt.resolve_backend("auto")
        # Assert
        assert chosen in _stt.BACKENDS

    def test_autodetect_returns_a_known_backend(self, env_save_restore):
        # Arrange
        os.environ.pop(_stt.BACKEND_ENV_VAR, None)
        # Act
        chosen = _stt.resolve_backend()
        # Assert
        assert chosen in _stt.BACKENDS

    def test_unknown_explicit_backend_is_returned_verbatim(self, env_save_restore):
        # Arrange
        os.environ.pop(_stt.BACKEND_ENV_VAR, None)
        # Act
        chosen = _stt.resolve_backend("bogus-engine")
        # Assert
        assert chosen == "bogus-engine"


class TestTranscribeDispatch:
    def test_unknown_backend_fails_rather_than_guessing(self, env_save_restore):
        # Arrange
        os.environ.pop(_stt.BACKEND_ENV_VAR, None)
        # Act
        result = _stt.transcribe("/nonexistent.wav", backend="bogus-engine")
        # Assert
        assert result["success"] is False

    def test_unknown_backend_error_names_the_backend(self, env_save_restore):
        # Arrange
        os.environ.pop(_stt.BACKEND_ENV_VAR, None)
        # Act
        result = _stt.transcribe("/nonexistent.wav", backend="bogus-engine")
        # Assert
        assert "bogus-engine" in result["error"]

    def test_unknown_backend_error_lists_the_valid_choices(self, env_save_restore):
        # Arrange
        os.environ.pop(_stt.BACKEND_ENV_VAR, None)
        # Act
        result = _stt.transcribe("/nonexistent.wav", backend="bogus-engine")
        # Assert
        assert all(name in result["error"] for name in _stt.BACKENDS)

    def test_faster_whisper_dispatch_reaches_that_backend(self, env_save_restore):
        # Arrange — a path that cannot exist, so we see the backend's own
        # not-found error rather than whisper.cpp's binary-missing error.
        os.environ.pop(_stt.BACKEND_ENV_VAR, None)
        # Act
        result = _stt.transcribe(
            "/nonexistent-audio-file.wav", backend=_stt.BACKEND_FASTER_WHISPER
        )
        # Assert
        assert "whisper-cli" not in result.get("error", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF

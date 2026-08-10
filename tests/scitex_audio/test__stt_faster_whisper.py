#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_audio._stt_faster_whisper.

No mocks: these exercise the real pure functions and the real "package is
absent" path. The faster-whisper package itself is optional, so tests that
need it are skipped rather than faked.
"""

import os
import re

import pytest

from scitex_audio import _stt_faster_whisper as fw

# The shape _stt._parse_whisper_output produces for the whisper.cpp backend.
# Both backends cross the same published boundary (the MCP audio_transcribe
# tool returns segments as JSON), so the shapes must not drift apart.
WHISPER_CPP_TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")


@pytest.fixture
def existing_audio_file(tmp_path):
    """A real file on disk, so transcribe() gets past its existence check."""
    path = tmp_path / "probe.wav"
    path.write_bytes(b"RIFF")
    return str(path)


@pytest.fixture
def env_save_restore():
    """Snapshot the faster-whisper env vars; restore on teardown."""
    keys = (
        fw.MODEL_ENV_VAR,
        fw.DEVICE_ENV_VAR,
        fw.COMPUTE_TYPE_ENV_VAR,
    )
    saved = {k: os.environ.get(k) for k in keys}
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TestFormatTimestamp:
    def test_zero_renders_as_padded_origin(self):
        # Arrange
        seconds = 0.0
        # Act
        rendered = fw.format_timestamp(seconds)
        # Assert
        assert rendered == "00:00:00.000"

    def test_subsecond_keeps_milliseconds(self):
        # Arrange
        seconds = 1.234
        # Act
        rendered = fw.format_timestamp(seconds)
        # Assert
        assert rendered == "00:00:01.234"

    def test_minute_boundary_carries_correctly(self):
        # Arrange
        seconds = 61.0
        # Act
        rendered = fw.format_timestamp(seconds)
        # Assert
        assert rendered == "00:01:01.000"

    def test_hour_boundary_carries_correctly(self):
        # Arrange
        seconds = 3661.5
        # Act
        rendered = fw.format_timestamp(seconds)
        # Assert
        assert rendered == "01:01:01.500"

    def test_negative_input_clamps_to_origin(self):
        # Arrange
        seconds = -1.0
        # Act
        rendered = fw.format_timestamp(seconds)
        # Assert
        assert rendered == "00:00:00.000"

    @pytest.mark.parametrize(
        "seconds", [0, 0.5, 1.234, 61.0, 3661.5, 39599.999]
    )
    def test_matches_whisper_cpp_timestamp_shape(self, seconds):
        # Arrange
        # Act
        rendered = fw.format_timestamp(seconds)
        # Assert
        assert WHISPER_CPP_TIMESTAMP.match(rendered)


class TestResolveDevice:
    def test_explicit_device_wins(self, env_save_restore):
        # Arrange
        os.environ[fw.DEVICE_ENV_VAR] = "cpu"
        # Act
        device = fw.resolve_device("cuda")
        # Assert
        assert device == "cuda"

    def test_env_used_when_no_explicit_device(self, env_save_restore):
        # Arrange
        os.environ[fw.DEVICE_ENV_VAR] = "cuda"
        # Act
        device = fw.resolve_device()
        # Assert
        assert device == "cuda"

    def test_autodetect_returns_a_known_device(self, env_save_restore):
        # Arrange
        os.environ.pop(fw.DEVICE_ENV_VAR, None)
        # Act
        device = fw.resolve_device()
        # Assert
        assert device in ("cuda", "cpu")


class TestTranscribeFailurePaths:
    def test_missing_audio_file_reports_failure(self, tmp_path):
        # Arrange
        missing = str(tmp_path / "definitely-absent.wav")
        # Act
        result = fw.transcribe(missing)
        # Assert
        assert result["success"] is False

    def test_missing_audio_file_names_the_path(self, tmp_path):
        # Arrange
        missing = str(tmp_path / "definitely-absent.wav")
        # Act
        result = fw.transcribe(missing)
        # Assert
        assert "definitely-absent.wav" in result["error"]

    @pytest.mark.skipif(
        fw.available(),
        reason="faster-whisper is installed; the absent-package path cannot run",
    )
    def test_absent_package_explains_how_to_install(self, existing_audio_file):
        # Arrange
        # Act
        result = fw.transcribe(existing_audio_file)
        # Assert
        assert "pip install" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF

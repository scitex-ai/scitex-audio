"""Real filesystem checks for explicit STT binary/model configuration."""

import os
import sys

import pytest

from scitex_audio._stt import find_whisper_cli, find_whisper_model


@pytest.fixture(autouse=True)
def restore_stt_environment():
    keys = ("SCITEX_AUDIO_WHISPER_CLI", "SCITEX_AUDIO_WHISPER_MODEL")
    previous = {key: os.environ.get(key) for key in keys}
    yield
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_non_executable_cli_override_is_rejected(tmp_path):
    # Arrange
    path = tmp_path / "not-executable"
    path.write_text("owned filesystem fixture; never executed")
    path.chmod(0o600)
    os.environ["SCITEX_AUDIO_WHISPER_CLI"] = str(path)
    # Act
    found = find_whisper_cli()
    # Assert
    assert found is None


def test_missing_cli_override_does_not_silently_select_another_binary(tmp_path):
    # Arrange
    os.environ["SCITEX_AUDIO_WHISPER_CLI"] = str(tmp_path / "missing")
    # Act
    found = find_whisper_cli()
    # Assert
    assert found is None


def test_executable_file_override_is_honored_without_execution():
    # Arrange
    os.environ["SCITEX_AUDIO_WHISPER_CLI"] = sys.executable
    # Act
    found = find_whisper_cli()
    # Assert
    assert found == sys.executable


def test_model_override_is_a_file_path_not_a_model_name(tmp_path):
    # Arrange
    path = tmp_path / "owned-model-path.bin"
    path.write_bytes(b"")  # Discovery fixture only, not usable recognition weights.
    os.environ["SCITEX_AUDIO_WHISPER_MODEL"] = str(path)
    # Act
    found = find_whisper_model("tiny")
    # Assert
    assert found == str(path)


def test_missing_model_override_is_reported_missing(tmp_path):
    # Arrange
    os.environ["SCITEX_AUDIO_WHISPER_MODEL"] = str(tmp_path / "missing.bin")
    # Act
    found = find_whisper_model()
    # Assert
    assert found is None

#!/usr/bin/env python3
"""Tests for scitex_audio._cli._commands._stt."""

import click
import pytest

from scitex_audio._cli._commands._stt import register


class TestRegister:
    def test_register_attaches_transcribe_audio(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "transcribe-audio" in group.commands




@pytest.fixture
def invalid_audio(tmp_path):
    """Owned invalid input fails before any recognition or external service."""
    path = tmp_path / "invalid.mp3"
    path.write_bytes(b"not an audio container")
    return str(path)


def _command_group():
    group = click.Group()
    register(group)
    return group


def test_json_transcription_failure_has_nonzero_exit(invalid_audio):
    # Arrange
    from click.testing import CliRunner

    group = _command_group()
    # Act
    result = CliRunner().invoke(group, ["transcribe-audio", invalid_audio, "--json"])
    # Assert
    assert result.exit_code == 1


def test_json_transcription_failure_keeps_machine_readable_payload(invalid_audio):
    # Arrange
    import json
    from click.testing import CliRunner

    group = _command_group()
    # Act
    result = CliRunner().invoke(group, ["transcribe-audio", invalid_audio, "--json"])
    payload = json.loads(result.stdout)
    # Assert
    assert payload["success"] is False


def test_text_transcription_failure_keeps_nonzero_exit(invalid_audio):
    # Arrange
    from click.testing import CliRunner

    group = _command_group()
    # Act
    result = CliRunner().invoke(group, ["transcribe-audio", invalid_audio])
    # Assert
    assert result.exit_code == 1


@pytest.mark.parametrize("expected", ["SCITEX_AUDIO_WHISPER_CLI", "SCITEX_AUDIO_WHISPER_MODEL", "skills get 01_installation"])
def test_transcription_help_explains_setup(expected):
    # Arrange
    from click.testing import CliRunner

    group = _command_group()
    # Act
    result = CliRunner().invoke(group, ["transcribe-audio", "--help"])
    # Assert
    assert expected in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF

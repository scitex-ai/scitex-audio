#!/usr/bin/env python3
"""Tests for scitex_audio._cli._main (Click root group + leaf commands).

No mocks: the CLI is exercised through the real ``CliRunner``. Commands that
would shell out to network/hardware (TTS synthesis, whisper transcription,
``pkill espeak``) are tested through their pure / dry-run / validation paths;
the speak-text option plumbing is verified directly via the pure
``build_speak_kwargs`` helper that the command delegates to.
"""

import pytest
from click.testing import CliRunner

from scitex_audio._cli._commands._speak import build_speak_kwargs
from scitex_audio._cli._main import audio


@pytest.fixture
def runner():
    return CliRunner()


class TestRootGroup:
    def test_help_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert result.exit_code == 0

    def test_help_mentions_text_to_speech(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "Text-to-speech" in result.output

    def test_help_mentions_config_yaml(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "config.yaml" in result.output

    def test_version_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--version"])
        # Assert
        assert result.exit_code == 0

    def test_version_names_scitex_audio(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--version"])
        # Assert
        assert "scitex-audio" in result.output

    def test_short_version_flag_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["-V"])
        # Assert
        assert result.exit_code == 0

    def test_no_args_shows_help(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Assert
        assert result.exit_code == 0

    def test_no_args_lists_speak(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Assert
        assert "speak" in result.output.lower()

    def test_help_recursive_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert result.exit_code == 0

    def test_help_recursive_lists_speak_text(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert "speak-text" in result.output

    def test_help_recursive_lists_list_backends(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert "list-backends" in result.output

    def test_root_json_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--json"])
        # Assert
        assert result.exit_code == 0

    def test_root_json_lists_a_subcommand(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--json"])
        # Assert
        assert "speak-text" in result.output or "list-backends" in result.output


class TestSpeakTextOptionPlumbing:
    """speak-text translates options into speak() kwargs via build_speak_kwargs."""

    def test_text_passes_through(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, None, None, False)
        # Assert
        assert kwargs["text"] == "Hello"

    def test_play_defaults_true(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, None, None, False)
        # Assert
        assert kwargs["play"] is True

    def test_fallback_defaults_true(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, None, None, False)
        # Assert
        assert kwargs["fallback"] is True

    def test_backend_option_sets_backend(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hi", "gtts", None, None, False, None, None, False)
        # Assert
        assert kwargs["backend"] == "gtts"

    def test_no_play_flag_sets_play_false(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hi", None, None, None, True, None, None, False)
        # Assert
        assert kwargs["play"] is False

    def test_no_fallback_flag_sets_fallback_false(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hi", None, None, None, False, None, None, True)
        # Assert
        assert kwargs["fallback"] is False

    def test_invalid_backend_rejected_by_cli(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "Hi", "-b", "invalid"])
        # Assert
        assert result.exit_code != 0


class TestListBackends:
    """list-backends runs against the real backend registry."""

    def test_text_output_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert result.exit_code == 0

    def test_text_output_shows_fallback_order(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert "Fallback order" in result.output

    def test_json_envelope_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends", "--json"])
        # Assert
        assert result.exit_code == 0

    def test_json_envelope_has_available_key(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends", "--json"])
        # Assert
        assert "available" in result.output

    def test_json_envelope_has_fallback_order_key(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends", "--json"])
        # Assert
        assert "fallback_order" in result.output


class TestCheckBackends:
    """check-backends runs against the real WSL/audio probe."""

    def test_text_output_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["check-backends"])
        # Assert
        assert result.exit_code == 0

    def test_text_output_has_status_header(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["check-backends"])
        # Assert
        assert "Audio Status Check" in result.output

    def test_json_output_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["check-backends", "--json"])
        # Assert
        assert result.exit_code == 0

    def test_json_output_has_is_wsl_key(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["check-backends", "--json"])
        # Assert
        assert "is_wsl" in result.output


class TestStopPlayback:
    def test_dry_run_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["stop-playback", "--dry-run"])
        # Assert
        assert result.exit_code == 0

    def test_dry_run_announces_plan(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["stop-playback", "--dry-run"])
        # Assert
        assert "DRY RUN" in result.output


class TestTranscribeAudio:
    def test_nonexistent_path_rejected(self, runner):
        # Arrange — Click's Path(exists=True) validation rejects a missing file
        # Act
        result = runner.invoke(audio, ["transcribe-audio", "/no/such/file.wav"])
        # Assert
        assert result.exit_code != 0

    def test_help_lists_language_option(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["transcribe-audio", "--help"])
        # Assert
        assert "--language" in result.output


class TestShowEnvTemplate:
    def test_stdout_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["show-env-template"])
        # Assert
        assert result.exit_code == 0

    def test_stdout_is_non_empty(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["show-env-template"])
        # Assert
        assert len(result.output) > 0

    def test_no_sensitive_flag_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["show-env-template", "--no-sensitive"])
        # Assert
        assert result.exit_code == 0


_DEPRECATED = [
    ("speak", "speak-text"),
    ("backends", "list-backends"),
    ("check", "check-backends"),
    ("stop", "stop-playback"),
    ("transcribe", "transcribe-audio"),
    ("env-template", "show-env-template"),
]


class TestDeprecatedRedirects:
    @pytest.mark.parametrize("old, new", _DEPRECATED)
    def test_old_command_exits_two(self, runner, old, new):
        # Arrange
        # Act
        result = runner.invoke(audio, [old, "anything"])
        # Assert
        assert result.exit_code == 2

    @pytest.mark.parametrize("old, new", _DEPRECATED)
    def test_old_command_names_new_command(self, runner, old, new):
        # Arrange
        # Act
        result = runner.invoke(audio, [old, "anything"])
        # Assert
        assert new in result.output


class TestListPythonApis:
    def test_runs_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-python-apis"])
        # Assert
        assert result.exit_code == 0

    def test_output_mentions_package(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-python-apis"])
        # Assert
        assert "scitex_audio" in result.output.lower()


# EOF

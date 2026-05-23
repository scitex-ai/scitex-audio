#!/usr/bin/env python3
# Timestamp: "2026-03-14 (ywatanabe)"
# File: tests/integration/test_dunder_main.py

"""Tests for the scitex-audio Click CLI entry point.

The CLI is a thin translator from option flags to the ``scitex_audio.speak``
API. The translation itself (``build_speak_kwargs``) is tested directly as a
pure function; the rest of the CLI surface (help text, subcommand listing,
choice validation) is exercised through the real ``CliRunner`` without any
mocks.
"""

import pytest
from click.testing import CliRunner

from scitex_audio._cli._commands._speak import build_speak_kwargs
from scitex_audio._cli._main import audio


@pytest.fixture
def runner():
    return CliRunner()


class TestMainFunction:
    """The top-level group renders help and exposes a callable entry point."""

    def test_main_entry_point_is_callable(self):
        # Arrange
        from scitex_audio.__main__ import main

        # Act
        result = callable(main)
        # Assert
        assert result is True

    def test_help_flag_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert result.exit_code == 0

    def test_help_flag_shows_text_to_speech_in_output(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "Text-to-speech" in result.output

    def test_no_args_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Assert
        assert result.exit_code == 0

    def test_no_args_shows_speak_or_tts_in_output(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Assert
        assert (
            "speak" in result.output.lower()
            or "text-to-speech" in result.output.lower()
        )


class TestBuildSpeakKwargs:
    """``build_speak_kwargs`` maps CLI options onto ``speak()`` kwargs."""

    def test_text_is_passed_through(self):
        # Arrange
        text = "Hello world"
        # Act
        kwargs = build_speak_kwargs(text, None, None, None, False, None, None, False)
        # Assert
        assert kwargs["text"] == "Hello world"

    def test_backend_option_sets_backend_kwarg(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs(
            "Hello", "gtts", None, None, False, None, None, False
        )
        # Assert
        assert kwargs["backend"] == "gtts"

    def test_voice_option_sets_voice_kwarg(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, "en", None, False, None, None, False)
        # Assert
        assert kwargs["voice"] == "en"

    def test_output_option_sets_output_path_kwarg(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs(
            "Hello", None, None, "/tmp/test.mp3", False, None, None, False
        )
        # Assert
        assert kwargs["output_path"] == "/tmp/test.mp3"

    def test_rate_option_sets_rate_kwarg(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, 200, None, False)
        # Assert
        assert kwargs["rate"] == 200

    def test_speed_option_sets_speed_kwarg(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, None, 1.5, False)
        # Assert
        assert kwargs["speed"] == 1.5

    def test_no_play_flag_sets_play_false(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, True, None, None, False)
        # Assert
        assert kwargs["play"] is False

    def test_play_defaults_true_when_no_play_absent(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, None, None, False)
        # Assert
        assert kwargs["play"] is True

    def test_no_fallback_flag_sets_fallback_false(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, None, None, True)
        # Assert
        assert kwargs["fallback"] is False

    def test_fallback_defaults_true_when_no_fallback_absent(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, None, None, False)
        # Assert
        assert kwargs["fallback"] is True

    def test_unset_optional_backend_is_absent(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("Hello", None, None, None, False, None, None, False)
        # Assert
        assert "backend" not in kwargs


class TestBackendsCommand:
    """``list-backends`` runs against the real backend registry."""

    def test_list_backends_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert result.exit_code == 0

    def test_list_backends_shows_fallback_order(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert "Fallback order" in result.output


class TestArgumentParser:
    """Choice validation and help-listed backend names."""

    def test_invalid_backend_is_rejected(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "Hello", "-b", "invalid"])
        # Assert
        assert result.exit_code != 0

    def test_speak_help_lists_pyttsx3(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Assert
        assert "pyttsx3" in result.output

    def test_speak_help_lists_gtts(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Assert
        assert "gtts" in result.output

    def test_speak_help_lists_elevenlabs(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Assert
        assert "elevenlabs" in result.output


class TestCLIIntegration:
    """End-to-end help and subcommand discovery."""

    def test_dunder_main_exposes_main(self):
        # Arrange
        from scitex_audio import __main__

        # Act
        result = hasattr(__main__, "main")
        # Assert
        assert result is True

    def test_help_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert result.exit_code == 0

    def test_help_lists_speak(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "speak" in result.output

    def test_help_lists_backends(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "backends" in result.output

    def test_help_recursive_exits_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert result.exit_code == 0

    def test_help_recursive_lists_speak(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert "speak" in result.output


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])

# EOF

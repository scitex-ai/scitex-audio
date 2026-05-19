#!/usr/bin/env python3
# Timestamp: "2026-03-14 (ywatanabe)"
# File: tests/test___main__.py

"""Tests for scitex_audio.__main__ module (Click CLI entry point)."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from scitex_audio._cli._main import audio


@pytest.fixture
def runner():
    return CliRunner()


class TestMainFunction:
    """Tests for main() function."""

    def test_main_function_exists(self):
        """Test main function exists."""
        # Arrange
        # Act
        from scitex_audio.__main__ import main

        # Assert
        assert callable(main)

    def test_help_flag_shows_help_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_help_flag_shows_help_text_to_speech_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert "Text-to-speech" in result.output


    def test_no_args_shows_help_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_no_args_shows_help_speak_in_result_output_lower_or_text_to_speech_in_result_out(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Act
        # Assert
        assert (
            "speak" in result.output.lower()
            or "text-to-speech" in result.output.lower()
        )



class TestSpeakCommand:
    """Tests for 'speak' subcommand."""

    def test_speak_command_calls_speak_function(self, runner):
        """Test 'speak-text' command calls speak function."""
        # Arrange
        # Act
        # Assert
        mock_speak = MagicMock(return_value={"played": True})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello world"])

        mock_speak.assert_called_once()
        assert mock_speak.call_count == 1

    def test_speak_with_backend_option(self, runner):
        """Test 'speak-text' command with --backend option."""
        # Arrange
        mock_speak = MagicMock(return_value={"played": True})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello", "-b", "gtts"])

        # Act
        call_kwargs = mock_speak.call_args[1]
        # Assert
        assert call_kwargs["backend"] == "gtts"

    def test_speak_with_voice_option(self, runner):
        """Test 'speak-text' command with --voice option."""
        # Arrange
        mock_speak = MagicMock(return_value={"played": True})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello", "-v", "en"])

        # Act
        call_kwargs = mock_speak.call_args[1]
        # Assert
        assert call_kwargs["voice"] == "en"

    def test_speak_with_output_option(self, runner):
        """Test 'speak-text' command with --output option."""
        # Arrange
        mock_speak = MagicMock(return_value={"played": True, "path": "/tmp/test.mp3"})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(
                audio, ["speak-text", "Hello", "-o", "/tmp/test.mp3"]
            )

        # Act
        call_kwargs = mock_speak.call_args[1]
        # Assert
        assert call_kwargs["output_path"] == "/tmp/test.mp3"

    def test_speak_with_no_play_option(self, runner):
        """Test 'speak-text' command with --no-play option."""
        # Arrange
        mock_speak = MagicMock(return_value={})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello", "--no-play"])

        # Act
        call_kwargs = mock_speak.call_args[1]
        # Assert
        assert call_kwargs["play"] is False

    def test_speak_with_no_fallback_option(self, runner):
        """Test 'speak-text' command with --no-fallback option."""
        # Arrange
        mock_speak = MagicMock(return_value={"played": True})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello", "--no-fallback"])

        # Act
        call_kwargs = mock_speak.call_args[1]
        # Assert
        assert call_kwargs["fallback"] is False


class TestBackendsCommand:
    """Tests for 'list-backends' subcommand."""

    def test_backends_command_lists_backends_result_exit_code_equals_n_0(self, runner):
        # Arrange
        mock_available = MagicMock(return_value=["gtts", "pyttsx3"])
        # Act
        with patch("scitex_audio.available_backends", mock_available):
            with patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ):
                result = runner.invoke(audio, ["list-backends"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_backends_command_lists_backends_available_in_result_output_lower_or_gtts_in_result_output_lo(self, runner):
        # Arrange
        mock_available = MagicMock(return_value=["gtts", "pyttsx3"])
        # Act
        with patch("scitex_audio.available_backends", mock_available):
            with patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ):
                result = runner.invoke(audio, ["list-backends"])
        # Act
        # Assert
        assert "available" in result.output.lower() or "gtts" in result.output.lower()


    def test_backends_shows_availability_result_exit_code_equals_n_0(self, runner):
        # Arrange
        mock_available = MagicMock(return_value=["gtts"])
        # Act
        with patch("scitex_audio.available_backends", mock_available):
            with patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ):
                result = runner.invoke(audio, ["list-backends"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_backends_shows_availability_available_in_result_output_lower(self, runner):
        # Arrange
        mock_available = MagicMock(return_value=["gtts"])
        # Act
        with patch("scitex_audio.available_backends", mock_available):
            with patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ):
                result = runner.invoke(audio, ["list-backends"])
        # Act
        # Assert
        assert "available" in result.output.lower()



class TestArgumentParser:
    """Tests for argument parsing."""

    def test_invalid_backend_rejected(self, runner):
        """Test invalid backend is rejected."""
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "Hello", "-b", "invalid"])
        # Assert
        assert result.exit_code != 0

    def test_backend_choices_pyttsx3_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Act
        # Assert
        assert "pyttsx3" in result.output

    def test_backend_choices_gtts_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Act
        # Assert
        assert "gtts" in result.output

    def test_backend_choices_elevenlabs_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Act
        # Assert
        assert "elevenlabs" in result.output



class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_cli_module_runnable(self):
        """Test module can be run as script."""
        # Arrange
        # Act
        from scitex_audio import __main__

        # Assert
        assert hasattr(__main__, "main")

    def test_cli_has_subcommands_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_cli_has_subcommands_speak_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert "speak" in result.output

    def test_cli_has_subcommands_backends_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert "backends" in result.output


    def test_help_recursive_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_help_recursive_speak_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Act
        # Assert
        assert "speak" in result.output



if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])

# EOF

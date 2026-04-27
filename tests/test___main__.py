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
        from scitex_audio.__main__ import main

        assert callable(main)

    def test_help_flag_shows_help(self, runner):
        """Test --help flag shows help message."""
        result = runner.invoke(audio, ["--help"])
        assert result.exit_code == 0
        assert "Text-to-speech" in result.output

    def test_no_args_shows_help(self, runner):
        """Test no arguments shows help."""
        result = runner.invoke(audio, [])
        assert result.exit_code == 0
        assert (
            "speak" in result.output.lower()
            or "text-to-speech" in result.output.lower()
        )


class TestSpeakCommand:
    """Tests for 'speak' subcommand."""

    def test_speak_command_calls_speak_function(self, runner):
        """Test 'speak-text' command calls speak function."""
        mock_speak = MagicMock(return_value={"played": True})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello world"])

        mock_speak.assert_called_once()

    def test_speak_with_backend_option(self, runner):
        """Test 'speak-text' command with --backend option."""
        mock_speak = MagicMock(return_value={"played": True})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello", "-b", "gtts"])

        call_kwargs = mock_speak.call_args[1]
        assert call_kwargs["backend"] == "gtts"

    def test_speak_with_voice_option(self, runner):
        """Test 'speak-text' command with --voice option."""
        mock_speak = MagicMock(return_value={"played": True})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello", "-v", "en"])

        call_kwargs = mock_speak.call_args[1]
        assert call_kwargs["voice"] == "en"

    def test_speak_with_output_option(self, runner):
        """Test 'speak-text' command with --output option."""
        mock_speak = MagicMock(return_value={"played": True, "path": "/tmp/test.mp3"})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(
                audio, ["speak-text", "Hello", "-o", "/tmp/test.mp3"]
            )

        call_kwargs = mock_speak.call_args[1]
        assert call_kwargs["output_path"] == "/tmp/test.mp3"

    def test_speak_with_no_play_option(self, runner):
        """Test 'speak-text' command with --no-play option."""
        mock_speak = MagicMock(return_value={})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello", "--no-play"])

        call_kwargs = mock_speak.call_args[1]
        assert call_kwargs["play"] is False

    def test_speak_with_no_fallback_option(self, runner):
        """Test 'speak-text' command with --no-fallback option."""
        mock_speak = MagicMock(return_value={"played": True})

        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello", "--no-fallback"])

        call_kwargs = mock_speak.call_args[1]
        assert call_kwargs["fallback"] is False


class TestBackendsCommand:
    """Tests for 'list-backends' subcommand."""

    def test_backends_command_lists_backends(self, runner):
        """Test 'list-backends' command lists available backends."""
        mock_available = MagicMock(return_value=["gtts", "pyttsx3"])

        with patch("scitex_audio.available_backends", mock_available):
            with patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ):
                result = runner.invoke(audio, ["list-backends"])

        assert result.exit_code == 0
        assert "available" in result.output.lower() or "gtts" in result.output.lower()

    def test_backends_shows_availability(self, runner):
        """Test 'list-backends' command shows availability status."""
        mock_available = MagicMock(return_value=["gtts"])

        with patch("scitex_audio.available_backends", mock_available):
            with patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ):
                result = runner.invoke(audio, ["list-backends"])

        assert result.exit_code == 0
        assert "available" in result.output.lower()


class TestArgumentParser:
    """Tests for argument parsing."""

    def test_invalid_backend_rejected(self, runner):
        """Test invalid backend is rejected."""
        result = runner.invoke(audio, ["speak-text", "Hello", "-b", "invalid"])
        assert result.exit_code != 0

    def test_backend_choices(self, runner):
        """Test valid backends are accepted."""
        result = runner.invoke(audio, ["speak-text", "--help"])
        assert "pyttsx3" in result.output
        assert "gtts" in result.output
        assert "elevenlabs" in result.output


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_cli_module_runnable(self):
        """Test module can be run as script."""
        from scitex_audio import __main__

        assert hasattr(__main__, "main")

    def test_cli_has_subcommands(self, runner):
        """Test CLI has expected subcommands."""
        result = runner.invoke(audio, ["--help"])
        assert result.exit_code == 0
        assert "speak" in result.output
        assert "backends" in result.output

    def test_help_recursive(self, runner):
        """Test --help-recursive shows all subcommands."""
        result = runner.invoke(audio, ["--help-recursive"])
        assert result.exit_code == 0
        assert "speak" in result.output


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])

# EOF

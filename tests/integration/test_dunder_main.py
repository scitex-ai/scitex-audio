#!/usr/bin/env python3
# Timestamp: "2026-05-23 (proj-scitex-audio)"
# File: tests/integration/test_dunder_main.py

"""Tests for scitex_audio.__main__ module (Click CLI entry point).

Replaces a prior mock-based version that relied on unittest.mock.patch.
The CLI re-imports `scitex_audio.speak` / `scitex_audio.available_backends`
each time a subcommand runs (`from scitex_audio import speak as tts_speak`
lives inside the function body), so a yield-based fixture that swaps the
real attribute on the module and restores afterwards is enough — no mocks.
"""

import pytest
from click.testing import CliRunner

import scitex_audio
from scitex_audio._cli._main import audio


class _SpeakRecorder:
    """Hand-rolled fake — records every call's kwargs."""

    def __init__(self, return_value: dict | None = None) -> None:
        self.calls: list[dict] = []
        self.return_value = return_value or {"played": True}

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.return_value


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def fake_speak():
    """Swap `scitex_audio.speak` with a recorder; restore on teardown."""
    recorder = _SpeakRecorder()
    real = scitex_audio.speak
    scitex_audio.speak = recorder
    try:
        yield recorder
    finally:
        scitex_audio.speak = real


@pytest.fixture
def fake_speak_with_path():
    """Recorder that reports a saved-file path (covers --output)."""
    recorder = _SpeakRecorder({"played": True, "path": "/tmp/test.mp3"})
    real = scitex_audio.speak
    scitex_audio.speak = recorder
    try:
        yield recorder
    finally:
        scitex_audio.speak = real


@pytest.fixture
def fake_backends():
    """Swap `available_backends` + `FALLBACK_ORDER` on the module."""
    real_avail = scitex_audio.available_backends
    real_order = scitex_audio.FALLBACK_ORDER
    scitex_audio.available_backends = lambda: ["gtts", "pyttsx3"]
    scitex_audio.FALLBACK_ORDER = ["pyttsx3", "gtts", "luxtts", "elevenlabs"]
    try:
        yield
    finally:
        scitex_audio.available_backends = real_avail
        scitex_audio.FALLBACK_ORDER = real_order


class TestMainFunction:
    """Tests for main() function."""

    def test_main_function_is_callable(self):
        # Arrange
        from scitex_audio.__main__ import main
        # Act
        result = callable(main)
        # Assert
        assert result is True

    def test_help_flag_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert result.exit_code == 0

    def test_help_flag_mentions_text_to_speech(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "Text-to-speech" in result.output

    def test_no_args_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Assert
        assert result.exit_code == 0

    def test_no_args_mentions_speak_or_tts(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Assert
        assert (
            "speak" in result.output.lower()
            or "text-to-speech" in result.output.lower()
        )


class TestSpeakCommand:
    """Tests for 'speak-text' subcommand — uses a hand-rolled recorder fake."""

    def test_speak_text_command_invokes_speak_exactly_once(self, runner, fake_speak):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello world"])
        # Assert
        assert len(fake_speak.calls) == 1

    def test_speak_text_threads_backend_option_into_kwargs(self, runner, fake_speak):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello", "-b", "gtts"])
        # Assert
        assert fake_speak.calls[0]["backend"] == "gtts"

    def test_speak_text_threads_voice_option_into_kwargs(self, runner, fake_speak):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello", "-v", "en"])
        # Assert
        assert fake_speak.calls[0]["voice"] == "en"

    def test_speak_text_threads_output_option_into_kwargs(
        self, runner, fake_speak_with_path
    ):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello", "-o", "/tmp/test.mp3"])
        # Assert
        assert fake_speak_with_path.calls[0]["output_path"] == "/tmp/test.mp3"

    def test_speak_text_no_play_threads_play_false_into_kwargs(
        self, runner, fake_speak
    ):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello", "--no-play"])
        # Assert
        assert fake_speak.calls[0]["play"] is False

    def test_speak_text_no_fallback_threads_fallback_false_into_kwargs(
        self, runner, fake_speak
    ):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello", "--no-fallback"])
        # Assert
        assert fake_speak.calls[0]["fallback"] is False


class TestBackendsCommand:
    """Tests for 'list-backends' subcommand."""

    def test_list_backends_exits_with_code_zero(self, runner, fake_backends):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert result.exit_code == 0

    def test_list_backends_output_mentions_available_or_gtts(
        self, runner, fake_backends
    ):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert (
            "available" in result.output.lower()
            or "gtts" in result.output.lower()
        )

    def test_list_backends_single_available_exits_with_code_zero(
        self, runner, fake_backends
    ):
        # Arrange
        scitex_audio.available_backends = lambda: ["gtts"]
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert result.exit_code == 0

    def test_list_backends_single_available_mentions_available(
        self, runner, fake_backends
    ):
        # Arrange
        scitex_audio.available_backends = lambda: ["gtts"]
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert "available" in result.output.lower()


class TestArgumentParser:
    """Tests for argument parsing."""

    def test_invalid_backend_is_rejected_nonzero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "Hello", "-b", "invalid"])
        # Assert
        assert result.exit_code != 0

    def test_speak_text_help_lists_pyttsx3_backend(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Assert
        assert "pyttsx3" in result.output

    def test_speak_text_help_lists_gtts_backend(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Assert
        assert "gtts" in result.output

    def test_speak_text_help_lists_elevenlabs_backend(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "--help"])
        # Assert
        assert "elevenlabs" in result.output


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_dunder_main_module_exposes_main_entry(self):
        # Arrange
        # Act
        from scitex_audio import __main__
        # Assert
        assert hasattr(__main__, "main")

    def test_root_help_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert result.exit_code == 0

    def test_root_help_lists_speak_subcommand(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "speak" in result.output

    def test_root_help_lists_backends_subcommand(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "backends" in result.output

    def test_help_recursive_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert result.exit_code == 0

    def test_help_recursive_lists_speak_subcommand(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert "speak" in result.output


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])

# EOF

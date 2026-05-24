#!/usr/bin/env python3
# Timestamp: 2026-05-23
# File: tests/scitex_audio/_engines/test__base.py

"""Tests for scitex_audio._engines._base.

Rewritten to honour the no-mocks rule: every patch / MagicMock pair is
replaced by a `ConcreteTTS` subclass that overrides `_play_audio` (or
the relevant hook) directly, or by injecting a hand-rolled runner into
the refactored `_play_audio(..., runner=)` keyword.
"""

import os
import subprocess
from pathlib import Path

import pytest

from scitex_audio._engines._base import BaseTTS, TTSBackend


class _ConcreteTTS(BaseTTS):
    """Minimal concrete subclass for testing BaseTTS behaviour."""

    def synthesize(self, text, output_path):
        path = Path(output_path)
        path.write_text("dummy audio")
        return path

    def get_voices(self):
        return []

    @property
    def name(self):
        return "test"


class _RecordingPlayTTS(_ConcreteTTS):
    """Concrete subclass that records whether _play_audio was invoked."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.play_calls: list[Path] = []

    def _play_audio(self, path, *, runner=None, timeout: int = 30) -> bool:
        self.play_calls.append(path)
        return True


class _AlwaysOkPlayTTS(_ConcreteTTS):
    """Concrete subclass whose _play_audio simply succeeds."""

    def _play_audio(self, path, *, runner=None, timeout: int = 30) -> bool:
        return True


class TestTTSBackend:
    """Tests for TTSBackend class."""

    def test_ttsbackend_elevenlabs_constant_equals_elevenlabs(self):
        # Arrange
        # Act
        value = TTSBackend.ELEVENLABS
        # Assert
        assert value == "elevenlabs"

    def test_ttsbackend_gtts_constant_equals_gtts(self):
        # Arrange
        # Act
        value = TTSBackend.GTTS
        # Assert
        assert value == "gtts"

    def test_ttsbackend_pyttsx3_constant_equals_pyttsx3(self):
        # Arrange
        # Act
        value = TTSBackend.PYTTSX3
        # Assert
        assert value == "pyttsx3"

    def test_ttsbackend_edge_constant_equals_edge(self):
        # Arrange
        # Act
        value = TTSBackend.EDGE
        # Assert
        assert value == "edge"

    def test_available_returns_list_type(self):
        # Arrange
        # Act
        result = TTSBackend.available()
        # Assert
        assert isinstance(result, list)

    def test_available_detects_real_gtts_installation(self):
        # Arrange — gtts is a test-time install dep of scitex-audio
        # Act
        backends = TTSBackend.available()
        # Assert
        assert "gtts" in backends

    def test_available_returns_list_with_no_exception(self):
        # Arrange
        # Act
        result = TTSBackend.available()
        # Assert
        assert isinstance(result, list)


class TestBaseTTS:
    """Tests for BaseTTS abstract base class."""

    def test_basetts_cannot_be_instantiated_without_overrides(self):
        # Arrange
        # Act
        ctx = pytest.raises(TypeError)
        # Assert
        with ctx:
            BaseTTS()

    def test_config_preserves_first_init_kwarg(self):
        # Arrange
        tts = _ConcreteTTS(key1="value1", key2="value2")
        # Act
        result = tts.config["key1"]
        # Assert
        assert result == "value1"

    def test_config_preserves_second_init_kwarg(self):
        # Arrange
        tts = _ConcreteTTS(key1="value1", key2="value2")
        # Act
        result = tts.config["key2"]
        # Assert
        assert result == "value2"

    def test_requires_api_key_default_value_is_false(self):
        # Arrange
        tts = _ConcreteTTS()
        # Act
        value = tts.requires_api_key
        # Assert
        assert value is False

    def test_requires_internet_default_value_is_false(self):
        # Arrange
        tts = _ConcreteTTS()
        # Act
        value = tts.requires_internet
        # Assert
        assert value is False

    def test_speak_with_output_path_returns_success_true(self, tmp_path):
        # Arrange
        tts = _AlwaysOkPlayTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.speak("Hello", output_path=str(output_file), play=True)
        # Assert
        assert result["success"] is True

    def test_speak_with_output_path_returns_synthesised_path(self, tmp_path):
        # Arrange
        tts = _AlwaysOkPlayTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.speak("Hello", output_path=str(output_file), play=True)
        # Assert
        assert result["path"] == output_file

    def test_speak_with_output_path_writes_output_file(self, tmp_path):
        # Arrange
        tts = _AlwaysOkPlayTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), play=True)
        # Assert
        assert output_file.exists()

    def test_speak_without_output_path_returns_success_true(self, tmp_path):
        # Arrange
        tts = _AlwaysOkPlayTTS()
        # Act
        result = tts.speak("Hello", play=True)
        # Assert
        assert result["success"] is True

    def test_speak_without_output_path_omits_path_key(self, tmp_path):
        # Arrange
        tts = _AlwaysOkPlayTTS()
        # Act
        result = tts.speak("Hello", play=True)
        # Assert
        assert "path" not in result

    def test_speak_with_voice_kwarg_stores_voice_in_config(self, tmp_path):
        # Arrange
        tts = _AlwaysOkPlayTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), voice="custom_voice")
        # Assert
        assert tts.config.get("voice") == "custom_voice"

    def test_speak_with_play_false_does_not_invoke_player(self, tmp_path):
        # Arrange
        tts = _RecordingPlayTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), play=False)
        # Assert
        assert tts.play_calls == []

    def test_play_audio_returns_false_when_no_players_on_path(self, tmp_path):
        # Arrange — empty bin/ on PATH, real subprocess.run will raise
        # FileNotFoundError for every candidate player.
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")
        empty_bin = tmp_path / "empty_bin"
        empty_bin.mkdir()
        saved_path = os.environ.get("PATH", "")
        os.environ["PATH"] = str(empty_bin)
        try:
            # Act
            result = tts._play_audio(test_file)
        finally:
            os.environ["PATH"] = saved_path
        # Assert
        assert result is False

    def test_play_audio_returns_false_when_runner_times_out(self, tmp_path):
        # Arrange — inject a fake runner that always raises TimeoutExpired,
        # exercising the real except-branch in production.
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")

        def fake_runner(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 0))

        # Act
        result = tts._play_audio(test_file, runner=fake_runner)
        # Assert
        assert result is False

    @pytest.mark.skipif(
        not os.path.exists("/mnt/c/Windows"), reason="WSL-specific test"
    )
    def test_play_audio_windows_returns_bool_when_in_wsl(self, tmp_path):
        # Arrange
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.wav"
        test_file.write_text("dummy")
        # Act
        result = tts._play_audio_windows(test_file)
        # Assert
        assert isinstance(result, bool)

    def test_play_audio_windows_returns_false_on_non_wsl_host(self, tmp_path):
        # Arrange — when /mnt/c/Windows is absent, production short-circuits
        # to False. This box is non-WSL, so we can observe the real path.
        if os.path.exists("/mnt/c/Windows"):
            pytest.skip("WSL host present — non-WSL branch can't be reached")
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.wav"
        test_file.write_text("dummy")
        # Act
        result = tts._play_audio_windows(test_file)
        # Assert
        assert result is False


class TestAbstractMethodsEnforced:
    """Test that abstract methods are enforced."""

    def test_subclass_missing_synthesize_cannot_be_instantiated(self):
        # Arrange
        class IncompleteTTS(BaseTTS):
            def get_voices(self):
                return []

            @property
            def name(self):
                return "test"

        # Act
        ctx = pytest.raises(TypeError)
        # Assert
        with ctx:
            IncompleteTTS()

    def test_subclass_missing_get_voices_cannot_be_instantiated(self):
        # Arrange
        class IncompleteTTS(BaseTTS):
            def synthesize(self, text, output_path):
                return Path(output_path)

            @property
            def name(self):
                return "test"

        # Act
        ctx = pytest.raises(TypeError)
        # Assert
        with ctx:
            IncompleteTTS()

    def test_subclass_missing_name_cannot_be_instantiated(self):
        # Arrange
        class IncompleteTTS(BaseTTS):
            def synthesize(self, text, output_path):
                return Path(output_path)

            def get_voices(self):
                return []

        # Act
        ctx = pytest.raises(TypeError)
        # Assert
        with ctx:
            IncompleteTTS()


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF

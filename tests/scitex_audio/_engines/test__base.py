#!/usr/bin/env python3
# Timestamp: 2026-01-04
# File: tests/scitex_audio/_engines/test__base.py

"""Tests for scitex_audio._engines._base.

No mocks: playback is exercised via a concrete subclass that overrides
``_play_audio`` with a real recording method, and the player-fallback logic
runs the real ``_play_audio`` with an injectable subprocess ``runner=`` fake.
"""

import os
import subprocess
from pathlib import Path

import pytest

from scitex_audio._engines._base import BaseTTS, TTSBackend


class _ConcreteTTS(BaseTTS):
    """Minimal concrete backend: writes a dummy file on synthesize."""

    def synthesize(self, text, output_path):
        path = Path(output_path)
        path.write_text("dummy audio")
        return path

    def get_voices(self):
        return []

    @property
    def name(self):
        return "test"


class _RecordingPlaybackTTS(_ConcreteTTS):
    """Concrete backend that records playback instead of playing audio."""

    def __init__(self, play_result=True, **kwargs):
        super().__init__(**kwargs)
        self.play_calls = []
        self._play_result = play_result

    def _play_audio(self, path, runner=None):
        self.play_calls.append(path)
        return self._play_result


class _FakeRunner:
    """subprocess.run stand-in: records argv, raises a configured error."""

    def __init__(self, error=None):
        self.calls = []
        self._error = error

    def __call__(self, cmd, **kwargs):
        self.calls.append(cmd)
        if self._error is not None:
            raise self._error
        return subprocess.CompletedProcess(cmd, 0)


class TestTTSBackendConstants:
    def test_elevenlabs_constant_equals_elevenlabs(self):
        # Arrange
        # Act
        value = TTSBackend.ELEVENLABS
        # Assert
        assert value == "elevenlabs"

    def test_gtts_constant_equals_gtts(self):
        # Arrange
        # Act
        value = TTSBackend.GTTS
        # Assert
        assert value == "gtts"

    def test_pyttsx3_constant_equals_pyttsx3(self):
        # Arrange
        # Act
        value = TTSBackend.PYTTSX3
        # Assert
        assert value == "pyttsx3"

    def test_edge_constant_equals_edge(self):
        # Arrange
        # Act
        value = TTSBackend.EDGE
        # Assert
        assert value == "edge"


class TestTTSBackendAvailable:
    def test_available_returns_list(self):
        # Arrange
        # Act
        result = TTSBackend.available()
        # Assert
        assert isinstance(result, list)

    def test_available_entries_are_known_backends(self):
        # Arrange
        known = {
            TTSBackend.GTTS,
            TTSBackend.PYTTSX3,
            TTSBackend.ELEVENLABS,
            TTSBackend.LUXTTS,
            TTSBackend.EDGE,
        }
        # Act
        result = set(TTSBackend.available())
        # Assert
        assert result <= known


class TestBaseTTSAbstractness:
    def test_cannot_instantiate_directly(self):
        # Arrange
        # Act
        ctx = pytest.raises(TypeError)
        # Assert
        with ctx:
            BaseTTS()

    def test_missing_synthesize_blocks_instantiation(self):
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

    def test_missing_get_voices_blocks_instantiation(self):
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

    def test_missing_name_blocks_instantiation(self):
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


class TestBaseTTSConfig:
    def test_first_kwarg_stored_in_config(self):
        # Arrange
        # Act
        tts = _ConcreteTTS(key1="value1", key2="value2")
        # Assert
        assert tts.config["key1"] == "value1"

    def test_second_kwarg_stored_in_config(self):
        # Arrange
        # Act
        tts = _ConcreteTTS(key1="value1", key2="value2")
        # Assert
        assert tts.config["key2"] == "value2"

    def test_requires_api_key_defaults_false(self):
        # Arrange
        tts = _ConcreteTTS()
        # Act
        result = tts.requires_api_key
        # Assert
        assert result is False

    def test_requires_internet_defaults_false(self):
        # Arrange
        tts = _ConcreteTTS()
        # Act
        result = tts.requires_internet
        # Assert
        assert result is False


class TestBaseTTSSpeak:
    def test_speak_with_output_reports_success(self, tmp_path):
        # Arrange
        tts = _RecordingPlaybackTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.speak("Hello", output_path=str(output_file), play=True)
        # Assert
        assert result["success"] is True

    def test_speak_with_output_returns_path(self, tmp_path):
        # Arrange
        tts = _RecordingPlaybackTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.speak("Hello", output_path=str(output_file), play=True)
        # Assert
        assert result["path"] == output_file

    def test_speak_with_output_writes_file(self, tmp_path):
        # Arrange
        tts = _RecordingPlaybackTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), play=True)
        # Assert
        assert output_file.exists()

    def test_speak_without_output_reports_success(self):
        # Arrange
        tts = _RecordingPlaybackTTS()
        # Act
        result = tts.speak("Hello", play=True)
        # Assert
        assert result["success"] is True

    def test_speak_without_output_omits_path_key(self):
        # Arrange
        tts = _RecordingPlaybackTTS()
        # Act
        result = tts.speak("Hello", play=True)
        # Assert
        assert "path" not in result

    def test_speak_records_voice_in_config(self, tmp_path):
        # Arrange
        tts = _RecordingPlaybackTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), voice="custom_voice")
        # Assert
        assert tts.config.get("voice") == "custom_voice"

    def test_speak_skips_playback_when_play_false(self, tmp_path):
        # Arrange
        tts = _RecordingPlaybackTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), play=False)
        # Assert
        assert tts.play_calls == []

    def test_speak_invokes_playback_when_play_true(self, tmp_path):
        # Arrange
        tts = _RecordingPlaybackTTS()
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), play=True)
        # Assert
        assert len(tts.play_calls) == 1


class TestBaseTTSToBytes:
    def test_to_bytes_returns_synthesized_bytes(self):
        # Arrange
        tts = _ConcreteTTS()
        # Act
        data = tts.to_bytes("Hello")
        # Assert
        assert data == b"dummy audio"

    def test_to_bytes_records_voice_in_config(self):
        # Arrange
        tts = _ConcreteTTS()
        # Act
        tts.to_bytes("Hello", voice="fr")
        # Assert
        assert tts.config.get("voice") == "fr"


class TestBaseTTSPlayAudio:
    """The real `_play_audio`, driven through an injectable subprocess runner."""

    def test_missing_player_falls_through_to_warning(self, tmp_path):
        # Arrange
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_text("dummy")
        runner = _FakeRunner(error=FileNotFoundError("player not found"))
        # Act
        result = tts._play_audio(test_file, runner=runner)
        # Assert
        assert result is False

    def test_missing_player_tries_each_candidate(self, tmp_path):
        # Arrange
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_text("dummy")
        runner = _FakeRunner(error=FileNotFoundError("player not found"))
        # Act
        tts._play_audio(test_file, runner=runner)
        # Assert
        assert len(runner.calls) == 4

    def test_timeout_reports_failure(self, tmp_path):
        # Arrange
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_text("dummy")
        runner = _FakeRunner(error=subprocess.TimeoutExpired("ffplay", 30))
        # Act
        result = tts._play_audio(test_file, runner=runner)
        # Assert
        assert result is False

    def test_first_successful_player_reports_success(self, tmp_path):
        # Arrange
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_text("dummy")
        runner = _FakeRunner()  # no error -> succeeds immediately
        # Act
        result = tts._play_audio(test_file, runner=runner)
        # Assert
        assert result is True

    def test_successful_player_stops_after_first(self, tmp_path):
        # Arrange
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_text("dummy")
        runner = _FakeRunner()
        # Act
        tts._play_audio(test_file, runner=runner)
        # Assert
        assert len(runner.calls) == 1


class TestBaseTTSPlayAudioWindows:
    @pytest.mark.skipif(
        os.path.exists("/mnt/c/Windows"), reason="non-WSL behaviour under test"
    )
    def test_windows_fallback_false_when_not_wsl(self, tmp_path):
        # Arrange
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.wav"
        test_file.write_text("dummy")
        # Act
        result = tts._play_audio_windows(test_file)
        # Assert
        assert result is False

    @pytest.mark.skipif(
        not os.path.exists("/mnt/c/Windows"), reason="WSL-specific test"
    )
    def test_windows_fallback_returns_bool_in_wsl(self, tmp_path):
        # Arrange
        tts = _ConcreteTTS()
        test_file = tmp_path / "test.wav"
        test_file.write_text("dummy")
        # Act
        result = tts._play_audio_windows(test_file)
        # Assert
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF

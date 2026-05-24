#!/usr/bin/env python3
# Timestamp: "2026-03-14 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/test__tts.py

"""Tests for scitex_audio._tts (legacy ElevenLabs TTS facade).

No mocks: the ElevenLabs client is an injectable constructor seam
(``TTS(client=...)``); the import-error path uses a ``client_factory`` that
raises; playback uses ``TTS._play_audio(runner=...)`` with a hand-rolled
subprocess fake; env vars use yield-based save/restore fixtures.
"""

import inspect
import os
import subprocess

import pytest

from scitex_audio import _tts
from scitex_audio._tts import TTS, TTSConfig, speak


# --------------------------------------------------------------------------- #
# Hand-rolled fakes                                                           #
# --------------------------------------------------------------------------- #
class _FakeTextToSpeech:
    def __init__(self, audio_chunks):
        self._audio_chunks = audio_chunks
        self.convert_calls = []

    def convert(self, **kwargs):
        self.convert_calls.append(kwargs)
        return list(self._audio_chunks)


class _FakeVoice:
    def __init__(self, name, voice_id, labels):
        self.name = name
        self.voice_id = voice_id
        self.labels = labels


class _FakeVoicesEndpoint:
    def __init__(self, voices):
        self._voices = voices

    def get_all(self):
        class _Resp:
            pass

        resp = _Resp()
        resp.voices = self._voices
        return resp


class _FakeElevenLabsClient:
    def __init__(self, audio_chunks=(b"audio", b"data"), voices=None):
        self.text_to_speech = _FakeTextToSpeech(audio_chunks)
        self.voices = _FakeVoicesEndpoint(voices or [])


class _FakeRunner:
    def __init__(self, error=None):
        self.calls = []
        self._error = error

    def __call__(self, cmd, **kwargs):
        self.calls.append(cmd)
        if self._error is not None:
            raise self._error
        return subprocess.CompletedProcess(cmd, 0)


@pytest.fixture
def env_save_restore():
    keys = ("ELEVENLABS_API_KEY", "SCITEX_AUDIO_ELEVENLABS_API_KEY")
    saved = {k: os.environ.get(k) for k in keys}
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# --------------------------------------------------------------------------- #
# TTSConfig                                                                   #
# --------------------------------------------------------------------------- #
class TestTTSConfig:
    def test_default_voice_id_is_adam(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.voice_id == "pNInz6obpgDQGcFmaJgB"

    def test_default_voice_name_is_none(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.voice_name is None

    def test_default_model_id(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.model_id == "eleven_multilingual_v2"

    def test_default_stability_is_half(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.stability == 0.5

    def test_default_similarity_boost(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.similarity_boost == 0.75


# --------------------------------------------------------------------------- #
# TTS initialization                                                          #
# --------------------------------------------------------------------------- #
class TestTTSInitialization:
    def test_custom_api_key_stored(self):
        # Arrange
        # Act
        tts = TTS(api_key="test-key")
        # Assert
        assert tts.api_key == "test-key"

    def test_api_key_from_elevenlabs_env(self, env_save_restore):
        # Arrange
        os.environ.pop("SCITEX_AUDIO_ELEVENLABS_API_KEY", None)
        os.environ["ELEVENLABS_API_KEY"] = "env-api-key"
        # Act
        tts = TTS()
        # Assert
        assert tts.api_key == "env-api-key"

    def test_scitex_env_takes_precedence(self, env_save_restore):
        # Arrange
        os.environ["ELEVENLABS_API_KEY"] = "low"
        os.environ["SCITEX_AUDIO_ELEVENLABS_API_KEY"] = "high"
        # Act
        tts = TTS()
        # Assert
        assert tts.api_key == "high"

    def test_voice_name_sets_voice_id(self):
        # Arrange
        # Act
        tts = TTS(voice_name="rachel")
        # Assert
        assert tts.config.voice_id == TTS.VOICES["rachel"]

    def test_voice_id_overrides_voice_name(self):
        # Arrange
        # Act
        tts = TTS(voice_name="rachel", voice_id="custom-voice-id")
        # Assert
        assert tts.config.voice_id == "custom-voice-id"

    def test_stability_kwarg_passed_to_config(self):
        # Arrange
        # Act
        tts = TTS(stability=0.8, speed=1.5)
        # Assert
        assert tts.config.stability == 0.8

    def test_speed_kwarg_passed_to_config(self):
        # Arrange
        # Act
        tts = TTS(stability=0.8, speed=1.5)
        # Assert
        assert tts.config.speed == 1.5

    def test_client_none_until_accessed(self):
        # Arrange
        # Act
        tts = TTS()
        # Assert
        assert tts._client is None

    def test_voice_name_lookup_is_case_insensitive(self):
        # Arrange
        # Act
        upper = TTS(voice_name="RACHEL")
        # Assert
        assert upper.config.voice_id == TTS.VOICES["rachel"]


class TestTTSClientLoading:
    def test_injected_client_is_used(self):
        # Arrange
        fake = _FakeElevenLabsClient()
        # Act
        tts = TTS(client=fake)
        # Assert
        assert tts.client is fake

    def test_client_factory_import_error_propagates(self):
        # Arrange
        def boom(api_key):
            raise ImportError("elevenlabs not installed")

        tts = TTS(client_factory=boom)
        # Act
        ctx = pytest.raises(ImportError)
        # Assert
        with ctx:
            _ = tts.client


class TestTTSSpeak:
    def test_speak_method_is_callable(self):
        # Arrange
        tts = TTS(client=_FakeElevenLabsClient())
        # Act
        result = callable(tts.speak)
        # Assert
        assert result is True

    def test_returns_output_path_when_saving(self, tmp_path):
        # Arrange
        tts = TTS(api_key="test-key", client=_FakeElevenLabsClient())
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.speak("Hello", output_path=str(output_file), play=False)
        # Assert
        assert result == output_file

    def test_writes_output_file(self, tmp_path):
        # Arrange
        tts = TTS(api_key="test-key", client=_FakeElevenLabsClient())
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), play=False)
        # Assert
        assert output_file.exists()

    def test_voice_name_maps_to_voice_id_in_call(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient(audio_chunks=[b"audio"])
        tts = TTS(api_key="test-key", client=fake)
        # Act
        tts.speak(
            "Hello",
            output_path=str(tmp_path / "out.mp3"),
            voice_name="adam",
            play=False,
        )
        # Assert
        assert fake.text_to_speech.convert_calls[0]["voice_id"] == TTS.VOICES["adam"]

    def test_voice_id_passed_through_in_call(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient(audio_chunks=[b"audio"])
        tts = TTS(api_key="test-key", client=fake)
        # Act
        tts.speak(
            "Hello",
            output_path=str(tmp_path / "out.mp3"),
            voice_id="custom-voice-id",
            play=False,
        )
        # Assert
        assert fake.text_to_speech.convert_calls[0]["voice_id"] == "custom-voice-id"

    def test_returns_none_without_output_path(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient(audio_chunks=[b"audio"])
        tts = TTS(api_key="test-key", client=fake)
        # Act — play=True with the default runner would shell out; pass a
        # no-op via a subclass-free seam: use play=False but no output.
        result = tts.speak("Hello", play=False)
        # Assert
        assert result is None


class TestTTSListVoices:
    def test_returns_a_list(self):
        # Arrange
        fake = _FakeElevenLabsClient(voices=[_FakeVoice("Test Voice", "test-id", {})])
        tts = TTS(api_key="test-key", client=fake)
        # Act
        voices = tts.list_voices()
        # Assert
        assert isinstance(voices, list)

    def test_one_dict_per_voice(self):
        # Arrange
        fake = _FakeElevenLabsClient(voices=[_FakeVoice("Test Voice", "test-id", {})])
        tts = TTS(api_key="test-key", client=fake)
        # Act
        voices = tts.list_voices()
        # Assert
        assert len(voices) == 1

    def test_voice_dict_carries_name(self):
        # Arrange
        fake = _FakeElevenLabsClient(voices=[_FakeVoice("Test Voice", "test-id", {})])
        tts = TTS(api_key="test-key", client=fake)
        # Act
        voices = tts.list_voices()
        # Assert
        assert voices[0]["name"] == "Test Voice"


class TestTTSPlayAudio:
    def test_play_audio_tries_each_player(self, tmp_path):
        # Arrange
        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")
        runner = _FakeRunner(error=FileNotFoundError("player not found"))
        # Act
        tts._play_audio(test_file, runner=runner)
        # Assert
        assert len(runner.calls) == 4

    def test_first_successful_player_stops_iteration(self, tmp_path):
        # Arrange
        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")
        runner = _FakeRunner()
        # Act
        tts._play_audio(test_file, runner=runner)
        # Assert
        assert len(runner.calls) == 1

    @pytest.mark.skipif(
        os.path.exists("/mnt/c/Windows"), reason="non-WSL behaviour under test"
    )
    def test_windows_fallback_false_when_not_wsl(self, tmp_path):
        # Arrange
        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")
        # Act
        result = tts._play_audio_windows(test_file)
        # Assert
        assert result is False


class TestModuleLevelSpeak:
    def test_speak_function_is_callable(self):
        # Arrange
        # Act
        result = callable(speak)
        # Assert
        assert result is True

    def test_speak_creates_default_tts(self):
        # Arrange
        _tts._default_tts = None
        fake = _FakeElevenLabsClient(audio_chunks=[b"audio"])
        # Act — inject the fake client via kwargs forwarded to TTS()
        speak("Hello", play=False, client=fake)
        # Assert
        assert _tts._default_tts is not None

    def test_speak_signature_has_voice(self):
        # Arrange
        sig = inspect.signature(speak)
        # Act
        params = sig.parameters
        # Assert
        assert "voice" in params

    def test_speak_signature_has_output_path(self):
        # Arrange
        sig = inspect.signature(speak)
        # Act
        params = sig.parameters
        # Assert
        assert "output_path" in params


class TestTTSEdgeCases:
    def test_init_without_args_succeeds(self):
        # Arrange
        # Act
        tts = TTS()
        # Assert
        assert tts is not None


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF

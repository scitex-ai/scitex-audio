#!/usr/bin/env python3
# Timestamp: 2026-01-04
# File: tests/scitex_audio/_engines/test__elevenlabs_engine.py

"""Tests for scitex_audio._engines._elevenlabs_engine.

No mocks: the ElevenLabs SDK client is an injectable constructor seam
(``ElevenLabsTTS(client=...)``). Tests pass small hand-rolled fakes that
expose only the methods the engine actually calls and record their args.
"""

import os

import pytest

from scitex_audio._engines._base import BaseTTS
from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS


# --------------------------------------------------------------------------- #
# Hand-rolled fakes (only the surface the engine touches)                      #
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
    def __init__(self, voices=None, error=None):
        self._voices = voices or []
        self._error = error

    def get_all(self):
        if self._error is not None:
            raise self._error

        class _Resp:
            pass

        resp = _Resp()
        resp.voices = self._voices
        return resp


class _FakeElevenLabsClient:
    """Minimal stand-in for ``elevenlabs.client.ElevenLabs``."""

    def __init__(self, audio_chunks=(b"audio", b"data"), voices=None, error=None):
        self.text_to_speech = _FakeTextToSpeech(audio_chunks)
        self.voices = _FakeVoicesEndpoint(voices=voices, error=error)


@pytest.fixture
def env_save_restore():
    """Snapshot the ElevenLabs env vars; restore on teardown."""
    keys = (
        "ELEVENLABS_API_KEY",
        "SCITEX_AUDIO_ELEVENLABS_API_KEY",
        "SCITEX_AUDIO_ELEVENLABS_MODEL",
    )
    saved = {k: os.environ.get(k) for k in keys}
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TestElevenLabsTTSProperties:
    def test_name_is_elevenlabs(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        name = tts.name
        # Assert
        assert name == "elevenlabs"

    def test_requires_api_key_is_true(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        result = tts.requires_api_key
        # Assert
        assert result is True

    def test_requires_internet_is_true(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        result = tts.requires_internet
        # Assert
        assert result is True

    def test_inherits_from_base_tts(self):
        # Arrange
        # Act
        result = issubclass(ElevenLabsTTS, BaseTTS)
        # Assert
        assert result is True


class TestElevenLabsTTSDefaults:
    def test_default_voice_is_adam(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        voice = tts.voice
        # Assert
        assert voice == "adam"

    def test_default_model_id_is_low_latency_turbo(self, env_save_restore):
        # Arrange
        os.environ.pop("SCITEX_AUDIO_ELEVENLABS_MODEL", None)
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.model_id == "eleven_turbo_v2_5"

    def test_model_id_read_from_env_when_unset(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_ELEVENLABS_MODEL"] = "eleven_flash_v2_5"
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.model_id == "eleven_flash_v2_5"

    def test_explicit_model_id_takes_precedence_over_env(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_ELEVENLABS_MODEL"] = "eleven_flash_v2_5"
        # Act
        tts = ElevenLabsTTS(model_id="eleven_multilingual_v2")
        # Assert
        assert tts.model_id == "eleven_multilingual_v2"

    def test_default_stability_is_half(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        stability = tts.stability
        # Assert
        assert stability == 0.5

    def test_default_similarity_boost(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        similarity = tts.similarity_boost
        # Assert
        assert similarity == 0.75

    def test_default_speed_is_one(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        speed = tts.speed
        # Assert
        assert speed == 1.0


class TestElevenLabsTTSInitialization:
    def test_custom_api_key_is_stored(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(api_key="test-api-key")
        # Assert
        assert tts.api_key == "test-api-key"

    def test_api_key_read_from_elevenlabs_env(self, env_save_restore):
        # Arrange
        os.environ.pop("SCITEX_AUDIO_ELEVENLABS_API_KEY", None)
        os.environ["ELEVENLABS_API_KEY"] = "env-api-key"
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.api_key == "env-api-key"

    def test_scitex_env_takes_precedence_over_elevenlabs_env(self, env_save_restore):
        # Arrange
        os.environ["ELEVENLABS_API_KEY"] = "low-priority"
        os.environ["SCITEX_AUDIO_ELEVENLABS_API_KEY"] = "high-priority"
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.api_key == "high-priority"

    def test_api_key_is_none_when_env_absent(self, env_save_restore):
        # Arrange
        os.environ.pop("ELEVENLABS_API_KEY", None)
        os.environ.pop("SCITEX_AUDIO_ELEVENLABS_API_KEY", None)
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.api_key is None

    def test_custom_voice_is_stored(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(voice="bella")
        # Assert
        assert tts.voice == "bella"

    def test_custom_model_is_stored(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(model_id="custom_model")
        # Assert
        assert tts.model_id == "custom_model"

    def test_custom_stability_is_stored(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(stability=0.8)
        # Assert
        assert tts.stability == 0.8

    def test_custom_similarity_boost_is_stored(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(similarity_boost=0.9)
        # Assert
        assert tts.similarity_boost == 0.9

    def test_high_speed_is_clamped_to_max(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(speed=1.5)
        # Assert
        assert tts.speed == ElevenLabsTTS.MAX_SPEED

    def test_client_is_none_until_accessed(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts._client is None

    def test_injected_client_is_used(self):
        # Arrange
        fake = _FakeElevenLabsClient()
        # Act
        tts = ElevenLabsTTS(client=fake)
        # Assert
        assert tts.client is fake


class TestElevenLabsVoiceMapping:
    def test_voice_name_maps_to_id(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        voice_id = tts._get_voice_id("rachel")
        # Assert
        assert voice_id == ElevenLabsTTS.VOICES["rachel"]

    def test_unknown_id_passes_through(self):
        # Arrange
        tts = ElevenLabsTTS()
        custom_id = "custom-voice-id-12345"
        # Act
        voice_id = tts._get_voice_id(custom_id)
        # Assert
        assert voice_id == custom_id

    def test_voice_lookup_is_case_insensitive(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        upper = tts._get_voice_id("RACHEL")
        # Assert
        assert upper == ElevenLabsTTS.VOICES["rachel"]

    def test_none_voice_uses_instance_default(self):
        # Arrange
        tts = ElevenLabsTTS(voice="adam")
        # Act
        voice_id = tts._get_voice_id(None)
        # Assert
        assert voice_id == ElevenLabsTTS.VOICES["adam"]

    def test_voices_dictionary_contains_rachel(self):
        # Arrange
        # Act
        present = "rachel" in ElevenLabsTTS.VOICES
        # Assert
        assert present is True

    def test_voices_dictionary_contains_adam(self):
        # Arrange
        # Act
        present = "adam" in ElevenLabsTTS.VOICES
        # Assert
        assert present is True

    def test_all_preset_voices_have_string_ids(self):
        # Arrange
        # Act
        all_strings = all(
            isinstance(vid, str) and vid for vid in ElevenLabsTTS.VOICES.values()
        )
        # Assert
        assert all_strings is True

    def test_at_least_eight_preset_voices(self):
        # Arrange
        # Act
        count = len(ElevenLabsTTS.VOICES)
        # Assert
        assert count >= 8


class TestElevenLabsSynthesize:
    def test_passes_text_to_convert(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient()
        tts = ElevenLabsTTS(api_key="test-key", client=fake)
        # Act
        tts.synthesize("Hello world", str(tmp_path / "out.mp3"))
        # Assert
        assert fake.text_to_speech.convert_calls[0]["text"] == "Hello world"

    def test_passes_voice_id_to_convert(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient()
        tts = ElevenLabsTTS(api_key="test-key", client=fake)
        # Act
        tts.synthesize("Hello world", str(tmp_path / "out.mp3"))
        # Assert
        assert "voice_id" in fake.text_to_speech.convert_calls[0]

    def test_returns_output_path(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient()
        tts = ElevenLabsTTS(api_key="test-key", client=fake)
        output_file = tmp_path / "out.mp3"
        # Act
        result = tts.synthesize("Hello world", str(output_file))
        # Assert
        assert result == output_file

    def test_writes_output_file(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient()
        tts = ElevenLabsTTS(api_key="test-key", client=fake)
        output_file = tmp_path / "out.mp3"
        # Act
        tts.synthesize("Hello", str(output_file))
        # Assert
        assert output_file.exists()

    def test_concatenates_audio_chunks(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient(audio_chunks=[b"chunk1", b"chunk2", b"chunk3"])
        tts = ElevenLabsTTS(api_key="test-key", client=fake)
        output_file = tmp_path / "out.mp3"
        # Act
        tts.synthesize("Hello", str(output_file))
        # Assert
        assert output_file.read_bytes() == b"chunk1chunk2chunk3"

    def test_uses_voice_from_config(self, tmp_path):
        # Arrange
        fake = _FakeElevenLabsClient(audio_chunks=[b"audio"])
        tts = ElevenLabsTTS(api_key="test-key", client=fake)
        tts.config["voice"] = "adam"
        # Act
        tts.synthesize("Hello", str(tmp_path / "out.mp3"))
        # Assert
        call = fake.text_to_speech.convert_calls[0]
        assert call["voice_id"] == ElevenLabsTTS.VOICES["adam"]


class TestElevenLabsGetVoices:
    def test_returns_a_list(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        voices = tts.get_voices()
        # Assert
        assert isinstance(voices, list)

    def test_includes_all_preset_voices(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        voices = tts.get_voices()
        # Assert
        assert len(voices) >= len(ElevenLabsTTS.VOICES)

    def test_includes_custom_voice_from_api(self):
        # Arrange
        custom = _FakeVoice("Custom Voice", "custom-id", {"accent": "British"})
        fake = _FakeElevenLabsClient(voices=[custom])
        tts = ElevenLabsTTS(api_key="test-key", client=fake)
        # Act
        custom_voices = [v for v in tts.get_voices() if v.get("type") == "custom"]
        # Assert
        assert custom_voices == [
            {
                "name": "Custom Voice",
                "id": "custom-id",
                "type": "custom",
                "labels": {"accent": "British"},
            }
        ]

    def test_api_error_falls_back_to_presets(self):
        # Arrange
        fake = _FakeElevenLabsClient(error=RuntimeError("API Error"))
        tts = ElevenLabsTTS(api_key="test-key", client=fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert len(voices) == len(ElevenLabsTTS.VOICES)


class TestElevenLabsTTSEdgeCases:
    def test_zero_stability_preserved(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(stability=0.0)
        # Assert
        assert tts.stability == 0.0

    def test_max_stability_preserved(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(stability=1.0)
        # Assert
        assert tts.stability == 1.0

    def test_zero_similarity_boost_preserved(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(similarity_boost=0.0)
        # Assert
        assert tts.similarity_boost == 0.0

    def test_max_similarity_boost_preserved(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(similarity_boost=1.0)
        # Assert
        assert tts.similarity_boost == 1.0

    def test_slow_speed_clamped_to_min(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(speed=0.5)
        # Assert
        assert tts.speed == ElevenLabsTTS.MIN_SPEED

    def test_fast_speed_clamped_to_max(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(speed=2.0)
        # Assert
        assert tts.speed == ElevenLabsTTS.MAX_SPEED

    def test_mid_speed_preserved(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(speed=1.0)
        # Assert
        assert tts.speed == 1.0


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF

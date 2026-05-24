#!/usr/bin/env python3
# Timestamp: 2026-05-23
# File: tests/scitex_audio/_engines/test__elevenlabs_engine.py

"""Tests for scitex_audio._engines._elevenlabs_engine.

Mock-free rewrite: `ElevenLabsTTS` already exposes its `_client`
attribute, so tests inject a hand-rolled `_FakeElevenLabsClient` that
records every `text_to_speech.convert(...)` call's kwargs as plain
data. Environment-variable tests use a `clean_elevenlabs_env`
yield-based fixture that snapshots / restores `os.environ` for the
two API-key vars — no monkeypatch.
"""

import os
from typing import Any

import pytest

from scitex_audio._engines._base import BaseTTS
from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

_API_KEY_ENV_VARS = (
    "ELEVENLABS_API_KEY",
    "SCITEX_AUDIO_ELEVENLABS_API_KEY",
)


class _FakeConvertResult:
    """Iterable that yields the configured audio chunks once."""

    def __init__(self, chunks):
        self._chunks = list(chunks)

    def __iter__(self):
        return iter(self._chunks)


class _FakeTextToSpeech:
    def __init__(self, chunks):
        self.calls: list[dict] = []
        self._chunks = chunks

    def convert(self, **kwargs):
        self.calls.append(dict(kwargs))
        return _FakeConvertResult(self._chunks)


class _FakeVoiceResponse:
    def __init__(self, voices):
        self.voices = voices


class _FakeVoices:
    """Fake of `client.voices` — controls what get_all() returns."""

    def __init__(self, voices=None, raise_exc=None):
        self._voices = voices or []
        self._raise_exc = raise_exc

    def get_all(self):
        if self._raise_exc is not None:
            raise self._raise_exc
        return _FakeVoiceResponse(self._voices)


class _FakeElevenLabsClient:
    """Hand-rolled fake of the ElevenLabs SDK client used by ElevenLabsTTS."""

    def __init__(self, *, chunks=None, voices=None, voices_exc=None):
        self.text_to_speech = _FakeTextToSpeech(chunks or [b"audio"])
        self.voices = _FakeVoices(voices=voices, raise_exc=voices_exc)


class _FakeCustomVoice:
    def __init__(self, name: str, voice_id: str, labels: dict[str, Any]):
        self.name = name
        self.voice_id = voice_id
        self.labels = labels


@pytest.fixture
def clean_elevenlabs_env():
    """Snapshot the two ElevenLabs API-key env vars; restore on teardown."""
    saved = {k: os.environ.get(k) for k in _API_KEY_ENV_VARS}
    for k in _API_KEY_ENV_VARS:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _make_tts(client: _FakeElevenLabsClient, **kwargs) -> ElevenLabsTTS:
    tts = ElevenLabsTTS(api_key=kwargs.pop("api_key", "test-key"), **kwargs)
    tts._client = client
    return tts


class TestElevenLabsTTS:
    """Tests for ElevenLabsTTS class."""

    def test_name_property_returns_elevenlabs(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        value = tts.name
        # Assert
        assert value == "elevenlabs"

    def test_requires_api_key_property_returns_true(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        value = tts.requires_api_key
        # Assert
        assert value is True

    def test_requires_internet_property_returns_true(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        value = tts.requires_internet
        # Assert
        assert value is True

    def test_default_voice_is_adam(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        value = tts.voice
        # Assert
        assert value == "adam"

    def test_default_model_id_is_multilingual_v2(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        value = tts.model_id
        # Assert
        assert value == "eleven_multilingual_v2"

    def test_default_stability_is_half(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        value = tts.stability
        # Assert
        assert value == 0.5

    def test_default_similarity_boost_is_three_quarters(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        value = tts.similarity_boost
        # Assert
        assert value == 0.75

    def test_default_speed_is_one(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        value = tts.speed
        # Assert
        assert value == 1.0

    def test_custom_api_key_initialization_preserves_key(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(api_key="test-api-key")
        # Assert
        assert tts.api_key == "test-api-key"

    def test_api_key_read_from_elevenlabs_env_var(self, clean_elevenlabs_env):
        # Arrange
        os.environ["ELEVENLABS_API_KEY"] = "env-api-key"
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.api_key == "env-api-key"

    def test_api_key_prefers_scitex_audio_specific_env_var(
        self, clean_elevenlabs_env
    ):
        # Arrange
        os.environ["ELEVENLABS_API_KEY"] = "shared-key"
        os.environ["SCITEX_AUDIO_ELEVENLABS_API_KEY"] = "scitex-key"
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.api_key == "scitex-key"

    def test_custom_voice_initialization_preserves_voice(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(voice="adam")
        # Assert
        assert tts.voice == "adam"

    def test_custom_model_initialization_preserves_model(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(model_id="custom_model")
        # Assert
        assert tts.model_id == "custom_model"

    def test_custom_stability_initialization_preserves_value(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(stability=0.8)
        # Assert
        assert tts.stability == 0.8

    def test_custom_similarity_boost_initialization_preserves_value(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(similarity_boost=0.9)
        # Assert
        assert tts.similarity_boost == 0.9

    def test_custom_speed_above_limit_clamps_to_max(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS(speed=1.5)
        # Assert
        assert tts.speed == ElevenLabsTTS.MAX_SPEED

    def test_voices_table_includes_rachel_preset(self):
        # Arrange
        # Act
        keys = ElevenLabsTTS.VOICES
        # Assert
        assert "rachel" in keys

    def test_voices_table_includes_adam_preset(self):
        # Arrange
        # Act
        keys = ElevenLabsTTS.VOICES
        # Assert
        assert "adam" in keys

    def test_voices_table_includes_bella_preset(self):
        # Arrange
        # Act
        keys = ElevenLabsTTS.VOICES
        # Assert
        assert "bella" in keys

    def test_voices_table_includes_josh_preset(self):
        # Arrange
        # Act
        keys = ElevenLabsTTS.VOICES
        # Assert
        assert "josh" in keys

    def test_client_is_lazy_until_first_access(self):
        # Arrange
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts._client is None

    def test_inherits_from_base_tts(self):
        # Arrange
        # Act
        result = issubclass(ElevenLabsTTS, BaseTTS)
        # Assert
        assert result is True

    def test_get_voice_id_resolves_name_to_preset_id(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        voice_id = tts._get_voice_id("rachel")
        # Assert
        assert voice_id == ElevenLabsTTS.VOICES["rachel"]

    def test_get_voice_id_returns_unknown_string_unchanged(self):
        # Arrange
        tts = ElevenLabsTTS()
        custom_id = "custom-voice-id-12345"
        # Act
        voice_id = tts._get_voice_id(custom_id)
        # Assert
        assert voice_id == custom_id

    def test_get_voice_id_is_case_insensitive_for_presets(self):
        # Arrange
        tts = ElevenLabsTTS()
        # Act
        voice_id_upper = tts._get_voice_id("RACHEL")
        # Assert
        assert voice_id_upper == ElevenLabsTTS.VOICES["rachel"]

    def test_get_voice_id_with_none_uses_default_voice(self):
        # Arrange
        tts = ElevenLabsTTS(voice="adam")
        # Act
        voice_id = tts._get_voice_id(None)
        # Assert
        assert voice_id == ElevenLabsTTS.VOICES["adam"]

    def test_synthesize_passes_text_to_convert_api(self, tmp_path):
        # Arrange
        client = _FakeElevenLabsClient(chunks=[b"audio", b"data"])
        tts = _make_tts(client)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert client.text_to_speech.calls[0]["text"] == "Hello world"

    def test_synthesize_passes_voice_id_to_convert_api(self, tmp_path):
        # Arrange
        client = _FakeElevenLabsClient(chunks=[b"audio"])
        tts = _make_tts(client)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert "voice_id" in client.text_to_speech.calls[0]

    def test_synthesize_returns_supplied_output_path(self, tmp_path):
        # Arrange
        client = _FakeElevenLabsClient(chunks=[b"audio"])
        tts = _make_tts(client)
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.synthesize("Hello world", str(output_file))
        # Assert
        assert result == output_file

    def test_synthesize_writes_output_file_to_disk(self, tmp_path):
        # Arrange
        client = _FakeElevenLabsClient(chunks=[b"chunk1", b"chunk2", b"chunk3"])
        tts = _make_tts(client)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello", str(output_file))
        # Assert
        assert output_file.exists()

    def test_synthesize_concatenates_audio_chunks_into_file(self, tmp_path):
        # Arrange
        client = _FakeElevenLabsClient(chunks=[b"chunk1", b"chunk2", b"chunk3"])
        tts = _make_tts(client)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello", str(output_file))
        # Assert
        assert output_file.read_bytes() == b"chunk1chunk2chunk3"

    def test_synthesize_uses_voice_from_config_to_resolve_voice_id(self, tmp_path):
        # Arrange
        client = _FakeElevenLabsClient(chunks=[b"audio"])
        tts = _make_tts(client)
        tts.config["voice"] = "adam"
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello", str(output_file))
        # Assert
        assert (
            client.text_to_speech.calls[0]["voice_id"] == ElevenLabsTTS.VOICES["adam"]
        )

    def test_get_voices_with_no_client_returns_list(self):
        # Arrange
        client = _FakeElevenLabsClient(voices=[])
        tts = _make_tts(client)
        # Act
        voices = tts.get_voices()
        # Assert
        assert isinstance(voices, list)

    def test_get_voices_includes_all_preset_entries(self):
        # Arrange
        client = _FakeElevenLabsClient(voices=[])
        tts = _make_tts(client)
        # Act
        voices = tts.get_voices()
        # Assert
        assert len(voices) >= len(ElevenLabsTTS.VOICES)

    def test_get_voices_returns_one_custom_voice_when_remote_lists_one(self):
        # Arrange
        client = _FakeElevenLabsClient(
            voices=[
                _FakeCustomVoice(
                    name="Custom Voice",
                    voice_id="custom-id",
                    labels={"accent": "British"},
                ),
            ]
        )
        tts = _make_tts(client)
        # Act
        voices = tts.get_voices()
        custom_voices = [v for v in voices if v.get("type") == "custom"]
        # Assert
        assert len(custom_voices) == 1

    def test_get_voices_preserves_custom_voice_name_from_remote(self):
        # Arrange
        client = _FakeElevenLabsClient(
            voices=[
                _FakeCustomVoice(
                    name="Custom Voice",
                    voice_id="custom-id",
                    labels={"accent": "British"},
                ),
            ]
        )
        tts = _make_tts(client)
        # Act
        voices = tts.get_voices()
        custom_voices = [v for v in voices if v.get("type") == "custom"]
        # Assert
        assert custom_voices[0]["name"] == "Custom Voice"

    def test_get_voices_handles_api_error_returns_list_type(self):
        # Arrange
        client = _FakeElevenLabsClient(voices_exc=RuntimeError("API Error"))
        tts = _make_tts(client)
        # Act
        voices = tts.get_voices()
        # Assert
        assert isinstance(voices, list)

    def test_get_voices_handles_api_error_falls_back_to_presets_only(self):
        # Arrange
        client = _FakeElevenLabsClient(voices_exc=RuntimeError("API Error"))
        tts = _make_tts(client)
        # Act
        voices = tts.get_voices()
        # Assert
        assert len(voices) == len(ElevenLabsTTS.VOICES)


class TestElevenLabsTTSEdgeCases:
    """Edge case tests for ElevenLabsTTS."""

    def test_minimum_stability_zero_is_preserved(self):
        # Arrange
        # Act
        tts_min = ElevenLabsTTS(stability=0.0)
        # Assert
        assert tts_min.stability == 0.0

    def test_maximum_stability_one_is_preserved(self):
        # Arrange
        # Act
        tts_max = ElevenLabsTTS(stability=1.0)
        # Assert
        assert tts_max.stability == 1.0

    def test_minimum_similarity_boost_zero_is_preserved(self):
        # Arrange
        # Act
        tts_min = ElevenLabsTTS(similarity_boost=0.0)
        # Assert
        assert tts_min.similarity_boost == 0.0

    def test_maximum_similarity_boost_one_is_preserved(self):
        # Arrange
        # Act
        tts_max = ElevenLabsTTS(similarity_boost=1.0)
        # Assert
        assert tts_max.similarity_boost == 1.0

    def test_speed_below_min_is_clamped_to_min(self):
        # Arrange
        # Act
        tts_slow = ElevenLabsTTS(speed=0.5)
        # Assert
        assert tts_slow.speed == ElevenLabsTTS.MIN_SPEED

    def test_speed_above_max_is_clamped_to_max(self):
        # Arrange
        # Act
        tts_fast = ElevenLabsTTS(speed=2.0)
        # Assert
        assert tts_fast.speed == ElevenLabsTTS.MAX_SPEED

    def test_speed_within_range_is_preserved(self):
        # Arrange
        # Act
        tts_mid = ElevenLabsTTS(speed=1.0)
        # Assert
        assert tts_mid.speed == 1.0

    def test_no_api_key_env_resolves_to_none(self, clean_elevenlabs_env):
        # Arrange
        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.api_key is None

    def test_unknown_voice_id_passes_through_get_voice_id(self):
        # Arrange
        tts = ElevenLabsTTS()
        custom_id = "some-custom-voice-id-that-doesnt-exist"
        # Act
        result = tts._get_voice_id(custom_id)
        # Assert
        assert result == custom_id


class TestElevenLabsTTSVoicePresets:
    """Tests for voice preset mappings."""

    def test_every_preset_voice_id_is_non_empty_string(self):
        # Arrange
        ids = list(ElevenLabsTTS.VOICES.values())
        # Act
        all_ok = all(isinstance(v, str) and len(v) > 0 for v in ids)
        # Assert
        assert all_ok is True

    def test_preset_voice_table_has_at_least_eight_entries(self):
        # Arrange
        # Act
        size = len(ElevenLabsTTS.VOICES)
        # Assert
        assert size >= 8


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF
